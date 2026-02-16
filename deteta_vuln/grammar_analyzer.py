"""
Grammar Analyzer - Analyzes context-free grammars for LL(1) properties
Computes FIRST and FOLLOW sets, detects conflicts, and validates grammar
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import json

@dataclass
class Production:
    """Represents a single production rule (one alternative)"""
    nonterminal: str
    body: List[str]  # Empty list for epsilon
    
    def __hash__(self):
        return hash((self.nonterminal, tuple(self.body)))
    
    def __eq__(self, other):
        return self.nonterminal == other.nonterminal and self.body == other.body
    
    def __repr__(self):
        body_str = " ".join(self.body) if self.body else "ε"
        return f"{self.nonterminal} → {body_str}"

@dataclass
class LL1Conflict:
    """Represents an LL(1) conflict"""
    nonterminal: str
    terminal: str
    productions: List[Production]
    conflict_type: str  # "FIRST/FIRST", "FIRST/FOLLOW", or "FIRST/EPSILON"
    
    def __repr__(self):
        prod_str = " | ".join(str(p) for p in self.productions)
        return f"Conflict at ({self.nonterminal}, {self.terminal}) [{self.conflict_type}]: {prod_str}"

class GrammarAnalyzer:
    """Analyzes context-free grammars for LL(1) properties"""
    
    def __init__(self, grammar_dict: Dict[str, List[List[str]]]):
        """
        Initialize with grammar as dictionary of productions.
        
        Example:
            {
                'Program': [['StmtList']],
                'StmtList': [['Stmt', "StmtList'"], []],
                'Stmt': [['id', ':=', 'Expr']]
            }
        """
        self.grammar = grammar_dict
        self.nonterminals = set(grammar_dict.keys())
        self.terminals = self._extract_terminals()
        self.epsilon = "$EPSILON"  # Special marker for epsilon
        self.eof = "$EOF"  # End of input marker
        
        # Analysis results
        self.first: Dict[str, Set[str]] = {}
        self.follow: Dict[str, Set[str]] = {}
        self.ll1_table: Dict[Tuple[str, str], List[Production]] = {}
        self.conflicts: List[LL1Conflict] = []
        
    def _extract_terminals(self) -> Set[str]:
        """Extract all terminal symbols from grammar"""
        terminals = set()
        for nt, productions in self.grammar.items():
            for body in productions:
                for symbol in body:
                    if symbol not in self.nonterminals:
                        terminals.add(symbol)
        terminals.add(self.eof)
        return terminals
    
    def compute_first(self) -> Dict[str, Set[str]]:
        """
        Compute FIRST sets for all nonterminals.
        FIRST(α) = {a | α ⇒* aβ} ∪ {ε | α ⇒* ε}
        """
        # Initialize FIRST sets
        for nt in self.nonterminals:
            self.first[nt] = set()
        
        # Iteratively compute FIRST until no changes
        changed = True
        iterations = 0
        max_iterations = len(self.nonterminals) * len(self.nonterminals)
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for nt, productions in self.grammar.items():
                for body in productions:
                    if not body:  # Epsilon production
                        if self.epsilon not in self.first[nt]:
                            self.first[nt].add(self.epsilon)
                            changed = True
                    else:
                        # Add FIRST of first symbol that can derive epsilon
                        for i, symbol in enumerate(body):
                            if symbol in self.nonterminals:
                                # Add all non-epsilon terminals from FIRST(symbol)
                                before = len(self.first[nt])
                                self.first[nt].update(
                                    s for s in self.first.get(symbol, set())
                                    if s != self.epsilon
                                )
                                
                                # If symbol can't derive epsilon, stop
                                if self.epsilon not in self.first.get(symbol, set()):
                                    break
                            else:
                                # Terminal symbol
                                if symbol not in self.first[nt]:
                                    self.first[nt].add(symbol)
                                    changed = True
                                break
                        else:
                            # All symbols can derive epsilon
                            if self.epsilon not in self.first[nt]:
                                self.first[nt].add(self.epsilon)
                                changed = True
                        
                        if len(self.first[nt]) > before:
                            changed = True
        
        return self.first
    
    def first_of_sequence(self, sequence: List[str]) -> Set[str]:
        """Compute FIRST set of a sequence of symbols"""
        result = set()
        
        for symbol in sequence:
            if symbol in self.nonterminals:
                result.update(
                    s for s in self.first.get(symbol, set())
                    if s != self.epsilon
                )
                if self.epsilon not in self.first.get(symbol, set()):
                    return result
            else:
                result.add(symbol)
                return result
        
        # All symbols can derive epsilon
        result.add(self.epsilon)
        return result
    
    def compute_follow(self) -> Dict[str, Set[str]]:
        """
        Compute FOLLOW sets for all nonterminals.
        FOLLOW(A) = {a | S ⇒* ... Aa ...}
        """
        # Initialize FOLLOW sets
        for nt in self.nonterminals:
            self.follow[nt] = set()
        
        # Add EOF to follow of start symbol
        start_symbol = next(iter(self.grammar.keys()))
        self.follow[start_symbol].add(self.eof)
        
        # Iteratively compute FOLLOW until no changes
        changed = True
        iterations = 0
        max_iterations = len(self.nonterminals) * len(self.nonterminals)
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for nt, productions in self.grammar.items():
                for body in productions:
                    for i, symbol in enumerate(body):
                        if symbol in self.nonterminals:
                            before_size = len(self.follow[symbol])
                            
                            # Compute FIRST of what follows this symbol
                            rest = body[i+1:]
                            first_rest = self.first_of_sequence(rest)
                            
                            # Add non-epsilon terminals from FIRST of rest
                            self.follow[symbol].update(
                                s for s in first_rest
                                if s != self.epsilon
                            )
                            
                            # If rest can derive epsilon, add FOLLOW of nt
                            if self.epsilon in first_rest:
                                self.follow[symbol].update(self.follow[nt])
                            
                            if len(self.follow[symbol]) > before_size:
                                changed = True
        
        # Remove epsilon marker from FOLLOW sets
        for nt in self.follow:
            self.follow[nt].discard(self.epsilon)
        
        return self.follow
    
    def build_ll1_table(self) -> Dict[Tuple[str, str], List[Production]]:
        """Build LL(1) parsing table"""
        self.conflicts = []
        self.ll1_table = {}
        
        for nt, productions in self.grammar.items():
            for body in productions:
                prod = Production(nt, body)
                first_set = self.first_of_sequence(body)
                
                # For each terminal in FIRST(body)
                for terminal in first_set:
                    if terminal == self.epsilon:
                        continue
                    
                    key = (nt, terminal)
                    if key not in self.ll1_table:
                        self.ll1_table[key] = []
                    
                    if prod not in self.ll1_table[key]:
                        self.ll1_table[key].append(prod)
                
                # If body can derive epsilon, add for each terminal in FOLLOW(nt)
                if self.epsilon in first_set:
                    for terminal in self.follow[nt]:
                        key = (nt, terminal)
                        if key not in self.ll1_table:
                            self.ll1_table[key] = []
                        
                        if prod not in self.ll1_table[key]:
                            self.ll1_table[key].append(prod)
        
        return self.ll1_table
    
    def detect_conflicts(self) -> List[LL1Conflict]:
        """Detect LL(1) conflicts in the grammar"""
        self.conflicts = []
        
        for (nt, terminal), productions in self.ll1_table.items():
            if len(productions) > 1:
                conflict_type = "FIRST/FIRST"  # Simplified for now
                conflict = LL1Conflict(
                    nonterminal=nt,
                    terminal=terminal,
                    productions=productions,
                    conflict_type=conflict_type
                )
                self.conflicts.append(conflict)
        
        return self.conflicts
    
    def is_ll1(self) -> bool:
        """Check if grammar is LL(1)"""
        return len(self.conflicts) == 0
    
    def analyze_complete(self) -> Dict:
        """Perform complete LL(1) analysis"""
        self.compute_first()
        self.compute_follow()
        self.build_ll1_table()
        self.detect_conflicts()
        
        return {
            'first': {nt: self._format_set(s) for nt, s in self.first.items()},
            'follow': {nt: self._format_set(s) for nt, s in self.follow.items()},
            'll1_table': self._format_table(),
            'is_ll1': self.is_ll1(),
            'conflicts': [str(c) for c in self.conflicts],
            'conflict_count': len(self.conflicts)
        }
    
    def _format_set(self, s: Set[str]) -> List[str]:
        """Format a set for JSON serialization"""
        return sorted([
            "ε" if x == self.epsilon else "$" if x == self.eof else x
            for x in s
        ])
    
    def _format_table(self) -> Dict[str, List[str]]:
        """Format parsing table for JSON serialization"""
        result = {}
        for (nt, terminal), productions in self.ll1_table.items():
            key = f"{nt},{terminal if terminal != self.eof else '$'}"
            result[key] = [str(p) for p in productions]
        return result


def parse_grammar_text(text: str) -> Dict[str, List[List[str]]]:
    """
    Parse grammar from text format.
    Format: NT → alt1 | alt2 | ...;
    
    Example:
        Program → StmtList;
        StmtList → Stmt StmtList' | ε;
        Stmt → id := Expr;
    """
    grammar = {}
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        
        if '→' not in line:
            continue
        
        # Remove semicolon at end
        if line.endswith(';'):
            line = line[:-1]
        
        left, right = line.split('→', 1)
        nonterminal = left.strip()
        
        if nonterminal not in grammar:
            grammar[nonterminal] = []
        
        # Parse alternatives
        alternatives = right.split('|')
        for alt in alternatives:
            alt = alt.strip()
            if alt == 'ε':
                grammar[nonterminal].append([])
            else:
                symbols = alt.split()
                grammar[nonterminal].append(symbols)
    
    return grammar
