from flask import Flask, render_template, request
import sys
import os

# Adiciona a pasta raiz ao path para conseguirmos importar o 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.loader import carregar_gramatica_da_string
from core.parser_LL1 import calcular_first, calcular_follow, gerar_tabela_ll1

app = Flask(__name__)

# No topo do web/app.py, define os exemplos
EXEMPLOS = {
    "simples": "S -> A B\nA -> a | ε\nB -> b | c",
    "pascal_sub": "Program -> StmtList\nStmtList -> Stmt StmtList_P\nStmtList_P -> Stmt StmtList_P | ε\nStmt -> id : Expr\nExpr -> Term Expr_P\nExpr_P -> + Term Expr_P | ε\nTerm -> id | number",
    "agenda": """Agenda -> DeclXML AAGENDA Lista FAGENDA
DeclXML -> DCA ListaAtrib DCF
ListaAtrib -> Atrib ListaAtrib |
Atrib -> id '=' vatrib
Lista -> Elem Lista |  
Elem -> Entrada | Grupo
Entrada -> AENTRADA ListaAtrib '>' Nome EntradaCont
EntradaCont -> Telefone FENTRADA | Email Telefone FENTRADA
Nome -> ANOME string FNOME
Email -> AEMAIL string FEMAIL
Telefone -> ATELEFONE string FTELEFONE
Grupo -> AGRUPO ListaAtrib '>' GLista FGRUPO
GLista -> GElem GLista | 
GElem -> Entrada | Grupo | Ref 
Ref -> AREF ListaAtrib '/' '>'""",

"arithmetic": """E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E )  | id | number"""
}

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    gramatica_texto = ""
    frase_entrada = ""
    codigo_parser = ""
    sugestao = None
    
    if request.method == 'POST':
        gramatica_texto = request.form.get('gramatica', "")
        frase_entrada = request.form.get('frase', "")
        
        try:
            g = carregar_gramatica_da_string(gramatica_texto)
            f = calcular_first(g)
            fol = calcular_follow(g, f)
            tab, conf = gerar_tabela_ll1(g, f, fol)
            _, conflitos = gerar_tabela_ll1(g,f,fol)
            if conflitos:
                from core.refactor import propor_correcoes
                sugestao = propor_correcoes(g)
            
            from core.generator import gerar_codigo_parser
            codigo_parser = gerar_codigo_parser(g, tab)
            
            resultado = {
                'gramatica': g, 'tabela': tab, 'conflitos': conf, 'arvore': None
            }

            # Se o utilizador escreveu uma frase, tentamos gerar a árvore
            if frase_entrada.strip():
                # Tokenização simples: separa por espaços
                tokens_lista = []
                for t in frase_entrada.split():
                    if t.isdigit():
                        tipo = 'number'
                    else:
                        tipo = t
                    tokens_lista.append({'type': tipo, 'value': tipo})
                
                # Chamamos a função que criámos anteriormente
                from core.parser_LL1 import gerar_arvore_derivacao
                resultado['arvore'] = gerar_arvore_derivacao(tokens_lista, g, tab)

        except Exception as e:
            resultado = {'erro': str(e)}

    return render_template('index.html', 
                           resultado=resultado, 
                           gramatica_texto=gramatica_texto, 
                           frase_entrada=frase_entrada,
                           exemplos=EXEMPLOS,
                           codigo_parser=codigo_parser,
                           sugestao=sugestao)

if __name__ == '__main__':
    app.run(debug=True)