#app.py
from flask import Flask, render_template, request, session, redirect, url_for
import re
import sys
import os
import io
import contextlib
import tempfile
import types
import traceback
import json

# Adiciona a pasta raiz ao path para conseguirmos importar o 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.loader import carregar_gramatica_da_string
from core.parser_LL1 import calcular_first, calcular_follow, gerar_tabela_ll1, gerar_arvore_derivacao_com_erro, arvore_para_texto, arvore_para_mermaid, arvore_para_producoes_preordem
from core.lexer import tokenizar_frase, tokenizar_frase_com_eof
from core.ontology import gerar_ontologia
from flask import send_from_directory
from core.error_recovery import analyze_error_context, sugerir_recuperacao, format_error_message
import uuid
import time


app = Flask(__name__)
app.secret_key = 'grammar_playground_secret_key_2026'

# Server-side session storage em memória (evita cookies muito grandes)
analysis_cache = {}  # { analysis_id: { 'data': {...}, 'timestamp': time.time() } }
CACHE_EXPIRY = 3600  # 1 hora

def cleanup_cache():
    """Remove análises expiradas do cache"""
    now = time.time()
    expired_ids = [aid for aid, info in analysis_cache.items() if now - info['timestamp'] > CACHE_EXPIRY]
    for aid in expired_ids:
        del analysis_cache[aid]

def make_json_serializable(obj):
    """Converte objetos não-serializáveis (como sets) para tipos JSON-compatíveis"""
    if isinstance(obj, set):
        return sorted(list(obj))
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Objetos customizados - tenta converter para string
        return str(obj)
    else:
        return obj

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


def diagnose_parse_error(tokens_lista, gramatica, tabela, erro_msg):
    info_erro = {
        'stack_esperado': [],
        'token_recebido': None,
        'posicao': 0
    }
    
    import re
    # Extrair qual foi o token que falhou da mensagem
    m1 = re.search(r"lookahead\s*'([^']+)'", erro_msg)
    m2 = re.search(r"inesperado\s*'([^']+)'", erro_msg)
    m3 = re.search(r"extra após parsing:\s*'([^']+)'", erro_msg)
    
    if m1: info_erro['token_recebido'] = m1.group(1)
    elif m2: info_erro['token_recebido'] = m2.group(1)
    elif m3: info_erro['token_recebido'] = m3.group(1)
    
    # Extrair o que era esperado
    m_esp = re.search(r"Esperado um de:\s*(.+)", erro_msg)
    if m_esp:
        info_erro['stack_esperado'] = [e.strip() for e in m_esp.group(1).split(', ') if e.strip()]
    else:
        m_esp2 = re.search(r"\besperado\s*'([^']+)'", erro_msg)
        if m_esp2:
            info_erro['stack_esperado'] = [m_esp2.group(1)]
            
    diagnostico = analyze_error_context(
        info_erro['stack_esperado'],
        info_erro['token_recebido'] or '?',
        [],
        gramatica
    )
    
    recuperacao = sugerir_recuperacao(
        info_erro['stack_esperado'],
        info_erro['token_recebido'] or '?',
        gramatica,
        tabela
    )
    
    return {
        'erro': erro_msg,
        'diagnostico': diagnostico,
        'recuperacao': recuperacao,
        'mensagem_formatada': format_error_message(diagnostico, recuperacao)
    }
