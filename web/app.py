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
    "Lista": """Lista -> '[' Cont

Cont -> ']' 
    | Elems ']'

Elems -> Elem Resto

Resto -> vazio 
        | ',' Elem Resto

Elem-> int 
    | str

int -> [0-9]+""",
    
    "Pascal_sub": """Program -> StmtList

StmtList -> Stmt StmtList_P

StmtList_P -> Stmt StmtList_P 
            | ε

Stmt -> id ':' Expr

Expr -> Term Expr_P

Expr_P -> '+' Term Expr_P
        | ε

Term -> id 
        | number

id -> [a-zA-Z_][a-zA-Z0-9_]*
number  -> [0-9]+
""",
    
    "Agenda": """Agenda      -> DeclXML AAGENDA Lista FAGENDA

DeclXML     -> DCA ListaAtrib DCF

ListaAtrib  -> Atrib ListaAtrib 
              | ε

Atrib       -> id '=' vatrib

Lista       -> Elem Lista 
              | ε

Elem        -> Entrada 
              | Grupo

Entrada     -> AENTRADA ListaAtrib '>' Nome EntradaCont

EntradaCont -> Telefone FENTRADA 
              | Email Telefone FENTRADA

Nome        -> ANOME string FNOME

Email       -> AEMAIL string FEMAIL

Telefone    -> ATELEFONE string FTELEFONE

Grupo       -> AGRUPO ListaAtrib '>' GLista FGRUPO

GLista      -> GElem GLista 
              | ε

GElem       -> Entrada 
              | Grupo 
              | Ref

Ref         -> AREF ListaAtrib '/' '>'

DCA         -> '<?xml'
DCF         -> '?>'
AAGENDA     -> '<agenda>'
FAGENDA     -> '</agenda>'
AENTRADA    -> '<entrada'
FENTRADA    -> '</entrada>'
AGRUPO      -> '<grupo'
FGRUPO      -> '</grupo>'
AREF        -> '<ref'
ANOME       -> '<nome>'
FNOME       -> '</nome>'
AEMAIL      -> '<email>'
FEMAIL      -> '</email>'
ATELEFONE   -> '<telefone>'
FTELEFONE   -> '</telefone>'

id          -> [a-zA-Z_][a-zA-Z0-9_]*
vatrib      -> '"' [^"<>]* '"'
string      -> [^<>]+
number      -> [0-9]+ 
""",

    "Arithmetic": """E -> T E'

E' -> '+' T E' 
    | ε

T -> F T'

T' -> '*' F T' 
    | ε

F -> '(' E ')'  
    | id 
    | number

id -> [a-zA-Z_][a-zA-Z0-9_]*

number -> [0-9]+""",

    "Filesystem": """Z -> Dir

Dir -> '(' texto Conteudo ')' 
    | Ficheiro

Conteudo -> Conteudo Dir 
            | ε

Ficheiro -> '[' texto texto ']'

texto -> '"' [^"]+ '"'
""",
    "SQL": """SQuery         -> Query number ListaIds 'VALUES' ListaLinhas

Query          -> 'SELECT' Colunas 'FROM' id

Colunas        -> '*' 
                | ListaColunas

ListaColunas   -> id ListaColunas_P
ListaColunas_P -> ',' id ListaColunas_P 
                | ε

ListaIds       -> id ListaIds_P
ListaIds_P     -> id ListaIds_P 
                | ε

ListaLinhas    -> ListaVal ListaLinhas_P
ListaLinhas_P  -> 'SEP' ListaVal ListaLinhas_P 
                | ε

ListaVal       -> Coluna ListaVal_P
ListaVal_P     -> Coluna ListaVal_P 
                | ε

Coluna         -> number 
                | id

id             -> [a-zA-Z_][a-zA-Z0-9_]*
number         -> [0-9]+
""",

    "SQL Conflituosa":"""SQuery -> Query number ListaIds ListaLinhas

Query -> 'SELECT' Colunas 'FROM' id

Colunas -> '*' 
         | ListaColunas

ListaColunas -> ListaColunas ',' id
              | id

ListaIds -> ListaIds id
          | id

ListaLinhas -> ListaLinhas 'SEP' ListaVal
             | ListaVal

ListaVal -> ListaVal Coluna
          | Coluna

Coluna -> number 
        | id 
        
id -> [a-zA-Z_][a-zA-Z0-9_]*
number -> [0-9]+""",

        "SExp": """Sexp   --> Exp '.'
Exp    --> number
         | '(' Funcao ')'
Funcao --> '+' Lista
         | '*' Lista
Lista  --> Lista Exp
         | ε
number -> [0-9]+
        """,

    "S9 Bottom-Up":"""S      -> Exp '.'

Exp    -> number 
        | '(' Funcao ')'

Funcao -> '+' Lista 
        | '*' Lista

Lista  -> Exp Lista 
        | ε
number -> [0-9]+""",

    "JSON": """JSON          -> Value

Value         -> Object
               | Array
               | string
               | number
               | 'true'
               | 'false'
               | 'null'

Object        -> '{' Members '}'
Members       -> Pair Members_Tail
               | ε
Pair          -> string ':' Value
Members_Tail  -> ',' Pair Members_Tail
               | ε

Array         -> '[' Elements ']'
Elements      -> Value Elements_Tail
               | ε
Elements_Tail -> ',' Value Elements_Tail
               | ε """
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
                'gramatica': g, 'tabela': tab, 'conflitos': conf, 'arvore': None,
                'first': f, 'follow': fol
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