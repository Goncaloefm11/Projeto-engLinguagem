#core/refactor.py
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
    inicial = gramatica.get('inicial')
    
    # 1. Força o símbolo inicial a ser o primeiro da lista
    ordem = []
    if inicial:
        ordem.append(inicial)

    # 2. Adiciona os restantes Não-Terminais
    for nt in gramatica.get('nao_terminais', []):
        if nt not in ordem:
            ordem.append(nt)

    # 3. Acrescenta os gerados dinamicamente (fatorização/recursividade)
    for nt in gramatica['producoes'].keys():
        if nt not in ordem:
            ordem.append(nt)

    for nt in ordem:
        prods = gramatica['producoes'].get(nt, [])
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
            while nt_novo in novos_nt: nt_novo += "P"
            novos_nt.add(nt_novo)
            
            # A -> beta A_P (Se beta for ε, fica apenas A_P)
            novas_prods_base = []
            for p in nao_diretas:
                if p == ['ε']:
                    novas_prods_base.append([nt_novo])
                else:
                    novas_prods_base.append(p + [nt_novo])
            
            novas_producoes[nt] = novas_prods_base if nao_diretas else [[nt_novo]]
            
            # A_P -> alpha A_P | ε
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
    
    # Função auxiliar para obter o primeiro terminal real de uma produção
    def obter_primeiro_token(prod):
        simbolo = prod[0]
        if simbolo in gramatica['terminais'] or simbolo == 'ε':
            return simbolo
        # Se for Não-Terminal, tentamos ver o primeiro símbolo da sua primeira produção
        # Nota: Isto é uma simplificação. O ideal seria usar o conjunto FIRST.
        sub_prods = gramatica['producoes'].get(simbolo, [])
        if sub_prods and len(sub_prods[0]) > 0:
            return obter_primeiro_token(sub_prods[0])
        return simbolo

    for nt in list(novas_producoes.keys()):
        prods = novas_producoes[nt]
        if len(prods) < 2: continue
        
        prefixos = {}
        for p in prods:
            token_decisivo = obter_primeiro_token(p)
            prefixos.setdefault(token_decisivo, []).append(p)
            
        for token, lista_prods in prefixos.items():
            if len(lista_prods) > 1:
                modificado = True
                nt_novo = f"{nt}_F"
                while nt_novo in novos_nt: nt_novo += "F"
                novos_nt.add(nt_novo)
                
                # Manter produções que não conflituam
                restantes = [p for p in prods if obter_primeiro_token(p) != token]
                
                # Encontrar o prefixo comum real (neste caso simplificado, o primeiro símbolo)
                prefixo_comum = lista_prods[0][0] 
                novas_producoes[nt] = restantes + [[prefixo_comum, nt_novo]]
                
                # Criar as derivações para o novo NT fatorizado
                novas_producoes[nt_novo] = [p[1:] if len(p) > 1 else ['ε'] for p in lista_prods]
                
    gramatica['nao_terminais'] = list(novos_nt)
    gramatica['producoes'] = novas_producoes
    return gramatica, modificado