@app.route('/api/error-recovery', methods=['POST'])
def api_error_recovery():
    """
    Endpoint para obter diagnóstico de erro detalhado.
    POST data: {gramatica, tokens_lista, erro_msg}
    """
    try:
        data = request.get_json()
        gramatica_texto = data.get('gramatica', '')
        erro_msg = data.get('erro_msg', '')
        
        gramatica = carregar_gramatica_da_string(gramatica_texto)
        
        diagnostico_completo = diagnose_parse_error(
            [],  # tokens_lista vazio para agora
            gramatica,
            {},  # tabela vazia
            erro_msg
        )
        
        return diagnostico_completo
    except Exception as e:
        return {'erro': str(e)}, 400
    tokens_lista = []
    terminais = gramatica['terminais']
    producoes = gramatica['producoes']

    # Permite entradas compactas (ex.: <nome>Joana</nome>, ident="e1">)
    # separando terminais literais definidos na gramática.
    literais = gramatica.get('literais', [])

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

        # 2. Procura por padrao regex nas regras lexicais.
        for _, prods in producoes.items():
            for prod in prods:
                if len(prod) == 1:
                    padrao = prod[0]
                    try:
                        if re.fullmatch(padrao, t) and prod[0] not in candidatos:
                            candidatos.append(prod[0])
                    except re.error:
                        pass

        # Se ainda nao encontrou tipo, eh erro
        if not candidatos:
            return None, f"Token '{t}' não reconhecido: não é um literal e não dá match nenhum padrão lexical."

        # Normaliza candidatos: remove aspas externas de literais (ex: "']'" -> "]").
        def _clean(sym):
            if isinstance(sym, str) and len(sym) >= 2 and sym[0] == "'" and sym[-1] == "'":
                return sym[1:-1]
            return sym

        candidatos_normalizados = [_clean(c) for c in candidatos]
        chosen = candidatos_normalizados[0]

        tokens_lista.append({'type': chosen, 'value': t, 'candidates': candidatos_normalizados})

    return tokens_lista, None


