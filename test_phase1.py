import sys
import os

# Garantir que o Python encontra a pasta 'core'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.grammar import GrammarParser, EPSILON, END_MARKER
from core.ll1_analyzer import LL1Analyzer
from core.parser_generator import RecursiveDescentGenerator, TableDrivenGenerator
from core.derivation_tree import build_derivation_tree
from core.visitor import TreeVisitor

# ==========================================
# GRAMÁTICAS DE TESTE
# ==========================================

# Gramática 1: Perfeitamente LL(1)
GRAMMAR_LL1 = """
S → A B
A → a | ε
B → b | c
"""

# Gramática 2: Conflito FIRST/FIRST (Ambiguidade de prefixo comum)
GRAMMAR_FIRST_FIRST = """
S → a B | a C
B → b
C → c
"""

# Gramática 3: Conflito FIRST/FOLLOW (Anulável com FIRST e FOLLOW em interseção)
GRAMMAR_FIRST_FOLLOW = """
S → A a
A → a | ε
"""

# Gramática 4: Expressões aritméticas simples para testar a árvore
GRAMMAR_EXPR = """
E → T E'
E' → + T E' | ε
T → id
"""
# Subconjunto de Pascal exigido no PDF
PASCAL_SUBSET = """
Program → StmtList
StmtList → Stmt StmtList'
StmtList' → ; Stmt StmtList' | ε
Stmt → id := Expr
Expr → Term Expr'
Expr' → + Term Expr' | ε
Term → id | number
"""

# Gramática Inválida (Para testar a robustez do teu Parser da Meta-Gramática)
INVALID_META_GRAMMAR = """
Program -> 
SemSeta id
Head Com Espaco -> id
"""

# Gramática com Conflito FIRST/FIRST (Ambiguidade do 'if-then-else' clássico ou prefixo comum)
GRAMMAR_FIRST_FIRSTv2 = """
S → i E t S S' | a
S' → e S | ε
E → b
# Conflito injetado propositadamente para falhar:
A → x y | x z
"""

# Gramática com Conflito FIRST/FOLLOW
GRAMMAR_FIRST_FOLLOW = """
S → A a
A → a | ε
"""

def test_01_grammar_parsing_and_validation():
    """Testa se o parser de gramáticas lê corretamente os símbolos e produções."""
    grammar = GrammarParser.parse(GRAMMAR_LL1)
    errors = grammar.validate()
    
    assert len(errors) == 0, "A gramática LL(1) válida não deve ter erros de validação."
    assert str(grammar.start_symbol) == "S", "O símbolo inicial deve ser 'S'."
    
    # Verificar identificação de terminais e não-terminais
    terminals = {str(t) for t in grammar.terminals}
    non_terminals = {str(nt) for nt in grammar.non_terminals}
    
    assert "a" in terminals and "b" in terminals and "c" in terminals
    assert "S" in non_terminals and "A" in non_terminals and "B" in non_terminals


def test_02_first_and_follow_sets():
    """Testa o cálculo correto dos conjuntos FIRST e FOLLOW."""
    grammar = GrammarParser.parse(GRAMMAR_LL1)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    # Testar FIRST sets
    first_A = {str(s) for s in analyzer.first_sets[grammar.get_symbol_by_name("A")]}
    assert "a" in first_A and "ε" in first_A, "FIRST(A) deve conter 'a' e 'ε'."
    
    # Testar FOLLOW sets
    follow_A = {str(s) for s in analyzer.follow_sets[grammar.get_symbol_by_name("A")]}
    # Como S -> A B, FOLLOW(A) deve conter FIRST(B) = {'b', 'c'}
    assert "b" in follow_A and "c" in follow_A, "FOLLOW(A) deve conter 'b' e 'c'."


def test_03_detect_first_first_conflict():
    """Testa a deteção de conflitos FIRST/FIRST e a respetiva sugestão."""
    grammar = GrammarParser.parse(GRAMMAR_FIRST_FIRST)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    assert analyzer.ll1_table.has_conflicts() is True, "Deve detetar conflito na gramática ambígua."
    
    conflicts = analyzer.ll1_table.conflicts
    assert len(conflicts) > 0
    assert conflicts[0].type == "FIRST/FIRST", "O conflito deve ser do tipo FIRST/FIRST."
    assert "Fatoração à esquerda" in conflicts[0].suggestion or "ambiguidade" in conflicts[0].suggestion, "Deve sugerir fatoração ou avisar sobre ambiguidade[cite: 10]."


