import json
import re
# Visitor gerado - Projeto 2026

class TreeVisitor:
    """Visitor genérico para a árvore de derivação do parser."""

    def _convert_leaf(self, s):
        if s is None: return None
        # tenta int
        try:
            return int(s)
        except Exception:
            pass
        # tenta float
        try:
            return float(s)
        except Exception:
            pass
        # retira aspas externas
        if len(s) >= 2 and ((s[0] == ' and s[-1] == ') or (s[0] == " and s[-1] == ")):
            return s[1:-1]
        return s

    def visit(self, node):
        if node is None: return None
        # folha (sem filhos)
        children = node.get('children') if isinstance(node, dict) else None
        if not children:
            return self._convert_leaf(node.get('name'))
        # dispatch por nome (tenta nome original e nome seguro)
        name = node.get('name')
        safe_name = re.sub(r"[^0-9a-zA-Z_]", "_", str(name))
        method = getattr(self, f'visit_{name}', None) or getattr(self, f'visit_{safe_name}', None)
        if method:
            return method(node)
        # default: percorre filhos
        res = []
        for c in children:
            if isinstance(c, dict):
                res.append(self.visit(c))
            else:
                res.append(self._convert_leaf(c))
        return {name: res}

def visit_Lista(self, node):
    """Visita o não-terminal Lista"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"Lista": results}

def visit_Funcao(self, node):
    """Visita o não-terminal Funcao"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"Funcao": results}

def visit_Exp(self, node):
    """Visita o não-terminal Exp"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"Exp": results}

def visit_Lista_P(self, node):
    """Visita o não-terminal Lista_P"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"Lista_P": results}

def visit_INT(self, node):
    """Visita o não-terminal INT"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"INT": results}

def visit_Sexp(self, node):
    """Visita o não-terminal Sexp"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"Sexp": results}

if __name__ == '__main__':
    print('Este ficheiro define TreeVisitor. Importa-o em parser_generated.py e usa-o para processar a árvore.')