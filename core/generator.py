# core/generator.py
import re


def _sanitize(name):
    """Converte um nome (p.ex. "T'") para um identificador Python seguro: T_"""
    return re.sub(r"[^0-9a-zA-Z_]", "_", str(name))


def gerar_codigo_parser(gramatica, tabela):
    codigo = [
    "import sys",
    "import json",
        "# Parser Gerado - Projeto 2026",
        f"gramatica = {repr(gramatica)}",
        "prox_simb = None",
        "",
        "def parser_error(simb):",
        "    print(f'Erro sintático: token inesperado {simb}')",
        "",
        "def rec_term(esperado):",
        "    global prox_simb",
        "    if prox_simb and prox_simb['type'] == esperado:",
        "        no_folha = {'name': prox_simb['value']}  # CRIA O NÓ",
        "        prox_simb = lexer.token()",
        "        return no_folha",
        "    else:",
        "        parser_error(prox_simb)",
        "        prox_simb = ('erro', '', 0, 0)",
        "        return None",
        "# --------------------------------------------------------",
        ""
    ]

    # Mapear não-terminais para nomes seguros (para usar em identificadores)
    nt_safe = {nt: _sanitize(nt) for nt in gramatica.get('nao_terminais', [])}

    # Gerar funções para cada Não-Terminal 
    for nt, caminhos in tabela.items():
        safe_nt = nt_safe.get(nt, _sanitize(nt))
        codigo.append(f"def rec_{safe_nt}():")
        codigo.append("    global prox_simb")
        codigo.append(f"    no_atual = {{'name': '{nt}', 'children': []}}") # Inicializa o nó atual
        
        for i, (term, prod) in enumerate(caminhos.items()):
            condicao = "if" if i == 0 else "elif"
            # O terminal '$' representa o fim da entrada
            if term == "$":
                t_cond = "None"
            else:
                # Se for um literal escrito como '\'x\'' na gramática, limpamos as aspas externas
                if len(term) >= 2 and term[0] == "'" and term[-1] == "'":
                    cleaned = term[1:-1]
                else:
                    cleaned = term
                t_cond = repr(cleaned)

            codigo.append(f"    {condicao} prox_simb and prox_simb['type'] == {t_cond}:")
            if prod == ['ε']:
                codigo.append("        no_atual['children'].append({'name': 'ε'})") # Adiciona o epsilon aos filhos
            else:
                for j, simbolo in enumerate(prod): # enumerate para ter id único de cada símbolo
                    if simbolo in gramatica.get('nao_terminais', []):
                        safe_child = nt_safe.get(simbolo, _sanitize(simbolo))
                        codigo.append(f"        filho_{j} = rec_{safe_child}()")
                        codigo.append(f"        if filho_{j}: no_atual['children'].append(filho_{j})")
                    else:
                        # Limpar aspas com segurança e capturar/adicionar o filho
                        if len(simbolo) >= 2 and simbolo[0] == "'" and simbolo[-1] == "'":
                            s_clean = simbolo[1:-1]
                        else:
                            s_clean = simbolo
                        codigo.append(f"        filho_{j} = rec_term({repr(s_clean)})")
                        codigo.append(f"        if filho_{j}: no_atual['children'].append(filho_{j})")
            
            # Retornar o nó se entrou nesta condição (construção da AST)
            codigo.append("        return no_atual")
        
        # Fallback final caso nenhuma condição se verifique
        codigo.append("    else:")
        codigo.append("        parser_error(prox_simb)")
        codigo.append("        return None\n")

    # --- Runner/tokenizador genérico embutido ---
    inicial_safe = _sanitize(gramatica.get('inicial')) if gramatica.get('inicial') else ''
    runner = [
        "",
        "def _clean(sym):",
        "    if isinstance(sym, str) and len(sym) >= 2 and sym[0] == \"'\" and sym[-1] == \"'\":",
        "        return sym[1:-1]",
        "    return sym",
        "",
        "def tokenizar_frase_com_eof_local(frase, gramatica):",
        "    import re",
        "    terminais = gramatica.get('terminais', [])",
        "    producoes = gramatica.get('producoes', {})",
        "    literais = gramatica.get('literais', []) if 'literais' in gramatica else []",
        "    partes = []",
        "    if literais:",
        "        pattern = '(' + '|'.join(re.escape(l) for l in sorted(set(literais), key=len, reverse=True)) + ')'",
        "        for pedaco in re.split(pattern, frase):",
        "            if not pedaco:",
        "                continue",
        "            if pedaco in literais:",
        "                partes.append(pedaco)",
        "            else:",
        "                partes.extend(pedaco.split())",
        "    else:",
        "        partes = frase.split()",
        "",
        "    tokens = []",
        "    padroes = []",
        "    for nt, prods in producoes.items():",
        "        for p in prods:",
        "            if len(p) == 1:",
        "                padroes.append(p[0])",
        "",
        "    for part in partes:",
        "        candidatos = []",
        "        if part in terminais:",
        "            candidatos.append(part)",
        "        for pat in padroes:",
        "            try:",
        "                if re.fullmatch(pat, part) and pat not in candidatos:",
        "                    candidatos.append(pat)",
        "            except re.error:",
        "                pass",
        "",
        "        if not candidatos:",
        "            return None, f\"Token '{part}' não reconhecido.\"",
        "",
        "        candidatos_normalizados = [_clean(c) for c in candidatos]",
        "        tokens.append({'type': candidatos_normalizados[0], 'value': part, 'candidates': candidatos_normalizados})",
        "",
        "    tokens.append({'type': '$', 'value': '$', 'candidates': ['$']})",
        "    return tokens, None",
        "",
        "class _SimpleLexer:",
        "    def __init__(self, tokens):",
        "        self._tokens = list(tokens)",
        "        self._i = 0",
        "    def token(self):",
        "        if self._i >= len(self._tokens):",
        "            return None",
        "        t = self._tokens[self._i]",
        "        self._i += 1",
        "        return t",
        "",
        "if __name__ == '__main__':",
        "    import sys, json",
        "    if len(sys.argv) > 1:",
        "        frase = ' '.join(sys.argv[1:])",
        "    else:",
        "        try:",
        "            frase = input('Frase para parser: ')",
        "        except EOFError:",
        "            frase = ''",
        "",
        "    tokens, err = tokenizar_frase_com_eof_local(frase, gramatica)",
        "    if err:",
        "        print('Erro léxico:', err)",
        "        sys.exit(1)",
        "",
        "    lexer = _SimpleLexer(tokens)",
        "    prox_simb = lexer.token()",
    f"    start_fn = globals().get(\"rec_{inicial_safe}\")",
        "    if not start_fn:",
        "        print('Função inicial rec_' + str(gramatica.get('inicial')) + ' não encontrada.')",
        "        sys.exit(1)",
        "    try:",
        "        raiz = start_fn()",
        "        print('\\nArvore gerada pela frase:')",
        "        def _pretty_print(node, nivel=0):",
        "            if node is None:",
        "                return",
        "            indent = '  ' * nivel",
        "            # Se o nó tem exatamente um filho que é folha, imprimimos em linha: NT -> leaf",
        "            children = node.get('children', []) if isinstance(node, dict) else []",
        "            if len(children) == 1 and (not children[0].get('children')):",
        "                print(f\"{indent}{node.get('name')} -> {children[0].get('name')}\")",
        "                return",
        "            # Caso contrário, imprimimos o nome e descemos aos filhos",
        "            print(f\"{indent}{node.get('name')}\")",
        "            for c in children:",
        "                if c.get('children'):",
        "                    _pretty_print(c, nivel+1)",
        "                else:",
        "                    print('  ' * (nivel+1) + str(c.get('name')))",
    "        _pretty_print(raiz)",
    "        # Tentar invocar um Visitor externo (visitor_generated.py) se existir",
    "        try:",
    "            from visitor_generated import TreeVisitor",
    "            v = TreeVisitor()",
    "            resultado_visit = v.visit(raiz)",
    "            print('\\nVisitor output:')",
    "            try:",
    "                print(json.dumps(resultado_visit, ensure_ascii=False, indent=2))",
    "            except Exception:",
    "                print(resultado_visit)",
    "        except Exception:",
    "            print('\\nNota: para usar um Visitor automÃ¡tico, descarregue visitor_generated.py e coloque-o na mesma pasta que este ficheiro.')",
    "    except Exception:",
    "        import traceback",
    "        traceback.print_exc()",
    "        sys.exit(1)",
    ]

    return "\n".join(codigo + runner)


