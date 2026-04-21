# core/generator.py

def gerar_codigo_parser(gramatica, tabela):
    codigo = [
        "import sys",
        "# Parser Gerado Automaticamente - Projeto GP 2026",
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

    # Gerar funções para cada Não-Terminal
    for nt, caminhos in tabela.items():
        codigo.append(f"def rec_{nt}():")
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
                    if simbolo in gramatica['nao_terminais']:
                        # CORREÇÃO: Capturar o filho e adicionar à árvore
                        codigo.append(f"        filho_{j} = rec_{simbolo}()")
                        codigo.append(f"        if filho_{j}: no_atual['children'].append(filho_{j})")
                    else:
                        # CORREÇÃO: Limpar aspas com segurança e capturar/adicionar o filho
                        if len(simbolo) >= 2 and simbolo[0] == "'" and simbolo[-1] == "'":
                            s_clean = simbolo[1:-1]
                        else:
                            s_clean = simbolo
                        codigo.append(f"        filho_{j} = rec_term({repr(s_clean)})")
                        codigo.append(f"        if filho_{j}: no_atual['children'].append(filho_{j})")
                    
                # 2. No FINAL, (não imprimimos a produção) — apenas construímos a árvore
            
            # CORREÇÃO: Retornar o nó se entrou nesta condição (construção da AST)
            codigo.append("        return no_atual")
        
        # CORREÇÃO: Fallback final caso nenhuma condição se verifique
        codigo.append("    else:")
        codigo.append("        parser_error(prox_simb)")
        codigo.append("        return None\n")

    # --- Runner/tokenizador genérico embutido ---
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
        "    start_fn = globals().get(f\"rec_{gramatica.get('inicial')}\")",
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
        "    except Exception:",
        "        import traceback",
        "        traceback.print_exc()",
        "        sys.exit(1)",
    ]

    return "\n".join(codigo + runner)