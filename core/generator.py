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
        "       prox_simb = lexer.token()",
        "    else:",
        "       parser_error(prox_simb)",
        "       prox_simb = ('erro', '', 0, 0)",
        "# --------------------------------------------------------",
        ""
    ]

    # Gerar funções para cada Não-Terminal
    for nt, caminhos in tabela.items():
        codigo.append(f"def rec_{nt}():")
        codigo.append("    global prox_simb")
        
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
            else:
                for simbolo in prod:
                    if simbolo in gramatica['nao_terminais']:
                        codigo.append(f"        rec_{simbolo}()")
                    else:
                        # Se o símbolo terminal for do tipo literal ('x'), limpamos as aspas
                        if len(simbolo) >= 2 and simbolo[0] == "'" and simbolo[-1] == "'":
                            s_clean = simbolo[1:-1]
                        else:
                            s_clean = simbolo
                        codigo.append(f"        rec_term({repr(s_clean)})")
                    
                # 2. No FINAL, imprimimos a regra completa numa só linha
                producao_texto = " ".join(prod)
                codigo.append(f"        print({repr(f'{nt} -> {producao_texto}')})")
        
        codigo.append("    else: parser_error(prox_simb)\n")

    return "\n".join(codigo)