def gerar_codigo_visitor(gramatica):
    """Gera um visitor funcional que converte folhas e percorre a árvore.

    O visitor devolve para cada não-terminal um dicionário {NT: [filhos]} e para
    folhas tenta converter para int/float, remove aspas de strings e devolve a string.
    """
    codigo = [
        "import json",
        "import re",
        "# Visitor gerado - Projeto 2026",
        "",
        "class TreeVisitor:",
        "    \"\"\"Visitor genérico para a árvore de derivação do parser.\"\"\"",
        "",
        "    def _convert_leaf(self, s):",
        "        if s is None: return None",
        "        # tenta int",
        "        try:",
        "            return int(s)",
        "        except Exception:",
        "            pass",
        "        # tenta float",
        "        try:",
        "            return float(s)",
        "        except Exception:",
        "            pass",
        "        # retira aspas externas",
        "        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):",
        "            return s[1:-1]",
        "        return s",
        "",
        "    def visit(self, node):",
        "        if node is None: return None",
        "        # folha (sem filhos)",
        "        children = node.get('children') if isinstance(node, dict) else None",
        "        if not children:",
        "            return self._convert_leaf(node.get('name'))",
    "        # dispatch por nome (tenta nome original e nome seguro)",
    "        name = node.get('name')",
    "        safe_name = re.sub(r\"[^0-9a-zA-Z_]\", \"_\", str(name))",
    "        method = getattr(self, f'visit_{name}', None) or getattr(self, f'visit_{safe_name}', None)",
    "        if method:",
    "            return method(node)",
        "        # default: percorre filhos",
        "        res = []",
        "        for c in children:",
        "            if isinstance(c, dict):",
        "                res.append(self.visit(c))",
        "            else:",
        "                res.append(self._convert_leaf(c))",
        "        return {name: res}",
        "",
    ]

    nt_safe = {nt: _sanitize(nt) for nt in gramatica.get('nao_terminais', [])}
    for nt in gramatica.get('nao_terminais', []):
        safe_nt = nt_safe.get(nt, _sanitize(nt))
        codigo.append(f"def visit_{safe_nt}(self, node):")
        codigo.append("    \"\"\"Visita o não-terminal %s\"\"\"" % nt)
        codigo.append("    results = []")
        codigo.append("    for c in node.get('children', []):")
        codigo.append("        if isinstance(c, dict):")
        codigo.append("            results.append(self.visit(c))")
        codigo.append("        else:")
        codigo.append("            results.append(self._convert_leaf(c))")
        codigo.append("    return {\"%s\": results}" % nt)
        codigo.append("")
    codigo.append("if __name__ == '__main__':")
    codigo.append("    print('Este ficheiro define TreeVisitor. Importa-o em parser_generated.py e usa-o para processar a árvore.')")

    return "\n".join(codigo)


