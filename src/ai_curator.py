import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

class NewsCurator:
    def __init__(self, config):
        self.config = config
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Erro: GEMINI_API_KEY não encontrada.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = config.get('api', {}).get('gemini_model', 'gemini-1.5-flash')
        
        # Tópicos de interesse do usuário
        self.user_topics = config.get('preferences', {}).get('topics', [])

    def filter_candidates(self, candidates_list, limit=5):
        """
        Analisa uma lista grande de manchetes e escolhe as melhores baseadas nos tópicos.
        Retorna uma lista de IDs das notícias escolhidas.
        """
        print("📰 Selecionando as notícias mais relevantes...")
        
        # Prepara a lista para o prompt (simplificada)
        candidates_text = ""
        for item in candidates_list:
            candidates_text += f"ID: {item['id']} | Título: {item['title']} | Fonte: {item['source']}\n"

        topics_str = ", ".join(self.user_topics)

        prompt = f"""
        Você é um editor chefe pessoal. Seu usuário tem interesse nestes tópicos: {topics_str}.
        
        Abaixo está uma lista de manchetes candidatas. 
        Sua tarefa é selecionar até {limit} das notícias mais relevantes e importantes baseadas nos interesses do usuário.
        Se houver notícias repetidas ou muito similares, escolha apenas a melhor fonte.
        
        LISTA DE CANDIDATOS:
        {candidates_text}
        
        FORMATO DE RESPOSTA:
        Retorne APENAS uma lista JSON com os IDs das notícias escolhidas. Nada mais.
        Exemplo: ["id_1", "id_2", "id_5"]
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Limpeza básica para garantir que é um JSON válido
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            selected_ids = json.loads(text_response)
            
            # Filtra a lista original mantendo apenas os escolhidos
            final_selection = [item for item in candidates_list if item['id'] in selected_ids]
            return final_selection

        except Exception as e:
            print(f"❌ [Erro na filtragem]: {e}")
            # Fallback: Se a IA falhar, retorna os primeiros 'limit' itens
            return candidates_list[:limit]

    # ... (Mantenha as funções summarize_article e generate_briefing exatamente como estavam antes) ...
    def summarize_article(self, article_data):
        # (Código anterior da função summarize_article...)
        print(f"🤔 Analisando artigo: {article_data['title']}...")
        prompt = f"""
        Você é um analista de inteligência especialista. Sua tarefa é ler e analisar a notícia abaixo e criar um relatório de resumo para um jornal executivo.
        O título do artigo é "{article_data['title']}", e se estiver em inglês, deve ser traduzido para português onde houver escrito *TÍTULO*.
        DADOS DA NOTÍCIA:
        Título: *TÍTULO* 
        Fonte: {article_data.get('source')}
        Conteúdo: {article_data['content'][:8000]} (Texto truncado se for muito longo)

        FORMATO DE SAÍDA (Markdown):
        - Se {article_data['title']} estiver em inglês, reescreva-o em inglês e em itálico no início do resumo.
        - Escreva um resumo de 2 a 3 parágrafos, mantendo as informações do conteúdo.
        - Liste 3 "Pontos Chave" em bullets.
        - Inclua uma seção "Contexto Adicional" com 2-3 frases que expliquem o motivo da importância do tema ou implicações.
        - O tom deve ser objetivo, profissional e direto.
        - Idioma: Português do Brasil.

        Gere apenas o conteúdo markdown, sem introduções ou conversas. Inclua o link original no final.
        """
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text
        except:
            return f"## {article_data['title']}\nErro no resumo."

    def generate_briefing(self, summaries_list):
        # (Código anterior da função generate_briefing...)
        print("📝 Gerando Briefing...")
        combined_text = "\n---\n".join(summaries_list)
        prompt = f"""
        Atue como Editor Chefe de um jornal de elite. Abaixo estão os resumos das principais notícias do dia.

        Sua tarefa é escrever a CAPA (Briefing Executivo) do jornal.

        NOTÍCIAS DO DIA:
        {combined_text}
        ESTRUTURA DO BRIEFING (Markdown):
        # KARTEIRO
        ## Visão Geral
        Um ou dois parágrafos concisos conectando os temas. Qual é o sentimento geral das notícias hoje?
        ## Resumo dos Temas Principais
        Identifique 3 a 5 temas mais relevantes que aparecem nas notícias, com um breve panorama geral de cada tema macro.
        Para cada tema, escreva um pequeno parágrafo que resuma o parnorama geral do tema nas notícias.
        ## Desenvolvimentos Chave
        Agrupe notícias similares se houver. Separe em temas se necessário em Heading 3 (###). Liste os desenvolvimentos mais importantes em bullets. Entre 1 e 2 bullets por notícia, cada um contendo uma frase.
        ## O que observar
        Uma lista curta de implicações futuras baseada nessas notícias.

        IMPORTANTE:
        - Não repita as notícias individualmente aqui, apenas sintetize os temas.
        - Seja extremamente conciso e denso em informação.
        - Gere apenas o markdown.
        """
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text
        except:
            return "# Briefing\nErro."
        
        # Bloco de teste rápido (para rodar esse arquivo diretamente e ver se funciona)



