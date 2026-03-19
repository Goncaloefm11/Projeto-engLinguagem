from core.parser_LL1 import gerar_tabela_ll1, calcular_first, calcular_follow
import os

def propor_correcoes(gramatica_original):
    # Fazemos uma cópia profunda para não estragar a original
    import copy
    g_nova = copy.deepcopy(gramatica_original)
    
    # Aplicamos as transformações
    g_nova, mod_rec = remover_recursividade_esquerda(g_nova)
    g_nova, mod_fat = fatorizar_esquerda(g_nova)
    
    if not mod_rec and not mod_fat:
        return None # Nada a sugerir

    # Convertemos para texto para o utilizador ler
    texto_sugerido = gramatica_para_texto(g_nova)
    
    return {
        'texto_novo': texto_sugerido,
        'alteracoes': [
            "Remover Recursividade à Esquerda" if mod_rec else None,
            "Fatorização de Prefixos Comuns" if mod_fat else None
        ]
    }

def gramatica_para_texto(gramatica):
    linhas = []
    # Procurar manter a ordem original dos não-terminais quando possível.
    # A estrutura `nao_terminais` costuma guardar a ordem desejada (símbolo inicial primeiro).
    ordem = list(gramatica.get('nao_terminais', []))

    # Acrescentar quaisquer não-terminais que estejam nas producoes mas não em 'nao_terminais'
    for nt in gramatica['producoes'].keys():
        if nt not in ordem:
            ordem.append(nt)

    for nt in ordem:
        prods = gramatica['producoes'].get(nt, [])
        # Junta as produções com o símbolo pipe |
        # Ex: S -> a B | c
        prods_texto = [" ".join(p) for p in prods]
        linhas.append(f"{nt} -> {' | '.join(prods_texto)}")

    return "\n".join(linhas)

def resolver_conflitos(gramatica):
    log_correcoes = []
    
    # 1. Tenta remover recursividade à esquerda
    gramatica, modificado = remover_recursividade_esquerda(gramatica)
    if modificado: log_correcoes.append("Recursividade à esquerda removida.")

    # 2. Tenta fatorizar prefixos comuns
    gramatica, modificado = fatorizar_esquerda(gramatica)
    if modificado: log_correcoes.append("Fatorização à esquerda aplicada.")

    # 3. Verificação final de LL(1)
    # Calcula FIRST e FOLLOW antes de gerar a tabela
    f = calcular_first(gramatica)
    fol = calcular_follow(gramatica, f)
    tabela, conflitos = gerar_tabela_ll1(gramatica, f, fol)
    
    if conflitos:
        # Se ainda há conflitos após as correções, é ambiguidade pura
        return gramatica, "Ambiguidade detetada: Não é possível resolver com LL(1).", log_correcoes
    
    return gramatica, "Sucesso: Gramática otimizada para LL(1).", log_correcoes

def remover_recursividade_esquerda(gramatica):
    modificado = False
    novas_producoes = {}
    novos_nt = set(gramatica['nao_terminais'])
    
    for nt in gramatica['nao_terminais']:
        producoes = gramatica['producoes'].get(nt, [])
        diretas = [p for p in producoes if p[0] == nt]
        nao_diretas = [p for p in producoes if p[0] != nt]
        
        if diretas:
            modificado = True
            nt_novo = f"{nt}_P"
            novos_nt.add(nt_novo)
            
            # A -> beta A_P
            # Se não houver betas, usamos apenas o novo NT (embora a gramática seria inválida)
            novas_producoes[nt] = [p + [nt_novo] for p in nao_diretas] if nao_diretas else [[nt_novo]]
            
            # A_P -> alpha A_P | epsilon
            novas_producoes[nt_novo] = [p[1:] + [nt_novo] for p in diretas] + [['ε']]
        else:
            novas_producoes[nt] = producoes
            
    gramatica['producoes'] = novas_producoes
    gramatica['nao_terminais'] = list(novos_nt)
    return gramatica, modificado

def fatorizar_esquerda(gramatica):
    modificado = False
    novas_producoes = gramatica['producoes'].copy()
    novos_nt = set(gramatica['nao_terminais'])
    
    for nt in list(novas_producoes.keys()):
        prods = novas_producoes[nt]
        if len(prods) < 2: continue
        
        # Agrupar por primeiro símbolo
        prefixos = {}
        for p in prods:
            primeiro = p[0]
            if primeiro not in prefixos: prefixos[primeiro] = []
            prefixos[primeiro].append(p)
            
        for simb, lista_prods in prefixos.items():
            if len(lista_prods) > 1: # Encontrou prefixo comum
                modificado = True
                nt_novo = f"{nt}_F"
                while nt_novo in novos_nt: nt_novo += "F" # Evitar colisões de nomes
                
                novos_nt.add(nt_novo)
                
                # Substituir as produções originais que tinham o prefixo
                novas_producoes[nt] = [p for p in prods if p[0] != simb]
                novas_producoes[nt].append([simb, nt_novo])
                
                # Criar as novas produções para o NT fatorizado
                # Se a produção era apenas o símbolo, sobra o epsilon
                novas_producoes[nt_novo] = [p[1:] if len(p) > 1 else ['ε'] for p in lista_prods]
                
    gramatica['producoes'] = novas_producoes
    gramatica['nao_terminais'] = list(novos_nt)
    return gramatica, modificado