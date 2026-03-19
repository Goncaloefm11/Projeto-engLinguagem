#le a string da gramatica

def carregar_gramatica_da_string(texto):
    gramatica = {
        'terminais': set(),
        'nao_terminais': set(),
        'producoes': {},
        'inicial': None
    }
    
    # Passo 1: Identificar todos os Não-Terminais primeiro (quem está à esquerda)
    linhas = [l.strip() for l in texto.split('\n') if '->' in l]
    for linha in linhas:
        esq = linha.split('->')[0].strip()
        gramatica['nao_terminais'].add(esq)
        if not gramatica['inicial']:
            gramatica['inicial'] = esq

    # Passo 2: Processar as produções
    for linha in linhas:
        esq, dir = linha.split('->')
        nt = esq.strip()
        
        # Split por '|' e lidar com campos vazios (transformar em ε)
        partes = dir.split('|')
        for p in partes:
            simbolos = p.strip().split()
            if not simbolos: # Se a parte estava vazia (ex: | )
                simbolos = ['ε']
            
            if nt not in gramatica['producoes']:
                gramatica['producoes'][nt] = []
            gramatica['producoes'][nt].append(simbolos)
            
            # Identificar terminais (o que não está na lista de Não-Terminais)
            for s in simbolos:
                if s not in gramatica['nao_terminais'] and s != 'ε':
                    gramatica['terminais'].add(s)

    gramatica['terminais'] = list(gramatica['terminais'] | {'ε'})
    gramatica['nao_terminais'] = list(gramatica['nao_terminais'])
    return gramatica