def _run_parser_with_lexer(code_str, tokens_list, inicial_nt):
    """Executa o código do parser gerado numa namespace controlada.
    Espera que o código defina funções `rec_<NT>()` para cada não-terminal
    e que use um objeto `lexer` com método `token()` que devolve dicionários
    como {'type': ..., 'value': ...} ou None no fim.

    Retorna (stdout, stderr).
    """
    # Preparar um lexer simples que fornece os tokens em sequence
    class _SimpleLexer:
        def __init__(self, tokens):
            self._tokens = list(tokens)
            self._i = 0

        def token(self):
            if self._i >= len(self._tokens):
                return None
            t = self._tokens[self._i]
            self._i += 1
            return t

    lexer = _SimpleLexer(tokens_list)

    # Namespace controlada para exec
    globs = {
        '__builtins__': __builtins__,
        'lexer': lexer,
    }

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        # Exec do código do parser (define funções rec_<NT>)
        exec(code_str, globs)

        # Inicializar prox_simb e invocar a função inicial
        globs['prox_simb'] = lexer.token()

        start_fn_name = f"rec_{inicial_nt}"
        if start_fn_name not in globs:
            raise RuntimeError(f"Função inicial {start_fn_name} não encontrada no código do parser gerado.")

        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            try:
                globs[start_fn_name]()
            except Exception:
                # Captura traceback para stderr
                traceback.print_exc(file=stderr_buf)

    except Exception:
        traceback.print_exc(file=stderr_buf)

    return stdout_buf.getvalue(), stderr_buf.getvalue()


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
    codigo_visitor = ""
    sugestao = None
    aviso_conflitos_persistentes = None
    
    # Post-Redirect-Get pattern: recuperar dados do cache se disponível
    cleanup_cache()
    if 'analysis_id' in session:
        analysis_id = session.pop('analysis_id')
        if analysis_id in analysis_cache:
            cached = analysis_cache.pop(analysis_id)
            result_data = cached['data']
            resultado = result_data.get('resultado')
            gramatica_texto = result_data.get('gramatica_texto', '')
            frase_entrada = result_data.get('frase_entrada', '')
            codigo_parser = result_data.get('codigo_parser', '')
            codigo_visitor = result_data.get('codigo_visitor', '')
            sugestao = result_data.get('sugestao')
            aviso_conflitos_persistentes = result_data.get('aviso_conflitos_persistentes')
    
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
            # Gerar também um esqueleto de Visitor para a árvore
            try:
                from core.generator import gerar_codigo_visitor
                codigo_visitor = gerar_codigo_visitor(g)
            except Exception:
                codigo_visitor = ''

            # Se a gramática foi aceite (sem conflitos LL(1)) e temos código gerado,
            # gravamos automaticamente os ficheiros na pasta 'gerado' do projecto.
            try:
                if codigo_parser and not conf:
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    gerado_dir = os.path.join(project_root, 'gerado')
                    os.makedirs(gerado_dir, exist_ok=True)

                    parser_path = os.path.join(gerado_dir, 'parser_generated.py')
                    with open(parser_path, 'w', encoding='utf-8') as fp:
                        fp.write(codigo_parser)

                    # Nota: geração do parser table-driven removida — apenas
                    # o parser recursivo-descendente é escrito automaticamente.

                    # Se não houve código visitor gerado, tentamos criar via generator
                    if not codigo_visitor:
                        try:
                            codigo_visitor = gerar_codigo_visitor(g)
                        except Exception:
                            codigo_visitor = ''

                    if codigo_visitor:
                        # Guardar o visitor gerado automaticamente
                        visitor_auto_path = os.path.join(gerado_dir, 'visitor_auto.py')
                        with open(visitor_auto_path, 'w', encoding='utf-8') as fp:
                            fp.write(codigo_visitor)

                    # Gerar ontologia Turtle para a gramática (opcional)
                    try:
                        ontology_path = os.path.join(gerado_dir, 'grammar.ttl')
                        gerar_ontologia(g, firsts=f, follows=fol, conflitos=conf, out_path=ontology_path)
                        resultado['ontology_path'] = ontology_path
                        resultado['ontology_filename'] = os.path.basename(ontology_path)
                    except Exception:
                        # não fatal
                        pass

                    # Disponibiliza caminhos no resultado para UI se necessário
                    if resultado is None:
                        resultado = {}
                    resultado['gerado_dir'] = gerado_dir
                    resultado['parser_path'] = parser_path
            except Exception:
                # Não queremos falhar o fluxo principal só porque a escrita falhou.
                # Guardamos a mensagem de erro em resultado para debug opcional.
                if resultado is None:
                    resultado = {}
                resultado['gerado_error'] = 'Erro ao gravar ficheiros na pasta gerado.'
            
            resultado = {
                'gramatica': g, 'tabela': tab, 'conflitos': conf, 'arvore': None,
                'first': f, 'follow': fol, 'erro_frase': None,
                'frase_sugestao': gerar_frase_exemplo_simples(g)
            }

            # NOTE: 'Testar com Lexer' feature removed — tokenization/testing
            # is performed as part of the normal 'Analisar Tudo' flow when a
            # frase is provided.
            # Se o utilizador escreveu uma frase, tentamos gerar a árvore
            if frase_entrada.strip():
                tokens_lista, erro_tokenizacao = tokenizar_frase(frase_entrada, g)
                
                if erro_tokenizacao:
                    resultado['erro_frase'] = erro_tokenizacao
                    resultado['erro_tipo'] = 'TOKENIZACAO'
                else:
                    arvore_dict, erro_parse = gerar_arvore_derivacao_com_erro(tokens_lista, g, tab)

                    if erro_parse:
                        # Enriquecer com diagnóstico de error recovery
                        diagnostico_err = diagnose_parse_error(tokens_lista, g, tab, erro_parse)
                        resultado['erro_frase'] = diagnostico_err['mensagem_formatada']
                        resultado['erro_tipo'] = 'PARSING'
                        resultado['erro_diagnostico'] = diagnostico_err['diagnostico']
                        resultado['erro_recuperacao'] = diagnostico_err['recuperacao']
                        resultado['erro_detalhes'] = diagnostico_err
                        frase_corrigida = corrigir_frase_com_diagnostico(tokens_lista, erro_parse, g, tab)
                        if frase_corrigida:
                            resultado['frase_sugestao'] = frase_corrigida
                            resultado['is_correcao'] = True # Avisa o frontend para mudar o botão
                        else:
                            resultado['frase_sugestao'] = gerar_frase_exemplo_simples(g)
                            resultado['is_correcao'] = False
                    else:
                        resultado['arvore'] = arvore_dict
                        resultado['arvore_texto'] = arvore_para_texto(arvore_dict)
                        resultado['arvore_mermaid'] = arvore_para_mermaid(arvore_dict)

        except Exception as e:
            resultado = {'erro': str(e)}
        
        # Post-Redirect-Get: guardar no cache server-side e só ID na sessão
        analysis_id = str(uuid.uuid4())
        analysis_cache[analysis_id] = {
            'data': {
                'resultado': make_json_serializable(resultado) if resultado else None,
                'gramatica_texto': gramatica_texto,
                'frase_entrada': frase_entrada,
                'codigo_parser': codigo_parser,
                'codigo_visitor': codigo_visitor,
                'sugestao': make_json_serializable(sugestao) if sugestao else None,
                'aviso_conflitos_persistentes': aviso_conflitos_persistentes
            },
            'timestamp': time.time()
        }
        session['analysis_id'] = analysis_id
        return redirect(url_for('index'))

    return render_template('index.html', 
                           resultado=resultado, 
                           gramatica_texto=gramatica_texto, 
                           frase_entrada=frase_entrada,
                           exemplos=EXEMPLOS,
                           frases_exemplo=frases_exemplo,
                           codigo_parser=codigo_parser,
                           codigo_visitor=codigo_visitor,
                           sugestao=sugestao,
                           aviso_conflitos_persistentes=aviso_conflitos_persistentes)


