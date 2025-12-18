import feedparser
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import uuid
from newspaper import Article
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import User, NewsHistory

class NewsScraper:
    def __init__(self, db: Session):
        """
        O Scraper agora precisa da sessão do banco de dados para verificar duplicatas.
        """
        self.db = db
        self.images_dir = os.path.join("data", "images")
        os.makedirs(self.images_dir, exist_ok=True)

    def get_candidates(self, user: User, limit_per_source=5):
        """
        Varre os RSS do usuário e retorna candidatos que AINDA NÃO estão no histórico.
        """
        candidates = []
        print(f"\n🔎 Iniciando varredura para: {user.name}")

        # Pega apenas fontes ativas do usuário (Magic do SQLAlchemy: user.sources)
        active_sources = [s for s in user.sources if s.is_active]
        
        if not active_sources:
            print("⚠️ Nenhuma fonte ativa encontrada para este usuário.")
            return []

        for source in active_sources:
            print(f"   📡 Conectando a: {source.name}...") 
            
            try:
                # O timeout evita que o script trave se o site estiver fora do ar
                feed = feedparser.parse(source.url)
                
                if not feed.entries:
                    print(f"      ⚠️  Nenhum item no feed.")
                    continue

                count_added = 0
                # Analisa os itens mais recentes
                for entry in feed.entries[:limit_per_source]:
                    link = entry.link.strip()
                    title = entry.title.strip()

                    # Verifica se essa URL já foi processada para ESTE usuário
                    exists = self.db.query(NewsHistory).filter(
                        NewsHistory.user_id == user.id,
                        NewsHistory.url == link
                    ).first()

                    if exists:
                        # Se já existe, ignora silenciosamente (ou printa para debug)
                        # print(f"      ↪️ Já vista: {title[:30]}...")
                        continue
                    
                    # Se não existe, adiciona aos candidatos
                    candidates.append({
                        "id": str(uuid.uuid4()), 
                        "title": title,
                        "url": link,
                        "source": source.name,
                        "published": entry.get('published', '')
                    })
                    count_added += 1
                    print(f"      • [NOVA] {title[:40]}...")
                
                print(f"      ✅ {count_added} notícias novas selecionadas.")

            except Exception as e:
                print(f"❌ [Erro no feed {source.name}]: {e}")
        
        print(f"\n💬 Total: {len(candidates)} candidatos novos encontrados.\n")
        return candidates

    def download_article_content(self, url):
        """
        Mantemos igual: Baixa o conteúdo completo usando Newspaper3k
        """
        try:
            article = Article(url, language='pt')
            article.download()
            article.parse()
            
            # Baixa imagem (Lógica simplificada: sempre baixa se tiver)
            local_image_path = None
            # if article.top_image:
            #     local_image_path = self._download_image(article.top_image)

            return {
                "content": article.text,
                "image_url": article.top_image,
                "local_image_path": local_image_path,
                "authors": article.authors
            }
        except Exception as e:
            print(f"❌ [Erro ao baixar artigo {url}]: {e}")
            return None

    def _download_image(self, image_url):
        if not image_url: return None
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join(self.images_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return filepath
        except:
            return None
        return None

# --- TESTE ISOLADO ---
if __name__ == "__main__":
    from src.database import SessionLocal
    
    db = SessionLocal()
    # Pega o primeiro usuário do banco para teste
    user = db.query(User).first()
    
    if user:
        scraper = NewsScraper(db)
        candidatos = scraper.get_candidates(user)
        print(f"Teste concluído: {len(candidatos)} itens retornados.")
    else:
        print("Nenhum usuário no banco. Rode o seed.py!")
    
    db.close()