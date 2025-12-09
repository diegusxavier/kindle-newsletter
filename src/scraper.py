import feedparser
import os
import requests
import uuid
from newspaper import Article
from datetime import datetime

class NewsScraper:
    def __init__(self, config):
        self.sources = config.get('sources', [])
        self.preferences = config.get('preferences', {})
        self.include_images = self.preferences.get('include_images', False)
        
        # --- LIMITE DE CANDIDATOS (AGORA DINÂMICO) ---
        # Tenta ler do YAML, se não existir, usa 15 como padrão
        self.candidates_limit = self.preferences.get('rss_scan_limit', 15)
        
        self.images_dir = os.path.join("data", "images")
        os.makedirs(self.images_dir, exist_ok=True)

    def get_candidates(self):
        """
        Passo 1: Varre os RSS e retorna uma lista leve (apenas Título e Link)
        para a IA decidir o que vale a pena.
        """
        candidates = []
        print("\n🔎 Iniciando varredura de RSS...")

        for source in self.sources:
            print(f"   📡 Conectando a: {source['name']}...") 
            
            try:
                feed = feedparser.parse(source['url'])
                
                if not feed.entries:
                    print(f"      ⚠️  Nenhum item encontrado neste feed. Verifique a URL.")
                    continue

                # Pega os X primeiros itens do feed para análise
                count_source = 0
                for entry in feed.entries[:self.candidates_limit]:
                    # Limpeza básica do título
                    title = entry.title.strip()
                    
                    # --- NOVO PRINT: MOSTRA CADA MANCHETE ENCONTRADA ---
                    print(f"      • [{source['name']}] {title}")
                    
                    candidates.append({
                        "id": str(uuid.uuid4()), 
                        "title": title,
                        "url": entry.link,
                        "source": source['name'],
                        "published": entry.get('published', '')
                    })
                    count_source += 1
                
                print(f"      ✅ {count_source} manchetes coletadas.")

            except Exception as e:
                print(f"❌ [Erro crítico no feed {source['name']}]: {e}")
        
        print(f"\n💬 Resumo: {len(candidates)} notícias candidatas enviadas para análise da IA.\n")
        return candidates

    def download_article_content(self, url):
        """
        Passo 2: Baixa o conteúdo pesado APENAS das notícias aprovadas pela IA.
        """
        try:
            article = Article(url, language='pt')
            article.download()
            article.parse()
            
            # Baixa imagem
            local_image_path = None
            if self.include_images and article.top_image:
                local_image_path = self._download_image(article.top_image)

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

# --- BLOCO DE TESTE INDIVIDUAL ---
if __name__ == "__main__":
    print("🛠️  Modo de Teste do Scraper Iniciado...")
    
    # Configuração Fake para testar sem ler o arquivo YAML
    mock_config = {
        "sources": [
            {"name": "Teste - CNN Tecnologia", "url": "https://www.cnnbrasil.com.br/tecnologia/feed/"},
            {"name": "Teste - G1 Tecnologia", "url": "https://g1.globo.com/rss/g1/tecnologia/"}
        ],
        "preferences": {
            "include_images": False,
            "max_articles_per_source": 5
        }
    }
    
    scraper = NewsScraper(mock_config)
    
    # Testa a coleta de candidatos
    print("\n--- Testando get_candidates() ---")
    candidatos = scraper.get_candidates()
    
    # Testa o download do primeiro artigo encontrado (se houver)
    if candidatos:
        print("\n--- Testando download_article_content() com o primeiro item ---")
        primeiro = candidatos[0]
        print(f"Baixando: {primeiro['title']} ({primeiro['url']})")
        conteudo = scraper.download_article_content(primeiro['url'])
        
        if conteudo:
            print("\n✅ Conteúdo baixado com sucesso!")
            print(f"Tamanho do texto: {len(conteudo['content'])} caracteres")
            print(f"Imagem principal: {conteudo['image_url']}")
        else:
            print("❌ Falha ao baixar conteúdo.")
    else:
        print("⚠️ Nenhuma notícia encontrada para testar o download.")