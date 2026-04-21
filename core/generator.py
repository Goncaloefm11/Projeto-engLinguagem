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
        "       no_folha = {'name': prox_simb['value']}",  # CRIA O NÓ
        "       prox_simb = lexer.token()",
        "       return no_folha",    #RETORNA O NÓ FOLHA
        "    else:",
        "       parser_error(prox_simb)",
        "       prox_simb = ('erro', '', 0, 0)",
        "       return None",        # Retorna None em caso de erro
        "--------------------------------------------------------"
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
            t_cond = "None" if term == "$" else f"'{term}'"
            
            codigo.append(f"    {condicao} prox_simb and prox_simb['type'] == {t_cond}:")
            if prod == ['ε']:
                codigo.append(f"        print('{nt} -> ε')")
                codigo.append("        no_atual['children'].append({'name': 'ε'})") # Adiciona o epsilon aos filhos
            else:
                for j, simbolo in enumerate(prod): #enumerate para ter id único de cada símbolo
                    if simbolo in gramatica['nao_terminais']:
                        codigo.append(f"        rec_{simbolo}()")
                        codigo.append(f"        no_atual['children'].append(filho_{j})")
                    else:
                        s_limpo = simbolo.replace("'", "")
                        codigo.append(f"        rec_term('{s_limpo}')")
                        codigo.append(f"        no_atual['children'].append(filho_{j})")
                    
                # 2. No FINAL, imprimimos a regra completa numa só linha
                producao_texto = " ".join(prod)
                codigo.append(f"        print('{nt} -> {producao_texto}')")
            
            # No fim de cada ramo (if/elif), retorna o nó construído
            codigo.append("        return no_atual")
        
        codigo.append("    else:")
        codigo.append("        parser_error(prox_simb)")
        codigo.append("        return None\n")

    return "\n".join(codigo)