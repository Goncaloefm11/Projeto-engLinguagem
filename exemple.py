import sys
# Parser Gerado Automaticamente - Projeto GP 2026
gramatica = {'terminais': ['[', ',', ']', '[0-9]+', '[^<>]+', 'ε'], 'nao_terminais': ['Cont', 'string', 'int', 'Elem', 'Resto', 'Lista', 'Elems'], 'producoes': {'Lista': [['[', 'Cont']], 'Cont': [[']'], ['Elems', ']']], 'Elems': [['Elem', 'Resto']], 'Resto': [['ε'], [',', 'Elem', 'Resto']], 'Elem': [['int'], ['string']], 'int': [['[0-9]+']], 'string': [['[^<>]+']]}, 'inicial': 'Lista', 'literais': {',', ']', '['}}
prox_simb = None

def parser_error(simb):
    print(f'Erro sintático: token inesperado {simb}')

def rec_term(esperado):
    global prox_simb
    if prox_simb and prox_simb['type'] == esperado:
        no_folha = {'name': prox_simb['value']}  # CRIA O NÓ
        prox_simb = lexer.token()
        return no_folha
    else:
        parser_error(prox_simb)
        prox_simb = ('erro', '', 0, 0)
        return None
# --------------------------------------------------------

def rec_Cont():
    global prox_simb
    no_atual = {'name': 'Cont', 'children': []}
    if prox_simb and prox_simb['type'] == ']':
        filho_0 = rec_term(']')
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    elif prox_simb and prox_simb['type'] == '[0-9]+':
        filho_0 = rec_Elems()
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_term(']')
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    elif prox_simb and prox_simb['type'] == '[^<>]+':
        filho_0 = rec_Elems()
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_term(']')
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_string():
    global prox_simb
    no_atual = {'name': 'string', 'children': []}
    if prox_simb and prox_simb['type'] == '[^<>]+':
        filho_0 = rec_term('[^<>]+')
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_int():
    global prox_simb
    no_atual = {'name': 'int', 'children': []}
    if prox_simb and prox_simb['type'] == '[0-9]+':
        filho_0 = rec_term('[0-9]+')
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_Elem():
    global prox_simb
    no_atual = {'name': 'Elem', 'children': []}
    if prox_simb and prox_simb['type'] == '[0-9]+':
        filho_0 = rec_int()
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    elif prox_simb and prox_simb['type'] == '[^<>]+':
        filho_0 = rec_string()
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_Resto():
    global prox_simb
    no_atual = {'name': 'Resto', 'children': []}
    if prox_simb and prox_simb['type'] == ']':
        no_atual['children'].append({'name': 'ε'})
        return no_atual
    elif prox_simb and prox_simb['type'] == ',':
        filho_0 = rec_term(',')
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_Elem()
        if filho_1: no_atual['children'].append(filho_1)
        filho_2 = rec_Resto()
        if filho_2: no_atual['children'].append(filho_2)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_Lista():
    global prox_simb
    no_atual = {'name': 'Lista', 'children': []}
    if prox_simb and prox_simb['type'] == '[':
        filho_0 = rec_term('[')
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_Cont()
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_Elems():
    global prox_simb
    no_atual = {'name': 'Elems', 'children': []}
    if prox_simb and prox_simb['type'] == '[0-9]+':
        filho_0 = rec_Elem()
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_Resto()
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    elif prox_simb and prox_simb['type'] == '[^<>]+':
        filho_0 = rec_Elem()
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_Resto()
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    else:
        parser_error(prox_simb)
        return None


def _clean(sym):
    if isinstance(sym, str) and len(sym) >= 2 and sym[0] == "'" and sym[-1] == "'":
        return sym[1:-1]
    return sym

def tokenizar_frase_com_eof_local(frase, gramatica):
    import re
    terminais = gramatica.get('terminais', [])
    producoes = gramatica.get('producoes', {})
    literais = gramatica.get('literais', []) if 'literais' in gramatica else []
    partes = []
    if literais:
        pattern = '(' + '|'.join(re.escape(l) for l in sorted(set(literais), key=len, reverse=True)) + ')'
        for pedaco in re.split(pattern, frase):
            if not pedaco:
                continue
            if pedaco in literais:
                partes.append(pedaco)
            else:
                partes.extend(pedaco.split())
    else:
        partes = frase.split()

    tokens = []
    padroes = []
    for nt, prods in producoes.items():
        for p in prods:
            if len(p) == 1:
                padroes.append(p[0])

    for part in partes:
        candidatos = []
        if part in terminais:
            candidatos.append(part)
        for pat in padroes:
            try:
                if re.fullmatch(pat, part) and pat not in candidatos:
                    candidatos.append(pat)
            except re.error:
                pass

        if not candidatos:
            return None, f"Token '{part}' não reconhecido: não é literal nem casa com padrões lexicais."

        candidatos_normalizados = [_clean(c) for c in candidatos]
        tokens.append({'type': candidatos_normalizados[0], 'value': part, 'candidates': candidatos_normalizados})

    tokens.append({'type': '$', 'value': '$', 'candidates': ['$']})
    return tokens, None

class _SimpleLexer:
    def __init__(self, tokens):
        self._tokens = list(tokens)
        self._i = 0
    def token(self):
        if self._i >= len(self._tokens):
            return None
        t = self._tokens[self._i]
        self._i += 1
        return t

if __name__ == '__main__':
    import sys, json
    if len(sys.argv) > 1:
        frase = ' '.join(sys.argv[1:])
    else:
        try:
            frase = input('Frase para parser: ')
        except EOFError:
            frase = ''

    tokens, err = tokenizar_frase_com_eof_local(frase, gramatica)
    if err:
        print('Erro léxico:', err)
        sys.exit(1)

    lexer = _SimpleLexer(tokens)
    prox_simb = lexer.token()
    start_fn = globals().get(f"rec_{gramatica.get('inicial')}")
    if not start_fn:
        print('Função inicial rec_' + str(gramatica.get('inicial')) + ' não encontrada.')
        sys.exit(1)
    try:
        raiz = start_fn()
        print('\nArvore gerada pela frase:')
        def _pretty_print(node, nivel=0):
            if node is None:
                return
            indent = '  ' * nivel
            # Se o nó tem exatamente um filho que é folha, imprimimos em linha: NT -> leaf
            children = node.get('children', []) if isinstance(node, dict) else []
            if len(children) == 1 and (not children[0].get('children')):
                print(f"{indent}{node.get('name')} -> {children[0].get('name')}")
                return
            # Caso contrário, imprimimos o nome e descemos aos filhos
            print(f"{indent}{node.get('name')}")
            for c in children:
                if c.get('children'):
                    _pretty_print(c, nivel+1)
                else:
                    print('  ' * (nivel+1) + str(c.get('name')))
        _pretty_print(raiz)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)