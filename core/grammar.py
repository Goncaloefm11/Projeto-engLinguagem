"""
Grammar Playground - Core Grammar Model
Estrutura da gramática: símbolos terminais, símbolos não-terminais e produções
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple
from enum import Enum
import re


class SymbolType(Enum):
    TERMINAL = "terminal"
    NON_TERMINAL = "non_terminal"
    EPSILON = "epsilon"
    END_MARKER = "end_marker"


@dataclass
class Symbol:
    """Represents a grammar symbol (terminal or non-terminal)"""
    name: str
    symbol_type: SymbolType
    
    def __hash__(self):
        return hash((self.name, self.symbol_type))
    
    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.name == other.name and self.symbol_type == other.symbol_type
        return False
    
    def __repr__(self):
        return self.name
    
    def is_terminal(self) -> bool:
        return self.symbol_type == SymbolType.TERMINAL
    
    def is_non_terminal(self) -> bool:
        return self.symbol_type == SymbolType.NON_TERMINAL
    
    def is_epsilon(self) -> bool:
        return self.symbol_type == SymbolType.EPSILON


# Special symbols
EPSILON = Symbol("ε", SymbolType.EPSILON)
END_MARKER = Symbol("$", SymbolType.END_MARKER)


@dataclass
class Production:
    """Represents a grammar production: head → body"""
    head: Symbol
    body: List[Symbol]
    index: int = 0  # Production number for identification
    
    def __hash__(self):
        return hash((self.head, tuple(self.body), self.index))
    
    def __repr__(self):
        body_str = " ".join(str(s) for s in self.body) if self.body else "ε"
        return f"{self.head} → {body_str}"
    
    def is_epsilon_production(self) -> bool:
        """Check if this is an epsilon production (A → ε)"""
        return len(self.body) == 1 and self.body[0].is_epsilon()
    
    def is_nullable(self) -> bool:
        """Check if this production directly derives epsilon"""
        return self.is_epsilon_production()


@dataclass
class Grammar:
    """Represents a context-free grammar"""
    terminals: Set[Symbol] = field(default_factory=set)
    non_terminals: Set[Symbol] = field(default_factory=set)
    productions: List[Production] = field(default_factory=list)
    start_symbol: Optional[Symbol] = None
    
    # Computed sets
    first_sets: Dict[Symbol, Set[Symbol]] = field(default_factory=dict)
    follow_sets: Dict[Symbol, Set[Symbol]] = field(default_factory=dict)
    nullable: Set[Symbol] = field(default_factory=set)
    
    def add_terminal(self, name: str) -> Symbol:
        """Add a terminal symbol to the grammar"""
        symbol = Symbol(name, SymbolType.TERMINAL)
        self.terminals.add(symbol)
        return symbol
    
    def add_non_terminal(self, name: str) -> Symbol:
        """Add a non-terminal symbol to the grammar"""
        symbol = Symbol(name, SymbolType.NON_TERMINAL)
        self.non_terminals.add(symbol)
        return symbol
    
    def add_production(self, head: Symbol, body: List[Symbol]) -> Production:
        """Add a production to the grammar"""
        prod = Production(head, body, len(self.productions))
        self.productions.append(prod)
        return prod
    
    def get_productions_for(self, non_terminal: Symbol) -> List[Production]:
        """Get all productions for a given non-terminal"""
        return [p for p in self.productions if p.head == non_terminal]
    
    def get_symbol_by_name(self, name: str) -> Optional[Symbol]:
        """Find a symbol by name"""
        for s in self.terminals:
            if s.name == name:
                return s
        for s in self.non_terminals:
            if s.name == name:
                return s
        if name == "ε":
            return EPSILON
        return None
    
    def validate(self) -> List[str]:
        """Validate the grammar and return any errors"""
        errors = []
        
        if not self.start_symbol:
            errors.append("No start symbol defined")
        elif self.start_symbol not in self.non_terminals:
            errors.append(f"Start symbol '{self.start_symbol}' is not a non-terminal")
        
        if not self.productions:
            errors.append("No productions defined")
        
        # Check that all non-terminals have at least one production
        for nt in self.non_terminals:
            if not self.get_productions_for(nt):
                errors.append(f"Non-terminal '{nt}' has no productions")
        
        # Check that all symbols in productions are defined
        for prod in self.productions:
            if prod.head not in self.non_terminals:
                errors.append(f"Production head '{prod.head}' is not a non-terminal")
            for symbol in prod.body:
                if not symbol.is_epsilon():
                    if symbol not in self.terminals and symbol not in self.non_terminals:
                        errors.append(f"Symbol '{symbol}' in production '{prod}' is not defined")
        
        return errors


class GrammarParser:
    """
    Parser para a Meta-Gramática (a linguagem de especificação de gramáticas).
    
    Especificação Formal (EBNF):
    <Grammar>      ::= <Production>+
    <Production>   ::= <Head> <Arrow> <Alternatives>
    <Head>         ::= <Symbol>
    <Arrow>        ::= "→" | "->"
    <Alternatives> ::= <Sequence> ( "|" <Sequence> )*
    <Sequence>     ::= <Symbol>+ | <Epsilon>
    <Epsilon>      ::= "ε" | "epsilon" | "ɛ"
    <Symbol>       ::= Letras, números ou caracteres especiais (exceto espaços, | e setas)
    """
    
    @staticmethod
    def is_terminal(name: str) -> bool:
        """
        Determine if a symbol name represents a terminal.
        Terminals: lowercase words, quoted strings, special chars like ; := + -
        Non-terminals: Start with uppercase
        """
        if name in ['ε', 'epsilon', 'ɛ']:
            return False
        if name.startswith("'") and name.endswith("'"):
            return True
        if name.startswith('"') and name.endswith('"'):
            return True
        if len(name) == 1 and not name.isalpha():
            return True
        if name in [':=', '==', '!=', '<=', '>=', '->', '=>', '++', '--', '&&', '||']:
            return True
        # Lowercase or special symbols are terminals
        if name[0].islower() or not name[0].isalpha():
            return True
        return False
    
    @classmethod
    def parse(cls, text: str) -> Grammar:
        """
        Implementa um parser descendente para analisar o texto de entrada 
        seguindo estritamente as regras da Meta-Gramática.
        """
        grammar = Grammar()
        
        # 1. Análise Lexical Simples (Separação por linhas de produção)
        # Normalizar '\n' literais que possam vir de JSON para quebras de linha reais
        normalized_text = text.replace('\\n', '\n')
        
        # Usar splitlines() lida melhor com diferentes tipos de quebra de linha (\r\n, \n)
        lines = [line.strip() for line in normalized_text.splitlines() if line.strip() and not line.startswith('#')]
        
        all_symbols = set()
        productions_raw = []
        
        # 2. Análise Sintática
        for line in lines:
            # Normalizar a seta para facilitar o parsing da regra <Arrow>
            line = line.replace("->", "→")
            
            if "→" not in line:
                raise ValueError(f"Erro Sintático: A produção deve conter uma seta '→' ou '->'. Linha: {line}")
            
            # Regra: <Production> ::= <Head> <Arrow> <Alternatives>
            head_str, body_str = line.split("→", 1)
            head = head_str.strip()
            
            # Validar <Head>
            if not head or " " in head:
                raise ValueError(f"Erro Sintático: A cabeça da produção tem de ser um único símbolo. Encontrado: '{head}'")
                
            all_symbols.add(head)
            
            # Regra: <Alternatives> ::= <Sequence> ( "|" <Sequence> )*
            alternatives = body_str.split('|')
            for alt in alternatives:
                alt = alt.strip()
                
                # Regra: <Sequence> ::= <Symbol>+ | <Epsilon>
                symbols = alt.split() # O split por defeito separa por espaços em branco
                
                # Tratar produções perfeitamente vazias como Epsilon
                if not symbols:
                    symbols = ['ε']
                    
                for s in symbols:
                    if s not in ['ε', 'epsilon', 'ɛ']:
                        all_symbols.add(s)
                        
                productions_raw.append((head, symbols))
        
        # 3. Construção da Gramática (Identificação Semântica)
        non_terminal_names = {head for head, _ in productions_raw}
        symbol_map = {}
        
        for name in all_symbols:
            if name in non_terminal_names:
                symbol_map[name] = grammar.add_non_terminal(name)
            elif cls.is_terminal(name):
                symbol_map[name] = grammar.add_terminal(name)
            else:
                symbol_map[name] = grammar.add_non_terminal(name)
        
        # Definir o símbolo inicial (a primeira cabeça encontrada)
        if productions_raw:
            first_head = productions_raw[0][0]
            grammar.start_symbol = symbol_map[first_head]
        
        # Associar as regras (Produções)
        for head, body_symbols in productions_raw:
            head_symbol = symbol_map[head]
            body = []
            
            for s in body_symbols:
                if s in ['ε', 'epsilon', 'ɛ']:
                    body.append(EPSILON)
                else:
                    body.append(symbol_map[s])
            
            if not body:
                body = [EPSILON]
            
            grammar.add_production(head_symbol, body)
        
        return grammar

    @staticmethod
    def to_text(grammar: Grammar) -> str:
        # (Mantém o teu método original to_text aqui em baixo)
        lines = []
        current_head = None
        current_alts = []
        
        for prod in grammar.productions:
            if current_head != prod.head:
                if current_head is not None:
                    body_str = " | ".join(current_alts)
                    lines.append(f"{current_head} → {body_str}")
                current_head = prod.head
                current_alts = []
            
            if prod.is_epsilon_production():
                current_alts.append("ε")
            else:
                current_alts.append(" ".join(str(s) for s in prod.body))
        
        if current_head is not None:
            body_str = " | ".join(current_alts)
            lines.append(f"{current_head} → {body_str}")
        
        return "\n".join(lines)