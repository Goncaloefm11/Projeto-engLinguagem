"""core/ontology.py

Gerador simples de ontologia OWL/RDF (Turtle) para uma gramática.

Implementação leve: tenta usar rdflib se disponível; caso contrário,
serializa Turtle manualmente (suficiente para inspeção e download).
"""
from typing import Dict, List, Set, Optional
import os
import re

EX_NS = "http://example.org/grammar#"

# Mapa de caracteres especiais para nomes descritivos
SPECIAL_CHARS_MAP = {
    '(': 'bracket_open',
    ')': 'bracket_close',
    '[': 'square_open',
    ']': 'square_close',
    '{': 'brace_open',
    '}': 'brace_close',
    '<': 'angle_open',
    '>': 'angle_close',
    '|': 'pipe',
    ';': 'semicolon',
    ':': 'colon',
    ',': 'comma',
    '.': 'dot',
    '+': 'plus',
    '-': 'minus',
    '*': 'star',
    '/': 'slash',
    '\\': 'backslash',
    '=': 'equals',
    '?': 'question',
    '!': 'exclaim',
    '@': 'at',
    '#': 'hash',
    '$': 'dollar',
    '%': 'percent',
    '^': 'caret',
    '&': 'ampersand',
    '~': 'tilde',
    '`': 'backtick',
    "'": 'quote',
    '"': 'dquote',
    ' ': 'space',
    '\t': 'tab',
    '\n': 'newline',
    'ε': 'epsilon',
}



def _frag(s: str) -> str:
    r"""Criar fragmento legível e único para o Turtle.

    Estratégia:
    1. Preserva prefixos (T_, NT_, P_, Conflict_)
    2. Remove aspas externas
    3. Mapeia caracteres especiais para nomes descritivos
    4. Para caracteres não mapeados, usa código hexadecimal (ex: \xHH)
    5. Garante que cada símbolo tem um URI único

    Exemplos:
    - T_'(' -> ex:T_bracket_open
    - T_'+' -> ex:T_plus
    - T_sym -> ex:T_sym
    - T_'#' -> ex:T_hash
    - T_'Ω' -> ex:T_x03A9  (código Unicode)
    """
    if s is None:
        s = 'unk'
    s = str(s)
    
    # Extrair prefixo se existir
    prefix = ''
    core = s
    if s.startswith('T_'):
        prefix = 'T_'
        core = s[2:]
    elif s.startswith('NT_'):
        prefix = 'NT_'
        core = s[3:]
    elif s.startswith('P_'):
        prefix = 'P_'
        core = s[2:]
    elif s.startswith('Conflict_'):
        prefix = 'Conflict_'
        core = s[len('Conflict_'):]

    # Remove aspas externas se existirem
    if len(core) >= 2:
        if (core[0] == '"' and core[-1] == '"') or (core[0] == "'" and core[-1] == "'"):
            core = core[1:-1]

    # Processar cada carácter
    result = []
    for char in core:
        if char in SPECIAL_CHARS_MAP:
            # Usar nome descritivo
            result.append(SPECIAL_CHARS_MAP[char])
        elif char.isalnum() or char == '_':
            # Caractere seguro - adicionar diretamente
            result.append(char)
        else:
            # Usar código hexadecimal (Unicode) para caracteres especiais
            hex_code = f"x{ord(char):04X}".lower()
            result.append(hex_code)
    
    # Juntar componentes com _ apenas entre itens especiais
    safe = ''.join(result)
    
    # Limpar múltiplos underscores
    safe = re.sub('_+', '_', safe).strip('_')
    if not safe:
        safe = 'sym'
    
    return f"{prefix}{safe}"



def _try_rdflib_available():
    try:
        import rdflib  
        return True
    except Exception:
        return False


