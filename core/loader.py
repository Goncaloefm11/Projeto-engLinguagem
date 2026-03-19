"""Lê uma string com a gramática e devolve a representação interna.

O loader aceita produções distribuídas por várias linhas usando o símbolo
'|' no início da linha para indicar uma alternativa da produção anterior.

Exemplo aceito:
  A -> a b | c
  B -> x y
  C -> z
  D -> t u
  E -> v
  F -> g
  G -> h

Também aceita o estilo alternativo com '|' em linhas seguintes:
  A -> a b
      | c

"""

def _preprocess_lines(raw_lines):
    """Retorna uma lista de linhas com as continuações iniciadas por '|' expandidas.

    Cada continuação é convertida numa linha do tipo: NT -> resto
    """
    processed_lines = []
    current_nt = None
    for raw in raw_lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        if '->' in line:
            processed_lines.append(line.strip())
            current_nt = line.split('->', 1)[0].strip()
        else:
            stripped = line.lstrip()
            if stripped.startswith('|') and current_nt:
                resto = stripped[1:].strip()
                combined = f"{current_nt} -> {resto}"
                processed_lines.append(combined)
            else:
                continue

    return processed_lines


def carregar_gramatica_da_string(texto):
    gramatica = {
        'terminais': set(),
        'nao_terminais': set(),
        'producoes': {},
        'inicial': None
    }

    raw_lines = texto.splitlines()
    processed_lines = _preprocess_lines(raw_lines)

    # Passo 1: identificar não-terminais (esquerda das setas)
    for linha in processed_lines:
        esq = linha.split('->', 1)[0].strip()
        gramatica['nao_terminais'].add(esq)
        if gramatica['inicial'] is None:
            gramatica['inicial'] = esq

    # Passo 2: processar producoes
    for linha in processed_lines:
        esq, rhs = linha.split('->', 1)
        nt = esq.strip()

        partes = [part.strip() for part in rhs.split('|')]
        for p in partes:
            simbolos = p.split() if p else []
            if not simbolos:
                simbolos = ['ε']

            gramatica['producoes'].setdefault(nt, []).append(simbolos)

            # identificar terminais (o que não está na lista de Não-Terminais)
            for s in simbolos:
                if s != 'ε' and s not in gramatica['nao_terminais']:
                    gramatica['terminais'].add(s)

    # garantir que ε está nos terminais (usado internamente)
    gramatica['terminais'] = list(gramatica['terminais'] | {'ε'})
    gramatica['nao_terminais'] = list(gramatica['nao_terminais'])
    return gramatica