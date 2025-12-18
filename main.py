import sys
import os
from datetime import datetime

# Garante que o Python encontre os módulos da pasta src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import SessionLocal
from src.models import User, NewsHistory
from src.scraper import NewsScraper
from src.ai_curator import NewsCurator
from src.pdf_generator import NewsFormatter
from src.epub_generator import EpubGenerator # 1. Importando o gerador de EPUB
from src.emailer import EmailSender 

def main():
    print("🚀 Iniciando Karteiro 2.0 (Database Edition)...")
    
    # 1. Conecta ao Banco
    db = SessionLocal()
    
    try:
        # 2. Busca todos os usuários ativos
        users = db.query(User).filter(User.is_active == True).all()
        print(f"👥 Usuários ativos encontrados: {len(users)}")

        if not users:
            print("⚠️ Nenhum usuário ativo. Rode o 'src/seed.py' se for a primeira vez.")
            return

        # Instancia as ferramentas
        scraper = NewsScraper(db)
        curator = NewsCurator()
        formatter = NewsFormatter()
        epub_gen = EpubGenerator() # 2. Instanciando a classe do EPUB
        emailer = EmailSender()

        # 3. Loop por Usuário
        for user in users:
            print(f"\n==========================================")
            print(f"👤 Processando jornal para: {user.name} ({user.email})")
            print(f"==========================================")

            # --- ETAPA A: Coleta ---
            candidates = scraper.get_candidates(user, limit_per_source=4)
            
            if not candidates:
                print("💤 Nenhuma notícia nova encontrada para este usuário hoje.")
                continue

            # --- ETAPA B: Curadoria (IA) ---
            selected_articles = curator.filter_candidates(candidates, user, limit=2)
            
            if not selected_articles:
                print("🧹 A IA filtrou todas as notícias (nada relevante).")
                continue

            # --- ETAPA C: Download e Resumo ---
            processed_articles = []
            summaries = []

            print(f"📚 Baixando e resumindo {len(selected_articles)} artigos...")
            for item in selected_articles:
                content_data = scraper.download_article_content(item['url'])
                
                if content_data:
                    full_article = {**item, **content_data}
                    
                    # Gera resumo com IA
                    summary = curator.summarize_article(full_article)
                    full_article['ai_summary'] = summary
                    
                    processed_articles.append(full_article)
                    summaries.append(summary)

            if not processed_articles:
                print("❌ Falha ao processar conteúdos.")
                continue

            # --- ETAPA D: Geração dos Arquivos ---
            briefing_text = curator.generate_briefing(summaries)
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # 3. Gera a versão PDF (Salva local, mas não envia)
            pdf_filename = f"Jornal_{user.name.split()[0]}_{date_str}.pdf"
            pdf_path = formatter.create_pdf(
                briefing_text, 
                processed_articles, 
                output_filename=pdf_filename
            )
            print(f"✅ PDF gerado (backup local): {pdf_path}")

            # 4. Gera a versão EPUB (Para envio)
            epub_filename = f"Jornal_{user.name.split()[0]}_{date_str}.epub"
            epub_path = epub_gen.create_epub(
                briefing_text, 
                processed_articles, 
                output_filename=epub_filename
            )

            # --- ETAPA E: Envio (Apenas EPUB) ---
            if epub_path:
                print(f"📤 Enviando EPUB para Kindle: {user.kindle_email}...")
                
                # O método chama send_pdf, mas funciona para qualquer arquivo
                sent = emailer.send_pdf(epub_path, target_email=user.kindle_email)
                
                if sent:
                    # --- ETAPA F: Atualizar Histórico ---
                    print("💾 Salvando histórico para evitar repetições futuras...")
                    for art in processed_articles:
                        history_item = NewsHistory(
                            user_id=user.id,
                            title=art['title'],
                            url=art['url'],
                            published_at=art.get('published', '')
                        )
                        db.add(history_item)
                    
                    db.commit()
                    print("✅ Ciclo concluído para este usuário!")
                else:
                    print("❌ Erro no envio. Histórico NÃO atualizado.")

    except Exception as e:
        print(f"❌ Erro fatal na execução: {e}")
    finally:
        db.close()
        print("\n🏁 Execução finalizada.")

if __name__ == "__main__":
    main()