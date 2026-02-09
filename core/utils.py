def carregar_gramatica(caminho):
    producoes = {}
    with open(caminho, 'r', encoding='utf-8') as f:
        for linha in f:
            if "->" not in linha: continue
            
            cabeca, corpo = linha.split("->")
            nt = cabeca.strip()
            # Divide as alternativas por "|"
            alternativas = [alt.strip().split() for alt in corpo.split("|")]
            
            if nt not in producoes:
                producoes[nt] = []
            producoes[nt].extend(alternativas)
            
    return producoes
