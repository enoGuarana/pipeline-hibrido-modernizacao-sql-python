import os
import re
import subprocess
from pathlib import Path


def markdown_to_html(md_text: str) -> str:
    # Process text into blocks and inline elements
    lines = md_text.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        
        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr />")
            continue
            
        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if header_match:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            level = len(header_match.group(1))
            content = header_match.group(2)
            content = process_inlines(content)
            html_lines.append(f"<h{level}>{content}</h{level}>")
            continue
            
        # Unordered list items
        list_match = re.match(r'^[\*\-]\s+(.*)$', stripped)
        if list_match:
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = list_match.group(1)
            content = process_inlines(content)
            html_lines.append(f"<li>{content}</li>")
            continue
            
        # If in list and empty line or normal text
        if in_list and (not stripped or not re.match(r'^[\*\-]\s+', stripped)):
            html_lines.append("</ul>")
            in_list = False
            
        if not stripped:
            continue
            
        # Paragraph
        content = process_inlines(stripped)
        html_lines.append(f"<p>{content}</p>")
        
    if in_list:
        html_lines.append("</ul>")
        
    return "\n".join(html_lines)

def process_inlines(text: str) -> str:
    # Bold italic
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    return text

def build_styled_html(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório Técnico: Pipeline Híbrido de Modernização SQL para Python</title>
<style>
    @page {{
        size: A4;
        margin: 18mm 16mm 20mm 16mm;
        @bottom-right {{
            content: "Página " counter(page);
            font-size: 8pt;
            color: #64748b;
        }}
    }}
    
    * {{
        box-sizing: border-box;
    }}
    
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #1e293b;
        background-color: #ffffff;
        line-height: 1.55;
        font-size: 10pt;
        margin: 0;
        padding: 0;
    }}
    
    .report-header {{
        border-bottom: 2px solid #0f2942;
        padding-bottom: 12px;
        margin-bottom: 18px;
    }}
    
    .project-badge {{
        display: inline-block;
        background-color: #0f2942;
        color: #ffffff;
        font-size: 8pt;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 4px;
        margin-bottom: 8px;
    }}
    
    .report-meta {{
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        font-size: 8.5pt;
        color: #475569;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 14px;
    }}
    
    h1 {{
        color: #0f2942;
        font-size: 16pt;
        margin: 0 0 6px 0;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}
    
    h2 {{
        color: #1e3a8a;
        font-size: 13pt;
        margin: 0 0 8px 0;
        font-weight: 700;
    }}
    
    h3 {{
        color: #0f2942;
        font-size: 11pt;
        margin: 16px 0 6px 0;
        font-weight: 700;
        border-left: 3.5px solid #2563eb;
        padding-left: 8px;
        page-break-after: avoid;
        break-after: avoid;
    }}
    
    p {{
        margin: 0 0 8px 0;
        text-align: justify;
    }}
    
    strong {{
        color: #0f172a;
    }}
    
    ul {{
        margin: 4px 0 10px 0;
        padding-left: 20px;
    }}
    
    li {{
        margin-bottom: 6px;
        text-align: justify;
    }}
    
    code {{
        font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
        font-size: 8.5pt;
        background-color: #f1f5f9;
        color: #094c9e;
        padding: 1.5px 4px;
        border-radius: 3px;
        border: 1px solid #e2e8f0;
    }}
    
    hr {{
        border: 0;
        height: 1px;
        background-color: #cbd5e1;
        margin: 14px 0;
    }}
    
    .section-card {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    
    .footer-note {{
        margin-top: 20px;
        font-size: 8pt;
        color: #94a3b8;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 8px;
    }}
</style>
</head>
<body>

<div class="report-header">
    <div class="project-badge">Engenharia de Software &amp; Modernização</div>
    <h1>RELATÓRIO DO PROJETO</h1>
    <h2>Relatório Técnico: Pipeline Híbrido de Modernização SQL para Python</h2>
    <div class="report-meta">
        <div><strong>Ambiente:</strong> Python 3.14 · PostgreSQL 16 · LangGraph</div>
        <div><strong>Orquestração:</strong> Multi-LLM (Gemini / OpenAI / OpenRouter)</div>
        <div><strong>Data de Emissão:</strong> Outubro de 2026</div>
    </div>
</div>

<div class="report-body">
{body_html}
</div>

</body>
</html>
"""

def main():
    root_dir = Path(__file__).resolve().parent.parent
    md_path = root_dir / "docs" / "relatorio-tecnico.md"
    html_path = root_dir / "docs" / "relatorio-tecnico.html"
    pdf_root_path = root_dir / "RELATORIO_TECNICO_PROJETO.pdf"

    print(f"Lendo markdown em: {md_path}")
    raw_md = md_path.read_text(encoding="utf-8")
    
    # Remove redundant title headers from markdown body since they are in template header
    lines = raw_md.splitlines()
    filtered_lines = []
    for l in lines:
        if l.strip().startswith("# RELATORIO DO PROJETO") or l.strip().startswith("## Relatório Técnico:"):
            continue
        filtered_lines.append(l)
    body_md = "\n".join(filtered_lines)

    body_html = markdown_to_html(body_md)
    full_html = build_styled_html(body_html)
    
    html_path.write_text(full_html, encoding="utf-8")
    print(f"HTML gerado em: {html_path}")

    # Generate PDF using Microsoft Edge
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if not os.path.exists(edge_path):
        raise FileNotFoundError("Nenhum executável de navegador compatível (Edge ou Chrome) foi encontrado.")

    file_uri = html_path.as_uri()
    print("Iniciando compilação de PDF via Edge/Chrome headless...")
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_root_path}",
        file_uri
    ]
    subprocess.run(cmd, check=True)

    if pdf_root_path.exists():
        size_kb = pdf_root_path.stat().st_size / 1024
        print("PDF gerado com sucesso!")
        print(f"  - Raiz: {pdf_root_path} ({size_kb:.1f} KB)")
        if html_path.exists():
            html_path.unlink()
    else:
        raise RuntimeError("Falha na geração do PDF: arquivo não foi criado.")

if __name__ == "__main__":
    main()