def test_04_detect_first_follow_conflict():
    """Testa a deteção de conflitos FIRST/FOLLOW e a respetiva sugestão."""
    grammar = GrammarParser.parse(GRAMMAR_FIRST_FOLLOW)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    assert analyzer.ll1_table.has_conflicts() is True
    
    conflicts = analyzer.ll1_table.conflicts
    assert any(c.type == "FIRST/FOLLOW" for c in conflicts), "Deve detetar um conflito FIRST/FOLLOW."


def test_05_generate_recursive_descent_parser():
    """Testa a geração do parser recursivo descendente[cite: 11]."""
    grammar = GrammarParser.parse(GRAMMAR_LL1)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    generator = RecursiveDescentGenerator(grammar, analyzer)
    python_code = generator.generate("python")
    
    assert "class Parser:" in python_code, "O código deve conter a classe base do Parser."
    assert "def parse_s(self)" in python_code.lower(), "Deve conter a função de parse para o símbolo S."
    assert "def parse_a(self)" in python_code.lower(), "Deve conter a função de parse para o símbolo A."


def test_06_generate_table_driven_parser():
    """Testa a geração do parser dirigido por tabela[cite: 12]."""
    grammar = GrammarParser.parse(GRAMMAR_LL1)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    generator = TableDrivenGenerator(grammar, analyzer)
    python_code = generator.generate("python")
    
    assert "PARSE_TABLE" in python_code, "O código deve exportar a tabela LL(1)."
    assert "TableDrivenParser" in python_code, "O código deve conter a classe do parser por tabela."


def test_07_build_derivation_tree_outputs():
    """Testa a geração da árvore de derivação nos formatos exigidos."""
    input_phrase = "id + id"
    result = build_derivation_tree(GRAMMAR_EXPR, input_phrase)
    
    assert result["success"] is True, f"O parse da frase '{input_phrase}' falhou: {result.get('errors')}"
    
    # Verificar se os formatos gráficos e textuais estão presentes 
    assert "tree_text" in result, "Deve conter a representação textual."
    assert "tree_mermaid" in result, "Deve conter a representação Mermaid."
    assert "tree_d3" in result, "Deve conter a representação D3.js JSON."
    assert "id" in result["tree_text"], "A árvore textual deve conter o terminal 'id'."


def test_08_visitor_code_generation():
    """Testa a base da função de visita para geração de código.
    Nota: Isto testa a infraestrutura interna simulando o que farás na Web.
    """
    # 1. Obter a árvore pura (mock do que acontece na tua rota Flask)
    grammar = GrammarParser.parse(GRAMMAR_EXPR)
    from core.lark_parser import LarkTreeBuilder
    builder = LarkTreeBuilder(grammar)
    tree_root, errors = builder.parse("id + id")
    
    assert len(errors) == 0
    assert tree_root is not None
    
    # 2. Simular a execução dinâmica do código do utilizador (Visitor Pattern) 
    user_visitor_code = """
class MyVisitor:
    def visit(self, node):
        if not node: return ""
        
        # Limpar nome (ex: E' -> E_prime)
        safe_name = str(node.symbol).replace("'", "_prime")
        method = getattr(self, f"visit_{safe_name}", self.generic_visit)
        return method(node)
        
    def generic_visit(self, node):
        res = []
        for child in getattr(node, 'children', []):
            res.append(self.visit(child))
        
        if getattr(node, 'is_terminal', lambda: False)():
            val = getattr(node, 'token_value', '')
            if val: return val
            
        return " ".join(filter(None, res))
        
    def visit_T(self, node):
        # Transforma o identificador em algo diferente para provar que a visita ocorreu
        val = self.generic_visit(node)
        return f"VAR({val})"
"""
    local_env = {}
    exec(user_visitor_code, globals(), local_env)
    
    visitor_instance = local_env["MyVisitor"]()
    generated_code = visitor_instance.visit(tree_root)
    
    # Validar se o Visitor processou a árvore e alterou a string conforme a regra de "T"
    assert "VAR(id)" in generated_code, "A função de visita do utilizador falhou a gerar o código customizado."

