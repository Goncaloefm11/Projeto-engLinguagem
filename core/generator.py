# core/generator.py

def gerar_codigo_parser(gramatica, tabela):
    codigo = [
        "import sys",
        "# Parser Gerado Automaticamente - Projeto GP 2026",
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
                codigo.append(f"        print('{nt} -> ε')")
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
                    
                # 2. No FINAL, imprimimos a regra completa numa só linha
                producao_texto = " ".join(prod)
                codigo.append(f"        print('{nt} -> {producao_texto}')")
            
            # CORREÇÃO: Retornar o nó se entrou nesta condição (construção da AST)
            codigo.append("        return no_atual")
        
        # CORREÇÃO: Fallback final caso nenhuma condição se verifique
        codigo.append("    else:")
        codigo.append("        parser_error(prox_simb)")
        codigo.append("        return None\n")

    return "\n".join(codigo)