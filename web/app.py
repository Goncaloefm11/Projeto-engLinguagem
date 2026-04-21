#app.py
from flask import Flask, render_template, request
import sys
import os
import re

# Adiciona a pasta raiz ao path para conseguirmos importar o 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.loader import carregar_gramatica_da_string
from core.parser_LL1 import calcular_first, calcular_follow, gerar_tabela_ll1, gerar_arvore_derivacao_com_erro, arvore_para_texto, arvore_para_mermaid


app = Flask(__name__)

# No topo do web/app.py, define os exemplos
EXEMPLOS = {
    "Lista": """Lista -> '[' Cont

Cont -> ']' 
    | Elems ']'

Elems -> Elem Resto

Resto -> ε
        | ',' Elem Resto

Elem-> int 
    | string

int -> [0-9]+
string -> [^<>]+""",
    
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

Ref->AREF ListaAtrib '/' '>'

DCA->'<?xml'
DCF->'?>'
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

id ->[a-zA-Z_][a-zA-Z0-9_]*
vatrib -> '"[^"<>]*"'
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

Dir -> '(' string Conteudo ')' 
    | Ficheiro

Conteudo -> Conteudo Dir 
            | ε

Ficheiro -> '[' string string ']'

string -> [^<>]+

""",
    "SQL": """SQuery->Query number ListaIds 'VALUES' ListaLinhas

Query ->'SELECT' Colunas 'FROM' id

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

Coluna->number 
                | id

id    ->[a-zA-Z_][a-zA-Z0-9_]*
number->[0-9]+
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

        "SExp": """Sexp   -> Exp '.'
Exp    -> INT
         | '(' Funcao ')'
Funcao -> '+' Lista
         | '*' Lista
Lista  -> Lista Exp
         | ε
INT -> [0-9]+
        """,

    "S9 Bottom-Up":"""S      -> Exp '.'

Exp    -> number 
        | '(' Funcao ')'

Funcao -> '+' Lista 
        | '*' Lista

Lista  -> Exp Lista 
        | ε
number -> [0-9]+""",

    "JSON": r"""JSON ->Value

Value->Object
        | Array
        | string
        | number
        | 'true'
        | 'false'
        | 'null'

Object        -> '{' Members '}'
Members       -> Pair Members_Tail
               | ε
               
Pair ->string ':' Value

Members_Tail  -> ',' Pair Members_Tail
               | ε

Array->'[' Elements ']'
Elements      -> Value Elements_Tail
               | ε
               
Elements_Tail -> ',' Value Elements_Tail
               | ε 

string        -> '"[^"]*"'
number        -> \-?[0-9]+(\.[0-9]+)?"""
}

frases_exemplo = {
    "Lista": "[ 1 , 2 , 3 ]",
    "Pascal_sub": "x : a + 10",
        "Agenda": "<?xml version = \"1.0\" ?> <agenda> <entrada ident = \"e1\" > <nome> Joana </nome> <email> joana@mail.com </email> <telefone> 912345678 </telefone> </entrada> <grupo ident = \"g1\" > <ref id = \"e1\" / > <entrada > <nome> Pedro </nome> <telefone> 220000000 </telefone> </entrada> </grupo> </agenda>",
   "Arithmetic": "5 + id_var * ( 10 + 20 )",
  "Filesystem": """( "root" ( "docs" [ "cv.pdf" "~/home/cv.pdf" ] ) ( "images" [ "foto.png" "./foto.png" ] ) )""",
  "SQL": "SELECT * FROM users 5 user_id VALUES 100 SEP 200 SEP 300",
  "SExp": "( + 1 2 ( * 3 4 ) ) .",
  "S9 Bottom-Up": "( * 5 10 20 ( + 1 1 ) ) .",
  "JSON": "{ \"id\" : 101 , \"activo\" : true , \"valores\" : [ 10.5 , 20.0 , -5 ] , \"info\" : { \"tags\" : [ \"ia\" , \"gramatica\" ] , \"nota\" : null } }"
}


def tokenizar_frase(frase, gramatica):
    tokens_lista = []
    terminais = gramatica['terminais']
    producoes = gramatica['producoes']

    # Permite entradas compactas (ex.: <nome>Joana</nome>, ident="e1">)
    # separando terminais literais definidos na gramática.
    literais = []
    for t in terminais:
        if len(t) >= 2 and t[0] == "'" and t[-1] == "'":
            lit = t[1:-1]
            if lit and lit != 'ε':
                literais.append(lit)

    # Separa por literais com regex (ordem por tamanho) para nao destruir
    # tokens maiores (ex.: <agenda>) ao separar tokens curtos (ex.: >).
    partes = []
    if literais:
        pattern = "(" + "|".join(re.escape(l) for l in sorted(set(literais), key=len, reverse=True)) + ")"
        for pedaco in re.split(pattern, frase):
            if not pedaco:
                continue
            if pedaco in literais:
                partes.append(pedaco)
            else:
                partes.extend(pedaco.split())
    else:
        partes = frase.split()

    for t in partes:
        candidatos = []

        # 1. Correspondencia exata: simbolo literal definido na gramatica.
        if t in terminais:
            candidatos.append(t)
        literal_entre_aspas = f"'{t}'"
        if literal_entre_aspas in terminais and literal_entre_aspas not in candidatos:
            candidatos.append(literal_entre_aspas)

        # 2. Procura por padrao regex nas regras lexicais.
        for _, prods in producoes.items():
            for prod in prods:
                if len(prod) == 1:
                    padrao = prod[0].strip("'")
                    try:
                        if re.fullmatch(padrao, t) and prod[0] not in candidatos:
                            candidatos.append(prod[0])
                    except re.error:
                        pass

        # Se ainda nao encontrou tipo, eh erro
        if not candidatos:
            return None, f"Token '{t}' não reconhecido: não é um literal e não dá match nenhum padrão lexical."

        tokens_lista.append({'type': candidatos[0], 'value': t, 'candidates': candidatos})

    return tokens_lista, None


