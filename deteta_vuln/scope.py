from lark.visitors import Interpreter
from lark import Token, Tree

class SymbolTable:
    def __init__(self):
        self.scopes = [{}] 
    
    def enter_scope(self):
        self.scopes.append({})
        
    def exit_scope(self):
        self.scopes.pop()
        
    def declare(self, name):
        # Guarda no escopo atual
        self.scopes[-1][name] = "var"
        
    def lookup(self, name):
        # Procura do escopo atual para trás até ao global
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

# MUDANÇA: Usamos Interpreter em vez de Visitor para controlar a ordem
class ScopeAnalyser(Interpreter):
    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    # Método padrão: Visita os filhos para continuar a descida
    def __default__(self, tree):
        self.visit_children(tree)

    # --- GESTÃO DE BLOCOS (A Mágica acontece aqui) ---
    def block(self, tree):
        self.table.enter_scope()  # 1. Cria o ambiente
        self.visit_children(tree) # 2. Analisa o código lá dentro
        self.table.exit_scope()   # 3. Destrói o ambiente

    # --- DECLARAÇÃO ---
    def assign_expr(self, tree):
        # assign_expr -> VAR "=" expression
        var_token = tree.children[0]
        
        # 1. Declarar a variável (Primeiro!)
        if isinstance(var_token, Token):
            self.table.declare(var_token.value)
            
        # 2. Visitar a expressão à direita (Para ver se usa vars que existem)
        if len(tree.children) > 1:
            self.visit(tree.children[1])

    def for_loop(self, tree):
        # O FOR é especial porque a inicialização (i=0) acontece ANTES do bloco
        # Mas o escopo do 'i' deve ser visível dentro do bloco.
        self.table.enter_scope()
        self.visit_children(tree)
        self.table.exit_scope()

    def try_catch_stmt(self, tree):
        self.table.enter_scope()
        # Se tiver variável de erro (catch e), declara-a
        if len(tree.children) >= 3:
            for child in tree.children:
                if isinstance(child, Token) and child.type == 'VAR':
                    self.table.declare(child.value)
        self.visit_children(tree)
        self.table.exit_scope()

    # --- USO ---
    def var_access(self, tree):
        var_token = tree.children[0]
        name = var_token.value
        
        # Se não encontrar na tabela, é erro!
        if not self.table.lookup(name):
            line = getattr(tree.meta, 'line', '?')
            self.errors.append({
                'line': line, 
                'message': f"Variável '{name}' não declarada (Scope Error).",
                'severity': 'SCOPE'
            })