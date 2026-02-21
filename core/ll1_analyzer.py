"""
Grammar Playground - LL(1) Analyzer
Computes FIRST, FOLLOW sets and LL(1) parsing table
Detects and reports conflicts
"""

from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass, field
from .grammar import Grammar, Symbol, Production, EPSILON, END_MARKER, SymbolType


@dataclass
class Conflict:
    """Represents an LL(1) conflict"""
    type: str  # "FIRST/FIRST" or "FIRST/FOLLOW"
    non_terminal: Symbol
    terminal: Symbol
    productions: List[Production]
    description: str
    suggestion: str = ""


@dataclass
class LL1Table:
    """LL(1) parsing table"""
    table: Dict[Tuple[Symbol, Symbol], List[Production]] = field(default_factory=dict)
    conflicts: List[Conflict] = field(default_factory=list)
    
    def get(self, non_terminal: Symbol, terminal: Symbol) -> Optional[List[Production]]:
        """Get production(s) for a given non-terminal and terminal"""
        return self.table.get((non_terminal, terminal))
    
    def set(self, non_terminal: Symbol, terminal: Symbol, production: Production):
        """Set a production in the table"""
        key = (non_terminal, terminal)
        if key not in self.table:
            self.table[key] = []
        if production not in self.table[key]:
            self.table[key].append(production)
    
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts in the table"""
        return len(self.conflicts) > 0
    
    def get_terminals(self) -> Set[Symbol]:
        """Get all terminals in the table"""
        terminals = set()
        for (_, terminal) in self.table.keys():
            terminals.add(terminal)
        return terminals
    
    def get_non_terminals(self) -> Set[Symbol]:
        """Get all non-terminals in the table"""
        non_terminals = set()
        for (nt, _) in self.table.keys():
            non_terminals.add(nt)
        return non_terminals


class LL1Analyzer:
    """Analyzes a grammar for LL(1) properties"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.first_sets: Dict[Symbol, Set[Symbol]] = {}
        self.follow_sets: Dict[Symbol, Set[Symbol]] = {}
        self.nullable: Set[Symbol] = set()
        self.ll1_table: Optional[LL1Table] = None
    
    def analyze(self) -> LL1Table:
        """Perform complete LL(1) analysis"""
        self._compute_nullable()
        self._compute_first_sets()
        self._compute_follow_sets()
        self._build_ll1_table()
        
        # Store in grammar for later use
        self.grammar.first_sets = self.first_sets
        self.grammar.follow_sets = self.follow_sets
        self.grammar.nullable = self.nullable
        
        return self.ll1_table
    
    def _compute_nullable(self):
        """Compute which non-terminals can derive ε"""
        self.nullable = {EPSILON}
        
        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                if prod.head not in self.nullable:
                    # A production is nullable if all symbols in its body are nullable
                    if all(s in self.nullable for s in prod.body):
                        self.nullable.add(prod.head)
                        changed = True
    
    def _compute_first_sets(self):
        """Compute FIRST sets for all symbols"""
        # Initialize FIRST sets
        for terminal in self.grammar.terminals:
            self.first_sets[terminal] = {terminal}
        
        for nt in self.grammar.non_terminals:
            self.first_sets[nt] = set()
        
        self.first_sets[EPSILON] = {EPSILON}
        self.first_sets[END_MARKER] = {END_MARKER}
        
        # Fixed-point iteration
        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                head = prod.head
                old_size = len(self.first_sets[head])
                
                # Compute FIRST of the production body
                first_of_body = self._first_of_sequence(prod.body)
                self.first_sets[head].update(first_of_body)
                
                if len(self.first_sets[head]) > old_size:
                    changed = True
    
    def _first_of_sequence(self, symbols: List[Symbol]) -> Set[Symbol]:
        """Compute FIRST set for a sequence of symbols"""
        result = set()
        
        if not symbols:
            return {EPSILON}
        
        for i, symbol in enumerate(symbols):
            if symbol.is_epsilon():
                result.add(EPSILON)
                continue
            
            # Add FIRST(symbol) - {ε} to result
            if symbol in self.first_sets:
                result.update(self.first_sets[symbol] - {EPSILON})
            elif symbol.is_terminal():
                result.add(symbol)
                return result
            
            # If symbol is not nullable, stop
            if symbol not in self.nullable:
                break
            
            # If we've processed all symbols and all are nullable
            if i == len(symbols) - 1 and symbol in self.nullable:
                result.add(EPSILON)
        
        return result
    
    def _compute_follow_sets(self):
        """Compute FOLLOW sets for all non-terminals"""
        # Initialize FOLLOW sets
        for nt in self.grammar.non_terminals:
            self.follow_sets[nt] = set()
        
        # Add $ to FOLLOW(start symbol)
        if self.grammar.start_symbol:
            self.follow_sets[self.grammar.start_symbol].add(END_MARKER)
        
        # Fixed-point iteration
        changed = True
        while changed:
            changed = False
            for prod in self.grammar.productions:
                for i, symbol in enumerate(prod.body):
                    if not symbol.is_non_terminal():
                        continue
                    
                    old_size = len(self.follow_sets[symbol])
                    
                    # Get the rest of the production after this symbol
                    rest = prod.body[i + 1:]
                    
                    if rest:
                        # Add FIRST(rest) - {ε} to FOLLOW(symbol)
                        first_of_rest = self._first_of_sequence(rest)
                        self.follow_sets[symbol].update(first_of_rest - {EPSILON})
                        
                        # If rest can derive ε, add FOLLOW(head) to FOLLOW(symbol)
                        if EPSILON in first_of_rest:
                            self.follow_sets[symbol].update(self.follow_sets[prod.head])
                    else:
                        # Symbol is at the end, add FOLLOW(head) to FOLLOW(symbol)
                        self.follow_sets[symbol].update(self.follow_sets[prod.head])
                    
                    if len(self.follow_sets[symbol]) > old_size:
                        changed = True
    
    def _build_ll1_table(self):
        """Build the LL(1) parsing table and detect conflicts"""
        self.ll1_table = LL1Table()
        
        for prod in self.grammar.productions:
            first_of_body = self._first_of_sequence(prod.body)
            
            # For each terminal in FIRST(body), add production to table
            for terminal in first_of_body:
                if terminal != EPSILON:
                    self.ll1_table.set(prod.head, terminal, prod)
            
            # If ε is in FIRST(body), add production for each terminal in FOLLOW(head)
            if EPSILON in first_of_body:
                for terminal in self.follow_sets[prod.head]:
                    self.ll1_table.set(prod.head, terminal, prod)
        
        # Detect conflicts
        self._detect_conflicts()
    
    def _detect_conflicts(self):
        """Detect and categorize LL(1) conflicts"""
        for (nt, terminal), productions in self.ll1_table.table.items():
            if len(productions) > 1:
                conflict = self._categorize_conflict(nt, terminal, productions)
                self.ll1_table.conflicts.append(conflict)
    
    def _categorize_conflict(self, nt: Symbol, terminal: Symbol, 
                            productions: List[Production]) -> Conflict:
        """Categorize a conflict as FIRST/FIRST or FIRST/FOLLOW"""
        # Check if any production is nullable
        nullable_prods = [p for p in productions if p.is_epsilon_production() or 
                         all(s in self.nullable for s in p.body)]
        non_nullable_prods = [p for p in productions if p not in nullable_prods]
        
        if nullable_prods and non_nullable_prods:
            # FIRST/FOLLOW conflict
            conflict_type = "FIRST/FOLLOW"
            description = (
                f"Conflito FIRST/FOLLOW para {nt} com terminal '{terminal}': "
                f"a produção anulável {nullable_prods[0]} conflita com "
                f"a produção {non_nullable_prods[0]} porque '{terminal}' está "
                f"em FOLLOW({nt}) e também em FIRST da outra produção."
            )
            suggestion = self._suggest_first_follow_fix(nt, productions)
        else:
            # FIRST/FIRST conflict
            conflict_type = "FIRST/FIRST"
            description = (
                f"Conflito FIRST/FIRST para {nt} com terminal '{terminal}': "
                f"múltiplas produções começam com símbolos que derivam '{terminal}'."
            )
            suggestion = self._suggest_first_first_fix(nt, productions)
        
        return Conflict(
            type=conflict_type,
            non_terminal=nt,
            terminal=terminal,
            productions=productions,
            description=description,
            suggestion=suggestion
        )
    
    def _suggest_first_first_fix(self, nt: Symbol, productions: List[Production]) -> str:
        """Suggest a fix for FIRST/FIRST conflicts (usually left factoring)"""
        # Check if productions share a common prefix
        if len(productions) < 2:
            return "Verifique as produções manualmente."
        
        bodies = [p.body for p in productions]
        
        # Find common prefix
        common_prefix = []
        min_len = min(len(b) for b in bodies)
        
        for i in range(min_len):
            symbols_at_i = set(b[i] for b in bodies)
            if len(symbols_at_i) == 1:
                common_prefix.append(bodies[0][i])
            else:
                break
        
        if common_prefix:
            prefix_str = " ".join(str(s) for s in common_prefix)
            return (
                f"Sugestão: Fatoração à esquerda\n"
                f"As produções compartilham o prefixo comum '{prefix_str}'.\n"
                f"Crie um novo não-terminal {nt}' para os sufixos diferentes:\n"
                f"  {nt} → {prefix_str} {nt}'\n"
                f"  {nt}' → <sufixos diferentes>"
            )
        else:
            return (
                f"Sugestão: As produções para {nt} têm ambiguidade.\n"
                f"Considere reestruturar a gramática para eliminar a ambiguidade, "
                f"ou use uma gramática diferente que seja LL(1) compatível."
            )
    
    def _suggest_first_follow_fix(self, nt: Symbol, productions: List[Production]) -> str:
        """Suggest a fix for FIRST/FOLLOW conflicts"""
        nullable = [p for p in productions if p.is_epsilon_production() or 
                   all(s in self.nullable for s in p.body)]
        
        return (
            f"Sugestão: Conflito FIRST/FOLLOW\n"
            f"A produção anulável significa que {nt} pode derivar ε.\n"
            f"Os terminais que seguem {nt} (FOLLOW) conflitam com FIRST de outra produção.\n"
            f"Considere:\n"
            f"  1. Remover a produção ε se possível\n"
            f"  2. Reestruturar a gramática para evitar que terminais "
            f"apareçam tanto em FIRST quanto em FOLLOW"
        )
    
    def first(self, symbol: Symbol) -> Set[Symbol]:
        """Get FIRST set for a symbol"""
        return self.first_sets.get(symbol, set())
    
    def follow(self, symbol: Symbol) -> Set[Symbol]:
        """Get FOLLOW set for a non-terminal"""
        return self.follow_sets.get(symbol, set())
    
    def is_nullable(self, symbol: Symbol) -> bool:
        """Check if a symbol is nullable"""
        return symbol in self.nullable
    
    def first_of_production(self, prod: Production) -> Set[Symbol]:
        """Get FIRST set for a production's body"""
        return self._first_of_sequence(prod.body)
    
    def get_analysis_report(self) -> dict:
        """Generate a complete analysis report"""
        if not self.ll1_table:
            self.analyze()
        
        report = {
            "grammar": {
                "terminals": sorted([str(t) for t in self.grammar.terminals]),
                "non_terminals": sorted([str(nt) for nt in self.grammar.non_terminals]),
                "start_symbol": str(self.grammar.start_symbol) if self.grammar.start_symbol else None,
                "productions": [str(p) for p in self.grammar.productions]
            },
            "nullable": sorted([str(s) for s in self.nullable if s.is_non_terminal()]),
            "first_sets": {
                str(nt): sorted([str(s) for s in self.first_sets.get(nt, set())])
                for nt in self.grammar.non_terminals
            },
            "follow_sets": {
                str(nt): sorted([str(s) for s in self.follow_sets.get(nt, set())])
                for nt in self.grammar.non_terminals
            },
            "is_ll1": not self.ll1_table.has_conflicts(),
            "conflicts": [
                {
                    "type": c.type,
                    "non_terminal": str(c.non_terminal),
                    "terminal": str(c.terminal),
                    "productions": [str(p) for p in c.productions],
                    "description": c.description,
                    "suggestion": c.suggestion
                }
                for c in self.ll1_table.conflicts
            ],
            "ll1_table": self._table_to_dict()
        }
        
        return report
    
    def _table_to_dict(self) -> dict:
        """Convert LL(1) table to a dictionary for display"""
        result = {}
        for (nt, terminal), productions in self.ll1_table.table.items():
            nt_str = str(nt)
            if nt_str not in result:
                result[nt_str] = {}
            result[nt_str][str(terminal)] = [str(p) for p in productions]
        return result
