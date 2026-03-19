#calcula first, follow, tabela e arvore
def calcular_first(gramatica):
    # Inicializa os conjuntos FIRST para cada Não-Terminal 
    first = {nt: set() for nt in gramatica['nao_terminais']}
    
    mudou = True
    while mudou:
        mudou = False
        for nt, producoes in gramatica['producoes'].items():
            for prod in producoes:
                # Caso a produção seja vazia (ε)
                if prod == ['ε']:
                    if 'ε' not in first[nt]:
                        first[nt].add('ε')
                        mudou = True
                    continue

                # Analisa cada símbolo da produção (para anuláveis)
                tudo_anulavel = True
                for simbolo in prod:
                    if simbolo in gramatica['terminais']:
                        if simbolo not in first[nt]:
                            first[nt].add(simbolo)
                            mudou = True
                        tudo_anulavel = False
                        break # Encontrou um terminal 
                    
                    elif simbolo in gramatica['nao_terminais']:
                        # Adiciona tudo do FIRST do símbolo exceto o ε
                        tamanho_antes = len(first[nt])
                        first_do_simbolo = first[simbolo]
                        first[nt].update(first_do_simbolo - {'ε'})
                        
                        if len(first[nt]) > tamanho_antes:
                            mudou = True
                        
                        # Se o símbolo não for anulável, paramos a análise desta produção
                        if 'ε' not in first_do_simbolo:
                            tudo_anulavel = False
                            break
                
                # Se todos os símbolos da produção puderem ser ε, o NT também pode ser
                if tudo_anulavel and 'ε' not in first[nt]:
                    first[nt].add('ε')
                    mudou = True
                        
    return first

def calcular_follow(gramatica, firsts):
    # Inicializa os conjuntos FOLLOW
    follow = {nt: set() for nt in gramatica['nao_terminais']}
    
    # Regra 1: Símbolo inicial recebe o marcador de fim ($)
    simbolo_inicial = gramatica['nao_terminais'][0]
    follow[simbolo_inicial].add('$')
    
    mudou = True
    while mudou:
        mudou = False
        for nt, producoes in gramatica['producoes'].items():
            for prod in producoes:
                # Analisamos cada símbolo na produção
                for i, simbolo in enumerate(prod):
                    if simbolo in gramatica['nao_terminais']:
                        tamanho_antes = len(follow[simbolo])
                        
                        # Espreitar o que vem a seguir (beta)
                        beta = prod[i+1:]
                        
                        if beta:
                            # Regra 2: FOLLOW recebe FIRST do que vem a seguir
                            primeiro_de_beta = obter_first_sequencia(beta, firsts, gramatica['terminais'])
                            follow[simbolo].update(primeiro_de_beta - {'ε'})
                            
                            # Regra 3: Se o que vem a seguir for anulável, recebe FOLLOW do pai
                            if 'ε' in primeiro_de_beta:
                                follow[simbolo].update(follow[nt])
                        else:
                            # Regra 3: Se for o último símbolo, recebe FOLLOW do pai
                            follow[simbolo].update(follow[nt])
                            
                        if len(follow[simbolo]) > tamanho_antes:
                            mudou = True
    return follow

def obter_first_sequencia(sequencia, firsts, terminais):
    res = set()
    for s in sequencia:
        if s in terminais:
            res.add(s)
            return res
        res.update(firsts[s] - {'ε'})
        if 'ε' not in firsts[s]:
            return res
    res.add('ε')
    return res

def gerar_tabela_ll1(gramatica, firsts, follows):
    tabela = {}
    conflitos = []

    for nt in gramatica['nao_terminais']:
        tabela[nt] = {}
        for prod in gramatica['producoes'][nt]:
            # Calculamos o FIRST da sequência da produção atual
            first_da_prod = obter_first_sequencia(prod, firsts, gramatica['terminais'])
            
            # Para cada terminal no FIRST da produção, preenchemos a tabela
            for terminal in first_da_prod - {'ε'}:
                if terminal in tabela[nt]:
                    conflitos.append(f"Conflito FIRST/FIRST em {nt} com terminal '{terminal}'")
                tabela[nt][terminal] = prod
            
            # Se a produção for anulável (tem ε), usamos o FOLLOW
            if 'ε' in first_da_prod:
                for terminal in follows[nt]:
                    if terminal in tabela[nt]:
                        conflitos.append(f"Conflito FIRST/FOLLOW em {nt} com terminal '{terminal}'")
                    tabela[nt][terminal] = prod

    return tabela, conflitos

def gerar_arvore_derivacao(tokens, gramatica, tabela):
    input_tokens = list(tokens)
    # adiciona um $ no fim para terminar a frase
    if not input_tokens or input_tokens[-1]['type'] != '$':
        input_tokens.append({'type': '$', 'value': '$'})
    
    prox_simb = input_tokens.pop(0)

    def parse(nt_atual):
        nonlocal prox_simb
        no = {'name': nt_atual, 'children': []}
        
        # Se for um Terminal esperado
        if nt_atual in gramatica['terminais']:
            if nt_atual == prox_simb['type']:
                no['name'] = nt_atual
                if input_tokens:
                    prox_simb = input_tokens.pop(0)
                return no
            return None # Não casou

        # Se for um Não-Terminal
        if nt_atual in gramatica['nao_terminais']:
            tipo_token = prox_simb['type']
            
            # Se o token não está na tabela para este NT
            if tipo_token not in tabela.get(nt_atual, {}):
                # Se houver uma regra de vazio (ε) na tabela para este NT, usamos
                if 'ε' in tabela.get(nt_atual, {}):
                    no['children'].append({'name': 'ε'})
                    return no
                return None # Erro: não há caminho nem vazio

            producao = tabela[nt_atual][tipo_token]
            
            if producao == ['ε']:
                no['children'].append({'name': 'ε'})
                return no

            # Processa os símbolos da produção
            for simbolo in producao:
                filho = parse(simbolo)
                if filho:
                    no['children'].append(filho)
            
            return no
        
        return no

    simbolo_inicial = gramatica['nao_terminais'][0]
    arvore_final = parse(simbolo_inicial)
    
    return arvore_final