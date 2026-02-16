from lark import Lark
from analyser import StaticAnalyser
from scope import ScopeAnalyser
from cfg_maker import CFGBuilder
import datetime

# Definição de cores para o Terminal
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# --- FUNÇÃO QUE GERA O HTML COM TOOLTIPS ---
def generate_html(all_issues, cfg_filename, source_code):
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Separar o código em linhas para acesso rápido
    code_lines = source_code.split('\n')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório IPL</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f4f9; padding: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td, th {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
            
            /* BADGES */
            .badge {{ padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; font-size: 0.8em; }}
            .CRITICAL {{ background: #e74c3c; }}
            .WARNING {{ background: #f39c12; }}
            .STYLE {{ background: #3498db; }}
            .SCOPE {{ background: #9b59b6; }}

            /* TOOLTIP MÁGICO (CSS Puro) */
            .tooltip-container {{ position: relative; cursor: help; border-bottom: 1px dotted #555; }}
            
            .tooltip-text {{
                visibility: hidden;
                background-color: #333;
                color: #fff;
                text-align: left;
                border-radius: 6px;
                padding: 10px;
                position: absolute;
                z-index: 1;
                bottom: 125%; /* Aparece em cima */
                left: 50%;
                margin-left: -100px; /* Ajuste central */
                width: 350px;
                opacity: 0;
                transition: opacity 0.3s;
                font-family: monospace;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            
            .tooltip-text strong {{ color: #ffeb3b; display: block; margin-bottom: 5px; border-bottom: 1px solid #555; }}
            
            /* Seta do tooltip */
            .tooltip-text::after {{
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #333 transparent transparent transparent;
            }}

            .tooltip-container:hover .tooltip-text {{ visibility: visible; opacity: 1; }}
            .code-snippet {{ color: #aaffaa; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📊 Relatório de Análise IPL</h1>
            <p>Gerado em: {timestamp}</p>
        </div>

        <div class="card">
            <h2>Problemas Detetados</h2>
            <table>
                <thead><tr><th>Severidade</th><th>Mensagem (Passe o rato para ver código)</th><th>Linha</th></tr></thead>
                <tbody>
    """

    if not all_issues:
        html += "<tr><td colspan='3' style='color:green; font-weight:bold'>✅ Código Limpo!</td></tr>"
    
    for issue in all_issues:
        sev = issue['severity']
        line_num = issue['line']
        msg = issue['message']
        
        # Obter a linha de código exata (cuidado com índices fora de limite)
        code_snippet = "Linha não encontrada"
        if isinstance(line_num, int) and 0 < line_num <= len(code_lines):
            code_snippet = code_lines[line_num - 1].strip()

        html += f"""
        <tr>
            <td><span class="badge {sev}">{sev}</span></td>
            <td>
                <div class="tooltip-container">
                    {msg}
                    <div class="tooltip-text">
                        <strong>Linha {line_num}:</strong>
                        <span class="code-snippet">{code_snippet}</span>
                    </div>
                </div>
            </td>
            <td>{line_num}</td>
        </tr>
        """

    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Control Flow Graph</h2>
            <div style="text-align:center"><img src="{cfg_filename}" style="max-width:100%"></div>
        </div>
    </body></html>
    """
    
    with open("relatorio.html", "w", encoding="utf-8") as f: f.write(html)
    print(f"{Colors.BOLD}📄 Relatório HTML gerado com sucesso!{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}=== IPL ANALYSER PRO ==={Colors.RESET}")
    
    # 1. Carregar Ficheiros
    try:
        grammar = open("grammar.lark", encoding="utf-8").read()
        code = open("test_secV3.ipl", encoding="utf-8").read()
    except:
        print("Erro: Ficheiros não encontrados."); return

    # 2. Parser
    parser = Lark(grammar, start='start', parser='lalr', propagate_positions=True)
    try:
        tree = parser.parse(code)
    except Exception as e:
        print(f"Erro Sintaxe: {e}"); return

    all_issues = []

    # 3. Scope
    scope = ScopeAnalyser()
    scope.visit(tree)
    all_issues.extend(scope.errors)

    # 4. Static Analysis
    linter = StaticAnalyser()
    linter.visit(tree)
    all_issues.extend(linter.issues)

    # 5. Print Terminal (Colorido)
    print("\n>>> Resumo no Terminal:")
    for i in all_issues:
        color = Colors.BLUE
        if i['severity'] == 'CRITICAL': color = Colors.RED
        elif i['severity'] == 'WARNING': color = Colors.YELLOW
        elif i['severity'] == 'SCOPE': color = Colors.PURPLE
        
        print(f"{color}[{i['severity']}] Linha {i['line']}: {i['message']}{Colors.RESET}")

    # 6. CFG
    try:
        cfg = CFGBuilder()
        cfg.visit(tree)
        cfg.draw("cfg_output.png")
    except: pass

    # 7. Gerar HTML Rico
    generate_html(all_issues, "cfg_output.png", code)

if __name__ == "__main__":
    main()