@app.route('/api/list_visitors', methods=['GET'])
def list_visitors_api():
    """Lista todos os visitors disponíveis na pasta gerado."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gerado_dir = os.path.join(project_root, 'gerado')
        
        visitors = []
        if os.path.exists(gerado_dir):
            for filename in os.listdir(gerado_dir):
                if filename.startswith('visitor_') and filename.endswith('.py'):
                    filepath = os.path.join(gerado_dir, filename)
                    visitors.append({
                        'name': filename[:-3],  # Remove .py
                        'filename': filename,
                        'is_auto': filename == 'visitor_auto.py'
                    })
        
        visitors.sort(key=lambda x: (not x['is_auto'], x['name']))  # Auto first
        return {'visitors': visitors}
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/api/run_visitor', methods=['POST'])
def run_visitor_api():
    data = request.get_json()
    gramatica_texto = data.get('gramatica', '')
    visitor_code = data.get('visitor_code', '')
    frase = data.get('frase', '')
    visitor_name = data.get('visitor_name', None)  # Nome do visitor a usar (opcional)

    if not all([gramatica_texto, frase]):
        return {'error': 'Gramática e frase são obrigatórios.'}, 400
    
    # Se visitor_name foi fornecido, tenta carregar do ficheiro
    if visitor_name:
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gerado_dir = os.path.join(project_root, 'gerado')
            visitor_file = os.path.join(gerado_dir, f'{visitor_name}.py')
            if os.path.exists(visitor_file):
                with open(visitor_file, 'r', encoding='utf-8') as fp:
                    visitor_code = fp.read()
        except Exception as e:
            return {'error': f"Erro ao carregar visitor '{visitor_name}': {str(e)}"}, 400
    elif not visitor_code:
        return {'error': 'Código do visitor ou nome do visitor são obrigatórios.'}, 400

    try:
        # 1. Gerar a árvore a partir da gramática e da frase
        gramatica = carregar_gramatica_da_string(gramatica_texto)
        firsts = calcular_first(gramatica)
        follows = calcular_follow(gramatica, firsts)
        tabela, _ = gerar_tabela_ll1(gramatica, firsts, follows)
        
        tokens, erro_tok = tokenizar_frase(frase, gramatica)
        if erro_tok:
            return {'error': f"Erro de tokenização: {erro_tok}"}, 400

        arvore, erro_parse = gerar_arvore_derivacao_com_erro(tokens, gramatica, tabela)
        if erro_parse:
            return {'error': f"Erro de parsing: {erro_parse}"}, 400

        # 2. Executar o código do visitor para o ter no scope
        visitor_module = types.ModuleType('visitor_module')
        exec(visitor_code, visitor_module.__dict__)

        # 3. Procura pela classe do visitor
        VisitorClass = getattr(visitor_module, 'TreeVisitor', None)
        if not VisitorClass:
            # Tenta encontrar qualquer classe que não seja 'NodeVisitor' ou built-in
            for name, obj in visitor_module.__dict__.items():
                if isinstance(obj, type) and name not in ('NodeVisitor', 'object') and not name.startswith('_'):
                    # Verifica se tem método 'visit'
                    if hasattr(obj, 'visit'):
                        VisitorClass = obj
                        break
        
        if not VisitorClass:
            return {'error': "Não foi encontrada uma classe de Visitor com método 'visit'."}, 400

        visitor_instance = VisitorClass()
        
        # 4. Executar o visitor na árvore
        # O 'visit' pode retornar qualquer coisa, então capturamos a saída
        # e também o que for printado para stdout.
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            result = visitor_instance.visit(arvore)
        
        stdout_output = stdout_buf.getvalue()

        # Prepara o resultado para ser JSON serializável
        final_result = result
        if isinstance(result, (dict, list, str, int, float, bool, type(None))):
            final_result = result
        else:
            # Tenta converter para string se não for um tipo básico
            try:
                final_result = str(result)
            except:
                final_result = f"Resultado do tipo '{type(result).__name__}' não é serializável."

        return {
            'result': final_result,
            'stdout': stdout_output
        }

    except Exception as e:
        return {'error': f"Erro ao executar o visitor: {traceback.format_exc()}"}, 500


@app.route('/api/save_visitor', methods=['POST'])
def save_visitor_api():
    """Guarda um novo visitor na pasta gerado."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        code = data.get('code', '').strip()
        
        if not name or not code:
            return {'error': 'Nome e código do visitor são obrigatórios.'}, 400
        
        # Validar nome (apenas caracteres seguros)
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return {'error': 'Nome do visitor deve conter apenas letras, números e underscore.'}, 400
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gerado_dir = os.path.join(project_root, 'gerado')
        os.makedirs(gerado_dir, exist_ok=True)
        
        visitor_path = os.path.join(gerado_dir, f'{name}.py')
        with open(visitor_path, 'w', encoding='utf-8') as fp:
            fp.write(code)
        
        return {'success': True, 'message': f"Visitor '{name}' guardado com sucesso."}
    except Exception as e:
        return {'error': f"Erro ao guardar visitor: {str(e)}"}, 500