def test_01_meta_grammar_strict_parsing():
    """Prova que a meta-gramática rejeita sintaxe inválida e aceita a correta."""
    print("A testar análise rigorosa da Meta-Gramática...")
    
    # 1. Testar o Pascal Subset válido
    grammar = GrammarParser.parse(PASCAL_SUBSET)
    assert len(grammar.productions) > 0, "Deveria ter feito o parse das produções do Pascal."
    assert str(grammar.start_symbol) == "Program", "O símbolo inicial tem de ser 'Program'."
    
    # 2. Testar rejeição de gramática inválida
    try:
        GrammarParser.parse(INVALID_META_GRAMMAR)
        assert False, "O parser devia ter falhado com uma gramática sem seta ou com espaços na cabeça."
    except ValueError as e:
        assert "Erro Sintático" in str(e) or "único símbolo" in str(e), "A mensagem de erro deve ser clara sobre o erro sintático."

def test_02_pascal_ll1_properties():
    """Valida os conceitos LL(1) no exemplo do Pascal exigido no PDF [cite: 22, 25-39]."""
    print("A testar propriedades LL(1) no subconjunto de Pascal...")
    grammar = GrammarParser.parse(PASCAL_SUBSET)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    # Testar FIRST(Expr') -> tem de conter '+' e 'ε'
    expr_prime = grammar.get_symbol_by_name("Expr'")
    first_expr_prime = {str(s) for s in analyzer.first(expr_prime)}
    assert "+" in first_expr_prime, "FIRST(Expr') deve conter '+'"
    assert "ε" in first_expr_prime, "FIRST(Expr') deve conter 'ε'"
    
    # Testar FOLLOW(Stmt) -> SmtList' produz '; Stmt ...', logo FOLLOW(Stmt) tem de conter ';'
    stmt = grammar.get_symbol_by_name("Stmt")
    follow_stmt = {str(s) for s in analyzer.follow(stmt)}
    assert ";" in follow_stmt or "$" in follow_stmt, "FOLLOW(Stmt) calculado corretamente."
    
    assert analyzer.ll1_table.has_conflicts() == False, "O subconjunto de Pascal dado não deve ter conflitos LL(1)."

def test_03_conflict_detection_and_suggestions():
    """Valida a deteção de conflitos FIRST/FIRST e FIRST/FOLLOW e as sugestões."""
    print("A testar deteção e correção de Conflitos...")
    
    # FIRST/FIRST
    g1 = GrammarParser.parse(GRAMMAR_FIRST_FIRSTv2)
    a1 = LL1Analyzer(g1)
    a1.analyze()
    assert a1.ll1_table.has_conflicts(), "Devia detetar conflito na gramática FIRST/FIRST."
    c1 = [c for c in a1.ll1_table.conflicts if c.type == "FIRST/FIRST"]
    assert len(c1) > 0, "Deve reportar pelo menos um conflito FIRST/FIRST."
    assert "Fatoração à esquerda" in c1[0].suggestion or "ambiguidade" in c1[0].suggestion, "Deve sugerir fatoração[cite: 10]."

    # FIRST/FOLLOW
    g2 = GrammarParser.parse(GRAMMAR_FIRST_FOLLOW)
    a2 = LL1Analyzer(g2)
    a2.analyze()
    assert a2.ll1_table.has_conflicts(), "Devia detetar conflito na gramática FIRST/FOLLOW."
    c2 = [c for c in a2.ll1_table.conflicts if c.type == "FIRST/FOLLOW"]
    assert len(c2) > 0, "Deve reportar pelo menos um conflito FIRST/FOLLOW."
    assert "anulável" in c2[0].description, "A justificação do erro tem de mencionar produções anuláveis[cite: 23]."

