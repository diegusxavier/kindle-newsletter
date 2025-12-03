import sys
import os

# Correção de PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yaml
from datetime import datetime
from src.scraper import NewsScraper
from src.ai_curator import NewsCurator
from src.formatter import NewsFormatter
from src.emailer import EmailSender # <--- NOVO IMPORT

def load_config():
    # (Mantém igual ao anterior)
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", "settings.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Erro: Config não encontrada.")
        sys.exit(1)

def main():
    print("🚀 Iniciando o Gerador de Jornal Diário Inteligente...")
    config = load_config()
    
    # --- ETAPA 1, 2 e 3 (Mantém igual: Scraper, Curator, Formatter) ---
    scraper = NewsScraper(config)
    curator = NewsCurator(config)
    
    candidates = scraper.get_candidates()
    if not candidates: return

    max_news = config.get('preferences', {}).get('max_articles_per_source', 3) 
    selected_articles = curator.filter_candidates(candidates, limit=max_news)
    print(f"🎯 IA selecionou {len(selected_articles)} notícias.")

    processed_articles = []
    summaries = []

    for item in selected_articles:
        print(f"⬇️ Baixando: {item['title']}")
        content_data = scraper.download_article_content(item['url'])
        if content_data:
            full_article = {**item, **content_data}
            summary = curator.summarize_article(full_article)
            full_article['ai_summary'] = summary
            processed_articles.append(full_article)
            summaries.append(summary)

    if not processed_articles: return

    briefing_text = curator.generate_briefing(summaries)
    
    formatter = NewsFormatter()
    filename = f"Jornal_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    pdf_path = formatter.create_pdf(briefing_text, processed_articles, output_filename=filename)
    
    # --- ETAPA 4: ENVIO DE EMAIL (NOVO) ---
    if pdf_path:
        print(f"✅ PDF Gerado: {pdf_path}")
        
        # Pergunta se quer enviar (opcional, para teste) ou envia direto
        # Vamos enviar direto:
        # emailer = EmailSender(config)
        # emailer.send_pdf(pdf_path)

if __name__ == "__main__":
    main()