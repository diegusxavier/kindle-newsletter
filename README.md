📰 Kindle Newsletter - Jornal Diário com IA

Este projeto é um agente autônomo de notícias que cria um jornal personalizado diário. Ele coleta notícias de feeds RSS, utiliza Inteligência Artificial (Google Gemini) para filtrar o que é relevante para você, resume os artigos, gera um arquivo PDF formatado e envia automaticamente para o seu Kindle com conversão para leitura otimizada.

✨ Funcionalidades

Coleta Automatizada: Lê múltiplos feeds RSS de sites de notícias.

Curadoria via IA: Utiliza o Google Gemini para analisar dezenas de manchetes e selecionar apenas as mais relevantes baseadas nos seus tópicos de interesse.

Resumo Inteligente: Gera resumos analíticos ("Deep Dive") e uma capa ("Briefing Executivo") conectando os fatos.

Formatação PDF: Cria um documento visualmente limpo e organizado usando ReportLab.

Envio para Kindle: Envia o PDF via e-mail com o assunto "Convert", garantindo que a Amazon transforme o arquivo para o formato nativo do Kindle.

🛠️ Pré-requisitos

Python 3.8+ instalado.

Uma conta no Google AI Studio (para obter a API Key do Gemini).

Uma conta Gmail (para envio via SMTP) com "Verificação em duas etapas" ativada e uma "Senha de App" gerada.

Um dispositivo ou app Kindle configurado.

🚀 Instalação

Clone o repositório:

```bash
   git clone [https://github.com/diegusxavier/kindle-newsletter.git](https://github.com/diegusxavier/kindle-newsletter.git)
   cd kindle-newsletter
```

Crie e ative um ambiente virtual:

```bash
    python -m venv venv
    # Linux/Mac:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate
```

Instale as dependências:
```python
    pip install -r requirements.txt
```

⚙️ Configuração

1. Variáveis de Ambiente (.env)

Renomeie o arquivo .env.example para .env e preencha com suas credenciais:

# Chave da API do Google Gemini ([https://aistudio.google.com/](https://aistudio.google.com/))
GEMINI_API_KEY=sua_chave_aqui

# Configurações de E-mail (Gmail)
# Gere uma senha de app em: Conta Google > Segurança > Verificação em 2 etapas > Senhas de App
EMAIL_PASSWORD=sua_senha_de_app_16_digitos
SENDER_EMAIL=seu_email_pessoal@gmail.com
KINDLE_EMAIL=seu_usuario@kindle.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587


2. Preferências e Fontes (config/settings.yaml)

Edite o arquivo config/settings.yaml para definir seus interesses e fontes de notícias:

preferences:
  topics:
    - "Inteligência Artificial"
    - "Mercado Financeiro"
  include_images: false # 'true' pode deixar o envio mais lento
  max_articles_per_source: 3

sources:
  - name: "El País Brasil"
    url: "[https://elpais.com/tag/rss/brasil/](https://elpais.com/tag/rss/brasil/)"


3. Autorização na Amazon

Para receber o arquivo, acesse Gerencie seu Conteúdo e Dispositivos > Preferências > Configurações de documentos pessoais na Amazon e adicione o seu SENDER_EMAIL à lista de e-mails aprovados.

▶️ Como Usar

Execute o arquivo principal:

python main.py


O script irá:

Coletar candidatos via RSS.

Usar a IA para filtrar as melhores notícias.

Baixar o conteúdo completo e gerar resumos.

Criar um PDF em data/output/.

Enviar para o seu Kindle via e-mail.

📂 Estrutura do Projeto

kindle-newsletter/
├── config/
│   └── settings.yaml       # Configuração de fontes e tópicos
├── src/
│   ├── scraper.py          # Coletor de RSS e download de artigos
│   ├── ai_curator.py       # Lógica do Gemini (Filtro e Resumo)
│   ├── formatter.py        # Gerador de PDF
│   └── emailer.py          # Envio SMTP
├── data/                   # Arquivos gerados (PDFs e imagens)
├── .env                    # Credenciais (GitIgnored)
├── main.py                 # Arquivo principal
└── requirements.txt        # Dependências


🛡️ Segurança

O arquivo .env está listado no .gitignore para evitar o vazamento de credenciais. Nunca compartilhe suas chaves de API ou senhas de e-mail publicamente.