def test_04_parser_generators():
    """Garante que os dois tipos de parser são gerados com sucesso[cite: 11, 12]."""
    print("A testar geração dos parsers (Recursivo e Tabela)...")
    grammar = GrammarParser.parse(PASCAL_SUBSET)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    # Parser Recursivo Descendente [cite: 11]
    rd_gen = RecursiveDescentGenerator(grammar, analyzer)
    rd_code = rd_gen.generate("python")
    assert "def parse_stmtlist_prime" in rd_code.lower() or "def parse_stmtlist" in rd_code.lower(), "Métodos de parse devem ser criados."
    
    # Parser Top-Down por Tabela [cite: 12]
    td_gen = TableDrivenGenerator(grammar, analyzer)
    td_code = td_gen.generate("python")
    assert "PARSE_TABLE =" in td_code or "PARSE_TABLE:" in td_code, "A tabela de parsing deve estar injetada no código gerado."

def test_05_derivation_tree_and_formats():
    """Verifica se a árvore de derivação é gerada nos formatos textual e gráfico."""
    print("A testar geração da Árvore de Derivação em formato texto e gráfico...")
    
    # Frase válida para o subconjunto de Pascal:
    input_phrase = "id := id + number"
    
    # Modificamos temporariamente a gramática para que 'Program' aceite diretamente 'Stmt' 
    # ou usamos o parsing do topo: 'Program -> StmtList -> Stmt' (não tem terminal inicial antes do id)
    result = build_derivation_tree(PASCAL_SUBSET, input_phrase)
    
    assert result.get("success") is True, f"Parse falhou: {result.get('errors')}"
    
    # Verificar saídas textuais e gráficas
    assert "tree_text" in result and result["tree_text"].strip() != "", "Árvore textual ausente."
    assert "tree_mermaid" in result and "graph TD" in result["tree_mermaid"], "Árvore Mermaid (gráfica) inválida/ausente."
    assert "tree_d3" in result and "name" in result["tree_d3"], "Árvore D3 (JSON) inválida/ausente."

def test_06_visitor_pattern_execution():
    """Testa complexo da introdução de funções de visita para geração de código."""
    print("A testar Padrão Visitor para Geração de Código...")
    
    grammar = GrammarParser.parse(PASCAL_SUBSET)
    from core.lark_parser import LarkTreeBuilder
    builder = LarkTreeBuilder(grammar)
    tree_root, errors = builder.parse("id := id + number")
    
    assert not errors, "A árvore deve ser gerada sem erros para o teste do Visitor."

    # Código Python que um utilizador introduziria na interface Web
    # Vamos gerar código do tipo "Atribuição: {variavel} = {expressão}"
    visitor_code = """
class MyVisitor(TreeVisitor):
    def visit_Stmt(self, node):
        # Stmt -> id := Expr
        id_node = node.children[0]
        expr_node = node.children[2]
        
        id_val = id_node.token_value
        expr_val = self.visit(expr_node)
        return f"ATRIBUIÇÃO({id_val} = {expr_val})"

    def visit_Expr(self, node):
        # Avalia toda a expressão juntando os filhos recursivamente
        return self.generic_visit(node)
"""
    local_env = {}
    global_env = {'TreeVisitor': TreeVisitor}
    
    # Execução dinâmica protegida (simulando a rota /execute-visitor)
    exec(visitor_code, global_env, local_env)
    
    visitor_instance = local_env["MyVisitor"]()
    generated_code = visitor_instance.visit(tree_root)
    
    # Como o generic_visit junta tudo (ex: "id + number"), a string final deve conter a formatação exigida
    assert "ATRIBUIÇÃO" in generated_code, "O Visitor devia ter formatado a saída."
    assert "=" in generated_code, "O Visitor falhou a processar os filhos corretamente."

if __name__ == "__main__":
    print("A iniciar testes da Fase 1...")
    test_01_grammar_parsing_and_validation()
    test_02_first_and_follow_sets()
    test_03_detect_first_first_conflict()
    test_04_detect_first_follow_conflict()
    test_05_generate_recursive_descent_parser()
    test_06_generate_table_driven_parser()
    test_07_build_derivation_tree_outputs()
    test_08_visitor_code_generation()
    test_01_meta_grammar_strict_parsing()
    test_02_pascal_ll1_properties()
    test_03_conflict_detection_and_suggestions()
    test_04_parser_generators()
    test_05_derivation_tree_and_formats()
    test_06_visitor_pattern_execution()
    print("✅ TODOS OS TESTES PASSARAM!")