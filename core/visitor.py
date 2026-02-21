# core/visitor.py

class TreeVisitor:
    """Classe base para percorrer a árvore de derivação."""
    
    def visit(self, node):
        """Descobre o método correto para visitar o nó atual."""
        if not node:
            return None
            
        # Limpa o nome do símbolo para ser um nome de método Python válido
        # Ex: "StmtList'" vira "visit_StmtList_prime"
        safe_symbol = str(node.symbol).replace("'", "_prime").replace("-", "_")
        method_name = f'visit_{safe_symbol}'
        
        # Procura o método na classe (ex: visit_Expr). Se não existir, usa o generic_visit
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
        """Comportamento por defeito: visita todos os filhos e junta os resultados."""
        results = []
        for child in getattr(node, 'children', []):
            res = self.visit(child)
            if res is not None:
                if isinstance(res, list):
                    results.extend(res)
                else:
                    results.append(res)
        
        # Se for um nó folha (terminal), retorna o valor do token
        if not getattr(node, 'children', []) and hasattr(node, 'token') and node.token:
            return node.token.value
            
        return "".join(str(r) for r in results if r is not None)