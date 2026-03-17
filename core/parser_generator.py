"""
Grammar Playground - Gerador de Parsers
Gera parsers descendentes recursivos e table-driven
"""

from typing import List, Dict, Set, Optional
from .grammar import Grammar, Symbol, Production, EPSILON, END_MARKER
from .ll1_analyzer import LL1Analyzer, LL1Table


class RecursiveDescentGenerator:
    """Gera um parser descendente recursivo a partir de uma gramática LL(1)"""
    
    def __init__(self, grammar: Grammar, analyzer: LL1Analyzer):
        self.grammar = grammar
        self.analyzer = analyzer
        if not analyzer.ll1_table:
            analyzer.analyze()
    
    def generate(self, language: str = "python") -> str:
        """Gera código do parser em Python"""
        if language.lower() == "python":
            return self._generate_python()
        else:
            raise ValueError(f"Unsupported language: {language} (only Python is supported)")
    
    def _generate_python(self) -> str:
        """Gera um parser descendente recursivo em Python.
        
        O resultado usa:
        - variáveis globais: tokens (lista), pos (inteiro)
        - funções auxiliares: match(), lookahead(), error()
        - funções de parsing: parse_Symbol() devolve tuplos aninhados
        - sem classes nem OOP complexa
        """
        lines = [
            '"""',
            'Parser Descendente Recursivo',
            '"""',
            '',
            '# Estado global',
            'tokens = []  # Lista de tokens a analisar',
            'pos = 0      # Posição atual na lista de tokens',
            '',
            '',
            'class ParseError(Exception):',
            '    """Exceção lançada quando o parsing falha"""',
            '    pass',
            '',
            '',
            'def error(expected: str) -> None:',
            '    """Lança um erro de parsing com uma mensagem útil"""',
            '    global pos, tokens',
            '    current = tokens[pos] if pos < len(tokens) else "$"',
            f'    raise ParseError(f"Expected {{expected}} but got {{current}} at position {{pos}}")',
            '',
            '',
            'def lookahead() -> str:',
            '    """Devolve o token atual sem o consumir"""',
            '    global tokens, pos',
            '    if pos < len(tokens):',
            '        return tokens[pos]',
            '    return "$"  # Marcador de fim de input',
            '',
            '',
            'def match(expected: str) -> str:',
            '    """Confirma e consome um token terminal"""',
            '    global pos, tokens',
            '    if pos < len(tokens) and tokens[pos] == expected:',
            '        token = tokens[pos]',
            '        pos += 1',
            '        return token',
            '    error(expected)',
            '',
        ]
        
        # Gerar uma função de parsing para cada não-terminal
        for nt in sorted(self.grammar.non_terminals, key=lambda x: str(x)):
            lines.extend(self._generate_nt_method_python(nt))
            lines.append('')
        
        # Adicionar a função principal de parsing
        start_name = self._safe_name(str(self.grammar.start_symbol))
        lines.extend([
            f'def parse(input_tokens: list):',
            f'    """Faz o parsing dos tokens a partir de {self.grammar.start_symbol}"""',
            f'    global tokens, pos',
            f'    tokens = input_tokens',
            f'    pos = 0',
            f'    tree = {start_name}()',
            f'    if pos < len(tokens):',
            f'        error("end of input")',
            f'    return tree',
            '',
        ])
        
        return '\n'.join(lines)
    
    def _generate_nt_method_python(self, nt: Symbol) -> List[str]:
            """Gera uma função de parsing simples para um não-terminal.
    
            Devolve tuplos aninhados que representam a árvore de parsing:
                parse_Expr() -> ('Expr', parse_Term(), parse_Expr_Prime())
    
            Sem classes nem manipulação complexa de estado.
            """
            safe_name = self._safe_name(str(nt))
            productions = self.grammar.get_productions_for(nt)
            
            lines = [
                f'def {safe_name}():',
                f'    """Faz o parsing do não-terminal {nt}"""',
                f'    la = lookahead()',
                f'    children = []',
                f'',
            ]
            
            # Construir os casos com base em FIRST/FOLLOW
            cases = []
            for prod in productions:
                first_set = self.analyzer.first_of_production(prod)
                terminals = [str(t) for t in first_set if t != EPSILON]
                
                is_nullable = EPSILON in first_set
                if is_nullable:
                    follow_terminals = [str(t) for t in self.analyzer.follow(nt)]
                    cases.append((follow_terminals, prod, True))
                else:
                    cases.append((terminals, prod, False))
            
            # Gerar cadeia if-elif para decidir pelo lookahead
            is_first = True
            for terminals, prod, is_nullable in cases:
                term_list = ", ".join(f'"{t}"' for t in terminals)
                condition = f"la in [{term_list}]" if terminals else "True"
                
                if is_first:
                    lines.append(f"    if {condition}:")
                    is_first = False
                else:
                    lines.append(f"    elif {condition}:")
                
                # Gerar o código desta produção
                lines.append(f"        # {prod}")
                
                if prod.is_epsilon_production():
                    # Produção epsilon: devolve o não-terminal sem filhos
                    lines.append(f"        pass")
                else:
                    # Construir a lista de filhos para produções não-epsilon
                    for symbol in prod.body:
                        if symbol.is_epsilon():
                            continue  # Epsilon não gera nenhum nó
                        elif symbol.is_terminal():
                            lines.append(f"        children.append(match('{symbol}'))  # Terminal: {symbol}")
                        else:
                            # Não-terminal: chamada recursiva
                            child_name = self._safe_name(str(symbol))
                            lines.append(f"        children.append({child_name}())  # Não-terminal: {symbol}")
            
            # Adicionar caso de erro, se necessário
            all_terminals = set()
            for terminals, _, _ in cases:
                all_terminals.update(terminals)
            
            if all_terminals:
                expected = " or ".join(sorted(all_terminals))
                if not is_first:
                    lines.append(f"    else:")
                    lines.append(f"        error('{expected}')")
            
            # Devolver a árvore de parsing como tuplo aninhado
            lines.append(f"    return (\"{nt}\", *children)")
            
            return lines
    

    def _safe_name(self, name: str) -> str:
        """Converte o nome de um símbolo num identificador Python válido"""
        result = name.replace("'", "_prime").replace("-", "_")
        result = ''.join(c if c.isalnum() or c == '_' else '_' for c in result)
        return result.lower()



