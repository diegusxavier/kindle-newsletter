import sys
import os

# Correção de PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yaml
from datetime import datetime
from src.scraper import NewsScraper
from src.ai_curator import NewsCurator
from src.pdf_generator import NewsFormatterfix
from src.emailer import EmailSender 
from src.epub_generator import EpubGenerator

# Função para carregar configuração YAML
def load_config():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", "settings.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Erro: Config não encontrada.")
        sys.exit(1)

# Função principal
def main():
    print("🚀 Iniciando o Gerador de Jornal Diário Inteligente...")
    config = load_config()
    
    scraper = NewsScraper(config)
    curator = NewsCurator(config)
    
    candidates = scraper.get_candidates()
    if not candidates: return

    max_news = config.get('preferences', {}).get('max_articles', 1) 
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
    
    # Geração do PDF
    pdf_formater = NewsFormatter()
    pdf_filename = f"Jornal_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    pdf_path = pdf_formater.create_pdf(briefing_text, processed_articles, output_filename=pdf_filename)

    # Geração do EPUB
    epub_gen = EpubGenerator()
    filename = f"Jornal_{datetime.now().strftime('%Y-%m-%d')}.epub" # Extensão .epub
    epub_path = epub_gen.create_epub(briefing_text, processed_articles, output_filename=filename)
    if pdf_path:
        print(f"✅ PDF Gerado: {pdf_path}")
        
        # Pergunta se quer enviar (opcional, para teste) ou envia direto
        # Vamos enviar direto:
        # emailer = EmailSender(config)
        # emailer.send_pdf(epub_path)

if __name__ == "__main__":
    main()