@app.route('/gerado/<path:filename>', methods=['GET'])
def serve_gerado(filename):
    """Serve ficheiros da pasta gerado."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gerado_dir = os.path.join(project_root, 'gerado')
        
        # Segurança: verificar que o ficheiro está dentro da pasta gerado
        requested_path = os.path.join(gerado_dir, filename)
        if not os.path.abspath(requested_path).startswith(os.path.abspath(gerado_dir)):
            return {'error': 'Acesso negado.'}, 403
        
        if os.path.exists(requested_path):
            return send_from_directory(gerado_dir, filename)
        else:
            return {'error': 'Ficheiro não encontrado.'}, 404
    except Exception as e:
        return {'error': str(e)}, 500



    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gerado_dir = os.path.join(project_root, 'gerado')
    return send_from_directory(gerado_dir, filename, as_attachment=True)

def corrigir_frase_com_diagnostico(tokens_lista, erro_parse, gramatica, tabela):
    import re
    if not tokens_lista:
        return ""
    
    # Ignora o EOF interno ($)
    t_values = [t['value'] for t in tokens_lista if t.get('type') != '$']
    frase_atual = " ".join(t_values)
    
    def concretizar(t):
        """Transforma regras em exemplos reais."""
        if not t or t in ('ε', '$', "''", '""'): return ''
        s = t.strip()
        if len(s) >= 2 and s[0] == "'" and s[-1] == "'": return s[1:-1]
        
        s_lower = s.lower()
        if s_lower in ('id', 'identificador'): return 'x'
        if s_lower in ('number', 'int', 'numero'): return '1'
        if s_lower in ('string', 'texto') or '[^' in s: return '"texto"'
        if s_lower in ('boolean', 'bool'): return 'true'
        
        if s.startswith('[a-z'): return 'var'
        if s.startswith('[0-9') or s.startswith(r'\-?[0-9]'): return '1'
        return s

    def rank_token(t):
        """Sistema de prioridades para evitar loops infinitos."""
        s = concretizar(t)
        # 1. Prioridade Máxima: Fechar blocos ou terminar a frase
        if s in (']', ')', '}', '.', ';', '?>') or s.startswith('</'): return 1
        # 2. Prioridade Alta: Literais (fecham o ramo sem abrir novos)
        if s in ('x', '1', '"texto"', 'true', 'var', '0') or s.isalnum(): return 2
        # 4. Prioridade Mínima (PERIGO): Abrir blocos
        if s in ('[', '(', '{', '<', '<?xml') or (s.startswith('<') and not s.startswith('</')): return 4
        return 3

    # Resolve a frase iterativamente (limite seguro de 30 ciclos)
    for iteracao in range(30):
        tokens_atuais, err_tok = tokenizar_frase(frase_atual, gramatica)
        if err_tok: break
        
        arvore, erro_p = gerar_arvore_derivacao_com_erro(tokens_atuais, gramatica, tabela)
        
        # A árvore foi gerada com sucesso, a frase está perfeita!
        if not erro_p:
            return frase_atual

        # Interpretação cirúrgica da string de erro LL(1)
        esperados = []
        m_esp = re.search(r"Esperado um de:\s*(.+)", erro_p)
        if m_esp:
            bruto = m_esp.group(1)
            # Proteção especial se a vírgula for o token esperado (ex: ,, ])
            if bruto.startswith(',,'):
                esperados = [','] + [e.strip() for e in bruto[2:].split(',')]
            else:
                esperados = [e.strip() for e in bruto.split(',')]
        else:
            m_esp2 = re.search(r"\besperado\s*'([^']+)'", erro_p)
            if m_esp2: esperados = [m_esp2.group(1)]
            
        token_falha = ''
        m_falha = re.search(r"lookahead\s*'([^']+)'", erro_p) or \
                  re.search(r"inesperado\s*'([^']+)'", erro_p) or \
                  re.search(r"extra após parsing:\s*'([^']+)'", erro_p)
        if m_falha: token_falha = m_falha.group(1)

        uteis = [e for e in esperados if e and e.strip() not in ('ε', '$')]
        t_atuais_val = [t['value'] for t in tokens_atuais if t.get('type') != '$']
        nova_frase = frase_atual

        if "extra após parsing" in erro_p:
            # Remove o token a mais (do fim para o início)
            for i in reversed(range(len(tokens_atuais))):
                if tokens_atuais[i]['value'] == token_falha or tokens_atuais[i].get('type') == token_falha:
                    val_remover = tokens_atuais[i]['value']
                    # Remover pelo valor correspondente
                    for j in reversed(range(len(t_atuais_val))):
                        if t_atuais_val[j] == val_remover:
                            t_atuais_val.pop(j)
                            break
                    nova_frase = " ".join(t_atuais_val)
                    break
                
        elif uteis:
            # Ordena pela nossa tabela de prioridades e insere
            uteis.sort(key=rank_token)
            token_escolhido = concretizar(uteis[0])
            
            if token_escolhido:
                if token_falha == '$' or token_falha == '':
                    t_atuais_val.append(token_escolhido)
                else:
                    inserido = False
                    for i in range(len(tokens_atuais)):
                        if tokens_atuais[i]['value'] == token_falha or tokens_atuais[i].get('type') == token_falha:
                            # Inserir antes desse token
                            val_alvo = tokens_atuais[i]['value']
                            for j in range(len(t_atuais_val)):
                                if t_atuais_val[j] == val_alvo:
                                    t_atuais_val.insert(j, token_escolhido)
                                    inserido = True
                                    break
                            if inserido:
                                break
                    if not inserido:
                        t_atuais_val.append(token_escolhido)
                        
                nova_frase = " ".join(t_atuais_val)

        # Tranca de segurança: quebra o loop se o código não alterou a frase
        if nova_frase == frase_atual:
            break
            
        frase_atual = nova_frase

    return frase_atual

if __name__ == '__main__':
    app.run(debug=True)

#para remover a porta nao apagar
#kill -9 $(lsof -t -i:5000)