class TableDrivenGenerator:
    """Gera um parser LL(1) table-driven"""
    
    def __init__(self, grammar: Grammar, analyzer: LL1Analyzer):
        self.grammar = grammar
        self.analyzer = analyzer
        if not analyzer.ll1_table:
            analyzer.analyze()
    
    def generate(self, language: str = "python") -> str:
        """Gera código do parser table-driven"""
        if language.lower() == "python":
            return self._generate_python()
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_python(self) -> str:
        """Gera um parser table-driven"""
        # Construir os dados da tabela
        table_entries = []
        for (nt, terminal), productions in self.analyzer.ll1_table.table.items():
            if productions:
                prod = productions[0]
                body = [str(s) for s in prod.body]
                table_entries.append(f'    ("{nt}", "{terminal}"): {body},')
        
        # Obter todos os terminais e não-terminais
        terminals = sorted([str(t) for t in self.grammar.terminals])
        non_terminals = sorted([str(nt) for nt in self.grammar.non_terminals])
        
        code = f'''"""
    Parser LL(1) Table-Driven
"""

from typing import List, Optional, Tuple, Dict


class ParseError(Exception):
    """Exceção lançada quando o parsing falha"""
    pass


class Token:
    """Representa um token vindo do analisador lexical"""
    def __init__(self, type: str, value: str, pos: int = 0):
        self.type = type
        self.value = value
        self.pos = pos
    
    def __repr__(self):
        return f"Token({{self.type}}, {{self.value!r}})"


class ParseTreeNode:
    """Nó na árvore de parsing"""
    def __init__(self, symbol: str, children: List["ParseTreeNode"] = None, token: Token = None):
        self.symbol = symbol
        self.children = children or []
        self.token = token
    
    def is_terminal(self) -> bool:
        return self.token is not None
    
    def add_child(self, child: "ParseTreeNode"):
        self.children.append(child)


# Informação da gramática
TERMINALS = {terminals}
NON_TERMINALS = {non_terminals}
START_SYMBOL = "{self.grammar.start_symbol}"

# Tabela de Parsing LL(1)
# Chave: (não-terminal, terminal) -> corpo da produção como lista de símbolos
PARSE_TABLE: Dict[Tuple[str, str], List[str]] = {{
{chr(10).join(table_entries)}
}}


class TableDrivenParser:
    """Parser LL(1) table-driven"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token: Optional[Token] = tokens[0] if tokens else None
    
    def lookahead(self) -> str:
        """Devolve o tipo do token atual"""
        if self.current_token:
            return self.current_token.type
        return "$"
    
    def advance(self) -> Token:
        """Avança para o token seguinte"""
        token = self.current_token
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None
        return token
    
    def parse(self) -> ParseTreeNode:
        """Faz o parsing do input usando a tabela LL(1)"""
        # A stack contém pares (símbolo, nó_pai)
        root = ParseTreeNode(START_SYMBOL)
        stack: List[Tuple[str, ParseTreeNode]] = [("$", None), (START_SYMBOL, root)]
        
        while stack:
            top_symbol, parent = stack.pop()
            la = self.lookahead()
            
            if top_symbol == "$":
                if la == "$":
                    break
                else:
                    raise ParseError(f"Expected end of input but got {{la}}")
            
            if top_symbol == "ε":
                # Epsilon - não faz nada
                continue
            
            if top_symbol in TERMINALS:
                # Terminal - tem de coincidir
                if top_symbol == la:
                    token = self.advance()
                    if parent:
                        parent.children.append(ParseTreeNode(top_symbol, token=token))
                else:
                    raise ParseError(f"Expected {{top_symbol}} but got {{la}}")
            
            elif top_symbol in NON_TERMINALS:
                # Não-terminal - consultar a tabela
                key = (top_symbol, la)
                if key not in PARSE_TABLE:
                    raise ParseError(f"No production for {{top_symbol}} with lookahead {{la}}")
                
                production_body = PARSE_TABLE[key]
                
                # Criar um nó para este não-terminal
                node = ParseTreeNode(top_symbol)
                if parent:
                    parent.children.append(node)
                
                # Colocar o corpo da produção em ordem inversa na stack
                for symbol in reversed(production_body):
                    stack.append((symbol, node))
            
            else:
                raise ParseError(f"Unknown symbol: {{top_symbol}}")
        
        return root


def tokenize_simple(text: str) -> List[Token]:
    """Tokenizador simples para testes - separa por espaços"""
    tokens = []
    pos = 0
    for word in text.split():
        tokens.append(Token(word, word, pos))
        pos += len(word) + 1
    return tokens


if __name__ == "__main__":
    # Exemplo de utilização
    test_input = "your input here"
    tokens = tokenize_simple(test_input)
    parser = TableDrivenParser(tokens)
    try:
        tree = parser.parse()
        print("Parse successful!")
        print(tree)
    except ParseError as e:
        print(f"Parse error: {{e}}")
'''
        return code
