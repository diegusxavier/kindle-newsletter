import os
import re
import uuid
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

class Bookmark(Flowable):
    """
    Elemento invisível que adiciona um marcador no índice (outline) do PDF.
    """
    def __init__(self, title, level=0):
        Flowable.__init__(self)
        self.title = title
        self.level = level
        self.key = str(uuid.uuid4())

    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, level=self.level)

class NewsFormatter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Estilos personalizados
        self.styles.add(ParagraphStyle(name='BriefingTitle', parent=self.styles['Title'], fontSize=24, spaceAfter=20))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, textColor=colors.darkblue))
        self.styles.add(ParagraphStyle(name='SubHeader', parent=self.styles['Heading3'], fontSize=14, spaceBefore=10, spaceAfter=5))
        self.styles.add(ParagraphStyle(name='ArticleTitle', parent=self.styles['Heading1'], fontSize=18, spaceBefore=20, spaceAfter=10, textColor=colors.darkred))
        self.styles.add(ParagraphStyle(name='Metadata', parent=self.styles['Italic'], fontSize=9, textColor=colors.gray, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='BodyTextCustom', parent=self.styles['BodyText'], fontSize=11, leading=15, spaceAfter=8))
        # Novo estilo para a lista de links
        self.styles.add(ParagraphStyle(name='LinkItem', parent=self.styles['BodyText'], fontSize=10, leading=12, spaceAfter=4))

    def _parse_markdown_to_flowables(self, text):
        flowables = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            if line.startswith('# '): flowables.append(Paragraph(line[2:], self.styles['BriefingTitle']))
            elif line.startswith('## '): flowables.append(Paragraph(line[3:], self.styles['SectionHeader']))
            elif line.startswith('### '): flowables.append(Paragraph(line[4:], self.styles['SubHeader']))
            elif line.startswith('* ') or line.startswith('- '): flowables.append(Paragraph(f"• {line[2:]}", self.styles['BodyTextCustom']))
            else: flowables.append(Paragraph(line, self.styles['BodyTextCustom']))
        return flowables

    def create_pdf(self, briefing_text, articles_list, candidates_list=None, output_filename="daily_briefing.pdf"):
        """
        Gera o arquivo PDF final. Agora aceita candidates_list.
        """
        output_path = os.path.join("data", "output", output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []

        # --- 1. Capa / Briefing ---
        story.append(Bookmark("Briefing Executivo", level=0))
        date_str = datetime.now().strftime("%d/%m/%Y")
        story.append(Paragraph(f"Edição de: {date_str}", self.styles['Metadata']))
        story.append(Spacer(1, 10))
        story.extend(self._parse_markdown_to_flowables(briefing_text))
        story.append(PageBreak())

        # --- 2. Artigos Detalhados ---
        story.append(Bookmark("Notícias Detalhadas", level=0))
        story.append(Paragraph("Notícias Detalhadas", self.styles['BriefingTitle']))
        story.append(Spacer(1, 20))

        for article in articles_list:
            clean_title = escape(article['title'])
            story.append(Bookmark(clean_title, level=1))
            
            if article.get('url'):
                title_paragraph = f'<a href="{article["url"]}">{clean_title}</a>'
            else:
                title_paragraph = clean_title
            
            story.append(Paragraph(title_paragraph, self.styles['ArticleTitle']))
            source_info = f"Fonte: {article.get('source', 'Desconhecida')} | {article.get('published_at', '')}"
            story.append(Paragraph(source_info, self.styles['Metadata']))
            
            if article.get('local_image_path') and os.path.exists(article['local_image_path']):
                try:
                    img = Image(article['local_image_path'])
                    aspect = img.imageHeight / float(img.imageWidth)
                    img.drawWidth = 400
                    img.drawHeight = 400 * aspect
                    story.append(img)
                    story.append(Spacer(1, 10))
                except: pass

            if 'ai_summary' in article:
                story.extend(self._parse_markdown_to_flowables(article['ai_summary']))
            
            story.append(Spacer(1, 20))
            story.append(Paragraph("_" * 50, self.styles['BodyText']))
            story.append(Spacer(1, 20))

        # --- 3. Lista Completa de Candidatos (NOVO) ---
        if candidates_list:
            story.append(PageBreak()) # Nova página
            story.append(Bookmark("Outras Manchetes", level=0))
            story.append(Paragraph("Todas as Manchetes Rastreadas", self.styles['BriefingTitle']))
            story.append(Paragraph("Abaixo, a lista completa de notícias encontradas nos feeds hoje.", self.styles['BodyTextCustom']))
            story.append(Spacer(1, 15))

            for item in candidates_list:
                clean_title = escape(item['title'])
                url = item.get('url', '')
                source = item.get('source', '?')
                
                # Formato: [Fonte] Título (Link)
                # O ReportLab permite links via tag <a href="...">
                line_html = f'<b>[{source}]</b> <a href="{url}" color="blue">{clean_title}</a>'
                
                story.append(Paragraph(line_html, self.styles['LinkItem']))

        try:
            doc.build(story)
            print(f"📇 PDF gerado com sucesso em: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return None