def gerar_ontologia(gramatica: Dict, firsts: Optional[Dict]=None, follows: Optional[Dict]=None, conflitos: Optional[List]=None, out_path: str = 'gerado/grammar.ttl'):
    """Gera um ficheiro Turtle representando a gramática.

    - gramatica: dicionário com chaves 'terminais','nao_terminais','producoes','inicial'
    - firsts/follows: opcionais (serão anotados como literais nos NT)
    - conflitos: lista de strings (mensagens) — cada uma será representada como uma instância Conflict
    - out_path: caminho de saída (cria pasta se necessário)
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    use_rdflib = _try_rdflib_available()
    if use_rdflib:
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF, RDFS, OWL

        g = Graph()
        EX = Namespace(EX_NS)
        g.bind('ex', EX)
        g.bind('rdfs', RDFS)
        g.bind('owl', OWL)

        # Classes
        g.add((EX.Grammar, RDF.type, OWL.Class))
        g.add((EX.NonTerminal, RDF.type, OWL.Class))
        g.add((EX.Terminal, RDF.type, OWL.Class))
        g.add((EX.Production, RDF.type, OWL.Class))
        g.add((EX.Conflict, RDF.type, OWL.Class))

        # Gramática
        gram_uri = URIRef(EX + _frag(gramatica.get('inicial', 'G')))
        g.add((gram_uri, RDF.type, EX.Grammar))
        g.add((gram_uri, RDFS.label, Literal('Grammar')))

        nt_map = {}
        t_map = {}

        # Terminais
        for t in gramatica.get('terminais', []):
            u = URIRef(EX + _frag('T_'+str(t)))
            t_map[t] = u
            g.add((u, RDF.type, EX.Terminal))
            g.add((u, RDFS.label, Literal(str(t))))

        # Nao Terminals (com first/follow sets se disponíveis)
        for nt in gramatica.get('nao_terminais', []):
            u = URIRef(EX + _frag('NT_'+str(nt)))
            nt_map[nt] = u
            g.add((u, RDF.type, EX.NonTerminal))
            g.add((u, RDFS.label, Literal(str(nt))))
            g.add((gram_uri, EX.hasNonTerminal, u))
            if firsts and nt in firsts:
                g.add((u, EX.firstSet, Literal(','.join(sorted(firsts[nt])))))
            if follows and nt in follows:
                g.add((u, EX.followSet, Literal(','.join(sorted(follows[nt])))))

        # Producoes
        prod_map = {}
        for nt, prods in gramatica.get('producoes', {}).items():
            for idx, prod in enumerate(prods):
                pid = f"{nt}_prod_{idx}"
                p_uri = URIRef(EX + _frag(pid))
                prod_map[(nt, idx)] = p_uri
                g.add((p_uri, RDF.type, EX.Production))
                g.add((p_uri, EX.lhs, nt_map[nt]))
                g.add((gram_uri, EX.hasProduction, p_uri))
                g.add((p_uri, RDFS.label, Literal(' '.join(prod))))
                # simbolos
                for pos, sym in enumerate(prod):
                    if sym in gramatica.get('nao_terminais', []):
                        g.add((p_uri, EX.hasRHSNonTerminal, nt_map[sym]))
                    else:
                        # clean literal if quoted
                        s_clean = sym[1:-1] if (isinstance(sym, str) and len(sym) >= 2 and sym[0]=="'" and sym[-1]=="'") else sym
                        if s_clean not in t_map:
                            t_uri = URIRef(EX + _frag('T_'+str(s_clean)))
                            t_map[s_clean] = t_uri
                            g.add((t_uri, RDF.type, EX.Terminal))
                            g.add((t_uri, RDFS.label, Literal(str(s_clean))))
                        g.add((p_uri, EX.hasRHSTerminal, t_map[s_clean]))

        # Conflitos
        if conflitos:
            for i, c in enumerate(conflitos):
                c_uri = URIRef(EX + _frag('Conflict_'+str(i)))
                g.add((c_uri, RDF.type, EX.Conflict))
                g.add((c_uri, RDFS.comment, Literal(str(c))))
                # best-effort: link conflict to any production whose text appears in message
                for (nt, idx), p_uri in prod_map.items():
                    lbl = str(g.value(p_uri, RDFS.label))
                    if lbl and lbl in c:
                        g.add((p_uri, EX.inConflict, c_uri))

        g.serialize(destination=out_path, format='turtle')
        return out_path

    # Fallback: gerar Turtle manualmente
    lines = []
    lines.append("@prefix ex: <{}> .".format(EX_NS))
    lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    lines.append("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
    lines.append("")
    lines.append("ex:Grammar a owl:Class .")
    lines.append("ex:NonTerminal a owl:Class .")
    lines.append("ex:Terminal a owl:Class .")
    lines.append("ex:Production a owl:Class .")
    lines.append("ex:Conflict a owl:Class .")
    lines.append("")

    gram_name = _frag(gramatica.get('inicial', 'G'))
    lines.append(f"ex:{gram_name} a ex:Grammar ; rdfs:label \"Grammar\" .")

    nt_map = {}
    t_map = {}
    prod_map = {}

    for t in gramatica.get('terminais', []):
        frag = _frag('T_'+str(t))
        t_map[t] = frag
        lines.append(f"ex:{frag} a ex:Terminal ; rdfs:label \"{t}\" .")

    for nt in gramatica.get('nao_terminais', []):
        frag = _frag('NT_'+str(nt))
        nt_map[nt] = frag
        lines.append(f"ex:{frag} a ex:NonTerminal ; rdfs:label \"{nt}\" .")
        lines.append(f"ex:{gram_name} ex:hasNonTerminal ex:{frag} .")
        if firsts and nt in firsts:
            lines.append(f"ex:{frag} ex:firstSet \"{','.join(sorted(firsts[nt]))}\" .")
        if follows and nt in follows:
            lines.append(f"ex:{frag} ex:followSet \"{','.join(sorted(follows[nt]))}\" .")

    for nt, prods in gramatica.get('producoes', {}).items():
        for idx, prod in enumerate(prods):
            pid = f"{nt}_prod_{idx}"
            frag = _frag('P_'+pid)
            prod_map[(nt, idx)] = frag
            lines.append(f"ex:{frag} a ex:Production ; ex:lhs ex:{nt_map[nt]} ; rdfs:label \"{' '.join(prod)}\" .")
            lines.append(f"ex:{gram_name} ex:hasProduction ex:{frag} .")
            for pos, sym in enumerate(prod):
                if sym in gramatica.get('nao_terminais', []):
                    lines.append(f"ex:{frag} ex:hasRHSNonTerminal ex:{nt_map[sym]} .")
                else:
                    s_clean = sym[1:-1] if (isinstance(sym, str) and len(sym) >= 2 and sym[0]=="'" and sym[-1]=="'") else sym
                    if s_clean not in t_map:
                        tfrag = _frag('T_'+str(s_clean))
                        t_map[s_clean] = tfrag
                        lines.append(f"ex:{tfrag} a ex:Terminal ; rdfs:label \"{s_clean}\" .")
                    lines.append(f"ex:{frag} ex:hasRHSTerminal ex:{t_map[s_clean]} .")

    if conflitos:
        for i, c in enumerate(conflitos):
            cfrag = _frag('Conflict_'+str(i))
            lines.append(f"ex:{cfrag} a ex:Conflict ; rdfs:comment \"{str(c)}\" .")
        
            for (nt, idx), pfrag in prod_map.items():
                label = ' '.join(gramatica.get('producoes', {}).get(nt, [])[idx])
                if label and label in c:
                    lines.append(f"ex:{pfrag} ex:inConflict ex:{cfrag} .")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return out_path
