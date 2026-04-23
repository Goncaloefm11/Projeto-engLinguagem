# visitor_generated.py
# Visitor gerado - Projeto 2026
import json
import re

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

def visit_B(self, node):
    """Visita o não-terminal B"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"B": results}

def visit_s(self, node):
    """Visita o não-terminal s"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"s": results}

def visit_C(self, node):
    """Visita o não-terminal C"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"C": results}

def visit_A(self, node):
    """Visita o não-terminal A"""
    results = []
    for c in node.get('children', []):
        if isinstance(c, dict):
            results.append(self.visit(c))
        else:
            results.append(self._convert_leaf(c))
    return {"A": results}

if __name__ == '__main__':
    print('Este ficheiro define TreeVisitor. Importa-o em parser_generated.py e usa-o para processar a árvore.')