def gerar_codigo_parser_table(gramatica, tabela):
    """Gera um parser table-driven (top-down) como ficheiro Python.

    O ficheiro contém a gramática, a tabela (com chaves já limpas) e um
    runtime `parse(nt)` que usa a tabela para escolher produções.
    """
    import json as _json

    # Garantir que a tabela tem chaves string e producoes como listas
    tabela_serial = {}
    for nt, linha in tabela.items():
        tabela_serial[nt] = {}
        for k, prod in linha.items():
            tabela_serial[nt][k] = prod

    codigo = [
        "#!/usr/bin/env python3",
        "# parser_table_generated.py",
        "# Parser table-driven gerado automaticamente",
        "import sys",
        "import json",
        "",
        f"gramatica = {repr(gramatica)}",
        "tabela = " + _json.dumps(tabela_serial, ensure_ascii=False, indent=4),
        "",
        "def _clean(sym):",
        "    if isinstance(sym, str) and len(sym) >= 2 and sym[0] == \"'\" and sym[-1] == \"'\":",
        "        return sym[1:-1]",
        "    return sym",
        "",
        "def tokenizar_frase_com_eof_local(frase, gramatica):",
        "    import re",
        "    terminais = gramatica.get('terminais', [])",
        "    producoes = gramatica.get('producoes', {})",
        "    literais = gramatica.get('literais', []) if 'literais' in gramatica else []",
        "    partes = []",
        "    if literais:",
        "        pattern = '(' + '|'.join(re.escape(l) for l in sorted(set(literais), key=len, reverse=True)) + ')'",
        "        for pedaco in re.split(pattern, frase):",
        "            if not pedaco:",
        "                continue",
        "            if pedaco in literais:",
        "                partes.append(pedaco)",
        "            else:",
        "                partes.extend(pedaco.split())",
        "    else:",
        "        partes = frase.split()",
        "",
        "    tokens = []",
        "    padroes = []",
        "    for nt, prods in producoes.items():",
        "        for p in prods:",
        "            if len(p) == 1:",
        "                padroes.append(p[0])",
        "",
        "    for part in partes:",
        "        candidatos = []",
        "        if part in terminais:",
        "            candidatos.append(part)",
        "        for pat in padroes:",
        "            try:",
        "                if re.fullmatch(pat, part) and pat not in candidatos:",
        "                    candidatos.append(pat)",
        "            except re.error:",
        "                pass",
        "",
        "        if not candidatos:",
        "            return None, f\"Token '{part}' não reconhecido: não é literal nem casa com padrões lexicais.\"",
        "",
        "        candidatos_normalizados = [_clean(c) for c in candidatos]",
        "        tokens.append({'type': candidatos_normalizados[0], 'value': part, 'candidates': candidatos_normalizados})",
        "",
        "    tokens.append({'type': '$', 'value': '$', 'candidates': ['$']})",
        "    return tokens, None",
        "",
        "class _SimpleLexer:",
        "    def __init__(self, tokens):",
        "        self._tokens = list(tokens)",
        "        self._i = 0",
        "    def token(self):",
        "        if self._i >= len(self._tokens):",
        "            return None",
        "        t = self._tokens[self._i]",
        "        self._i += 1",
        "        return t",
        "",
        "def _resolver_lookahead(prox_simb, nt_atual):",
        "    linha = tabela.get(nt_atual, {})",
        "    candidatos = [prox_simb.get('type')] + prox_simb.get('candidates', [])",
        "    for c in candidatos:",
        "        if c in linha:",
        "            return c",
        "    return prox_simb.get('type')",
        "",
        "def parse_from_table(tokens, gramatica):",
        "    input_tokens = list(tokens)",
        "    if not input_tokens or input_tokens[-1]['type'] != '$':",
        "        input_tokens.append({'type': '$', 'value': '$'})",
        "    prox_simb = input_tokens.pop(0)",
        "",
        "    def parse(nt_atual):",
        "        nonlocal prox_simb",
        "        no = {'name': nt_atual, 'children': []}",
        "        if nt_atual in gramatica['terminais']:",
        "            if nt_atual == prox_simb['type'] or nt_atual in prox_simb.get('candidates', []):",
        "                no['name'] = prox_simb['value']",
        "                if input_tokens:",
        "                    prox_simb = input_tokens.pop(0)",
        "                return no",
        "            return None",
        "",
        "        if nt_atual in gramatica['nao_terminais']:",
        "            tipo = _resolver_lookahead(prox_simb, nt_atual)",
        "            if tipo not in tabela.get(nt_atual, {}):",
        "                return None",
        "            producao = tabela[nt_atual][tipo]",
        "            if producao == ['ε']:",
        "                no['children'].append({'name': 'ε'})",
        "                return no",
        "            for simbolo in producao:",
        "                filho = parse(simbolo)",
        "                if not filho:",
        "                    return None",
        "                no['children'].append(filho)",
        "            return no",
        "        return no",
        "",
        "    raiz = parse(gramatica.get('inicial'))",
        "    if not raiz:",
        "        return None",
        "    if prox_simb['type'] != '$':",
        "        return None",
        "    return raiz",
        "",
        "if __name__ == '__main__':",
        "    import sys, json",
        "    if len(sys.argv) > 1:",
        "        frase = ' '.join(sys.argv[1:])",
        "    else:",
        "        try:",
        "            frase = input('Frase para parser: ')",
        "        except EOFError:",
        "            frase = ''",
        "",
        "    tokens, err = tokenizar_frase_com_eof_local(frase, gramatica)",
        "    if err:",
        "        print('Erro léxico:', err)",
        "        sys.exit(1)",
        "",
        "    raiz = parse_from_table(tokens, gramatica)",
        "    if not raiz:",
        "        print('Parsing falhou ou tokens extra')",
        "        sys.exit(1)",
        "",
        "    # pretty print",
        "    def _pretty_print(node, nivel=0):",
        "        if node is None:",
        "            return",
        "        indent = '  ' * nivel",
        "        children = node.get('children', []) if isinstance(node, dict) else []",
        "        if len(children) == 1 and (not children[0].get('children')):",
        "            print(f\"{indent}{node.get('name')} -> {children[0].get('name')}\")",
        "            return",
        "        print(f\"{indent}{node.get('name')}\")",
        "        for c in children:",
        "            if c.get('children'):",
        "                _pretty_print(c, nivel+1)",
        "            else:",
        "                print('  ' * (nivel+1) + str(c.get('name')))",
        "",
        "    _pretty_print(raiz)",
        "    # Tentar usar visitor se existir",
        "    try:",
        "        from visitor_generated import TreeVisitor",
        "        v = TreeVisitor()",
        "        res = v.visit(raiz)",
        "        try:",
        "            print(json.dumps(res, ensure_ascii=False, indent=2))",
        "        except Exception:",
        "            print(res)",
        "    except Exception:",
        "        pass",
    ]

    return "\n".join(codigo)