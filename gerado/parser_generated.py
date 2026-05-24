import sys
import json
# Parser Gerado - Projeto 2026
gramatica = {'terminais': ['2', 'ε', 'A', '1'], 'nao_terminais': ['S', 'S_F'], 'producoes': {'S': [['A', 'S_F']], 'S_F': [['1'], ['2']]}, 'inicial': 'S', 'literais': set()}
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

def rec_S():
    global prox_simb
    no_atual = {'name': 'S', 'children': []}
    if prox_simb and prox_simb['type'] == 'A':
        filho_0 = rec_term('A')
        if filho_0: no_atual['children'].append(filho_0)
        filho_1 = rec_S_F()
        if filho_1: no_atual['children'].append(filho_1)
        return no_atual
    else:
        parser_error(prox_simb)
        return None

def rec_S_F():
    global prox_simb
    no_atual = {'name': 'S_F', 'children': []}
    if prox_simb and prox_simb['type'] == '1':
        filho_0 = rec_term('1')
        if filho_0: no_atual['children'].append(filho_0)
        return no_atual
    elif prox_simb and prox_simb['type'] == '2':
        filho_0 = rec_term('2')
        if filho_0: no_atual['children'].append(filho_0)
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
            return None, f"Token '{part}' não reconhecido."

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
    start_fn = globals().get("rec_S")
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
        # Tentar invocar um Visitor externo (visitor_generated.py) se existir
        try:
            from visitor_generated import TreeVisitor
            v = TreeVisitor()
            resultado_visit = v.visit(raiz)
            print('\nVisitor output:')
            try:
                print(json.dumps(resultado_visit, ensure_ascii=False, indent=2))
            except Exception:
                print(resultado_visit)
        except Exception:
            print('\nNota: para usar um Visitor automÃ¡tico, descarregue visitor_generated.py e coloque-o na mesma pasta que este ficheiro.')
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)