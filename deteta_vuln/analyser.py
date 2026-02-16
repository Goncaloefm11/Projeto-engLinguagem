from lark import Visitor, Token, Tree

class StaticAnalyser(Visitor):
    def __init__(self):
        self.issues = [] # Lista de dicionários

    def _get_atomic_value(self, node):
        if isinstance(node, Token): return node
        if isinstance(node, Tree) and len(node.children) == 1:
            return self._get_atomic_value(node.children[0])
        return None

    # Método auxiliar para guardar o erro estruturado
    def add_issue(self, tree, message, severity):
        line = getattr(tree.meta, 'line', '?')
        self.issues.append({
            'line': line,
            'message': message,
            'severity': severity
        })

    def exec_stmt(self, tree):
        val = self._get_atomic_value(tree.children[0])
        if isinstance(val, Token) and val.type == 'STRING':
            self.add_issue(tree, f"Execução de sistema: {val.value}", "WARNING")
        else:
            self.add_issue(tree, "Possível Command Injection (exec dinâmico)", "CRITICAL")

    def assign_expr(self, tree):
        var_name = tree.children[0].value
        val = self._get_atomic_value(tree.children[1])
        
        # Segredos
        if isinstance(val, Token) and val.type == 'STRING':
            suspicious = ['pass', 'key', 'secret']
            if any(s in var_name.lower() for s in suspicious):
                self.add_issue(tree, f"Segredo Hardcoded em '{var_name}'", "CRITICAL")
        
        # Estilo
        if len(var_name) < 2 and var_name not in ['i', 'j', 'x', 'y']:
             self.add_issue(tree, f"Nome curto '{var_name}'", "STYLE")

    def throw_stmt(self, tree):
        val = self._get_atomic_value(tree.children[0])
        if isinstance(val, Token) and val.type == 'STRING':
             self.add_issue(tree, "Throw de string crua (Use Objetos)", "WARNING")