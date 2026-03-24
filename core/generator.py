# core/generator.py

def gerar_codigo_parser(gramatica, tabela):
    codigo = [
        "import sys",
        "# Parser Gerado Automaticamente - Projeto GP 2026",
        "prox_simb = None",
        "",
        "def parser_error(simb):",
        "    print(f'Erro sintático: token inesperado {simb}')",
        "    sys.exit(1)",
        "",
        "def rec_term(esperado, tokens):",
        "    global prox_simb",
        "    if prox_simb and prox_simb['type'] == esperado:",
        "        if tokens: prox_simb = tokens.pop(0)",
        "        else: prox_simb = None",
        "    else: parser_error(prox_simb)",
        "--------------------------------------------------------"
        ""
    ]

    # Gerar funções para cada Não-Terminal
    for nt, caminhos in tabela.items():
        codigo.append(f"def rec_{nt}(tokens):")
        codigo.append("    global prox_simb")
        
        for i, (term, prod) in enumerate(caminhos.items()):
            condicao = "if" if i == 0 else "elif"
            # O terminal '$' representa o fim da entrada
            t_cond = "None" if term == "$" else f"'{term}'"
            
            codigo.append(f"    {condicao} prox_simb and prox_simb['type'] == {t_cond}:")
            if prod == ['ε']:
                codigo.append(f"        {nt} ->      # Produção vazia")
            else:
                for simbolo in prod:
                    if simbolo in gramatica['nao_terminais']:
                        codigo.append(f"        rec_{simbolo}()")
                    else:
                        codigo.append(f"        rec_term({simbolo})")
                    
                # 2. No FINAL, imprimimos a regra completa numa só linha
                producao_texto = " ".join(prod)
                codigo.append(f"        {nt} -> {producao_texto}")
        
        codigo.append("    else: parser_error(prox_simb)\n")

    return "\n".join(codigo)