def gerar_frase_exemplo_simples(gramatica, max_depth=30):
    nao_terminais = set(gramatica.get('nao_terminais', []))
    producoes = gramatica.get('producoes', {})

    def exemplo_terminal(t):
        s = t.strip()
        if s == 'ε':
            return ''
        if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
            return s[1:-1]
        if s in ('id', '[a-zA-Z_][a-zA-Z0-9_]*'):
            return 'x'
        if s in ('number', '[0-9]+', r'\-?[0-9]+(\.[0-9]+)?'):
            return '1'
        if '[^"' in s or 'string' in s:
            return 'texto'
        return s

    def score_producao(prod):
        if prod == ['ε']:
            return (0, 0, 0)
        nt_count = sum(1 for simbolo in prod if simbolo in nao_terminais)
        tam = len([simbolo for simbolo in prod if simbolo != 'ε'])
        return (1, nt_count, tam)

    def expandir(simbolo, depth, stack):
        if depth > max_depth:
            return None
        if simbolo == 'ε':
            return []
        if simbolo not in nao_terminais:
            return [exemplo_terminal(simbolo)]

        if stack.get(simbolo, 0) > 2:
            return None

        stack_local = dict(stack)
        stack_local[simbolo] = stack_local.get(simbolo, 0) + 1

        for prod in sorted(producoes.get(simbolo, []), key=score_producao):
            resultado = []
            ok = True
            for s in prod:
                parte = expandir(s, depth + 1, stack_local)
                if parte is None:
                    ok = False
                    break
                resultado.extend(parte)
            if ok:
                return resultado

        return None

    inicial = gramatica.get('inicial')
    if not inicial:
        return ''

    tokens = expandir(inicial, 0, {})
    if tokens is None:
        return 'x'

    frase = ' '.join(t for t in tokens if t)
    return frase.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    gramatica_texto = ""
    frase_entrada = ""
    codigo_parser = ""
    sugestao = None
    aviso_conflitos_persistentes = None
    
    if request.method == 'POST':
        acao = request.form.get('acao', 'analisar')
        gramatica_texto = request.form.get('gramatica', "")
        frase_entrada = request.form.get('frase', "")
        
        try:
            g = carregar_gramatica_da_string(gramatica_texto)
            f = calcular_first(g)
            fol = calcular_follow(g, f)
            tab, conf = gerar_tabela_ll1(g, f, fol)

            if conf:
                from core.refactor import propor_correcoes
                sugestao = propor_correcoes(g)
                if not sugestao:
                    aviso_conflitos_persistentes = (
                        "Esta gramática tem conflitos LL(1) e não foi possível gerar "
                        "uma correção automática. Não dá para resolver em LL(1) com "
                        "as transformações atuais."
                    )

            if acao == 'aplicar_sugestao' and sugestao:
                gramatica_texto = sugestao['texto_novo']
                g = carregar_gramatica_da_string(gramatica_texto)
                f = calcular_first(g)
                fol = calcular_follow(g, f)
                tab, conf = gerar_tabela_ll1(g, f, fol)
                if conf:
                    from core.refactor import propor_correcoes
                    sugestao = propor_correcoes(g)
                    if not sugestao:
                        aviso_conflitos_persistentes = (
                            "Mesmo após aplicar sugestões, a gramática continua com "
                            "conflitos LL(1). Não dá para resolver em LL(1) com as "
                            "transformações atuais."
                        )
                else:
                    sugestao = None
            
            from core.generator import gerar_codigo_parser
            codigo_parser = gerar_codigo_parser(g, tab)
            
            resultado = {
                'gramatica': g, 'tabela': tab, 'conflitos': conf, 'arvore': None,
                'first': f, 'follow': fol, 'erro_frase': None,
                'frase_sugestao': gerar_frase_exemplo_simples(g)
            }

            # Se o utilizador escreveu uma frase, tentamos gerar a árvore
            if frase_entrada.strip():
                tokens_lista, erro_tokenizacao = tokenizar_frase(frase_entrada, g)
                
                if erro_tokenizacao:
                    resultado['erro_frase'] = erro_tokenizacao
                else:
                    arvore_dict, erro_parse = gerar_arvore_derivacao_com_erro(tokens_lista, g, tab)

                    if erro_parse:
                        resultado['erro_frase'] = erro_parse
                    else:
                        resultado['arvore'] = arvore_dict
                        resultado['arvore_texto'] = arvore_para_texto(arvore_dict)
                        resultado['arvore_mermaid'] = arvore_para_mermaid(arvore_dict)

        except Exception as e:
            resultado = {'erro': str(e)}

    return render_template('index.html', 
                           resultado=resultado, 
                           gramatica_texto=gramatica_texto, 
                           frase_entrada=frase_entrada,
                           exemplos=EXEMPLOS,
                           frases_exemplo=frases_exemplo,
                           codigo_parser=codigo_parser,
                           sugestao=sugestao,
                           aviso_conflitos_persistentes=aviso_conflitos_persistentes)

if __name__ == '__main__':
    app.run(debug=True)