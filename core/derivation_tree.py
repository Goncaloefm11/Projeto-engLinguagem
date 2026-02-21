"""
Grammar Playground - Derivation Tree
Parse input and construct derivation trees with text and graphical output
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
from .grammar import Grammar, Symbol, Production, EPSILON, END_MARKER, SymbolType
from .ll1_analyzer import LL1Analyzer


@dataclass
class Token:
    """Represents a token from the input"""
    type: str
    value: str
    position: int = 0
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


@dataclass
class TreeNode:
    """Node in the derivation tree"""
    symbol: str
    children: List["TreeNode"] = field(default_factory=list)
    token: Optional[Token] = None
    production_index: Optional[int] = None
    
    def is_terminal(self) -> bool:
        return self.token is not None or self.symbol == "ε"
    
    def add_child(self, child: "TreeNode"):
        self.children.append(child)
    
    def to_text(self, indent: int = 0, prefix: str = "") -> str:
        """Convert tree to text representation"""
        lines = []
        connector = "├── " if prefix else ""
        end_connector = "└── " if prefix else ""
        
        if self.is_terminal():
            if self.token:
                lines.append(f"{prefix}{self.symbol}: '{self.token.value}'")
            else:
                lines.append(f"{prefix}{self.symbol}")
        else:
            lines.append(f"{prefix}{self.symbol}")
        
        for i, child in enumerate(self.children):
            is_last = (i == len(self.children) - 1)
            new_prefix = prefix + ("    " if not prefix else ("    " if is_last else "│   "))
            child_connector = "└── " if is_last else "├── "
            
            child_text = child.to_text(indent + 1, "")
            lines.append(f"{prefix}{child_connector}{child_text.strip()}")
        
        return "\n".join(lines)
    
    def to_simple_text(self, indent: int = 0) -> str:
        """Simple indented text representation"""
        result = "  " * indent + self.symbol
        if self.token:
            result += f" ('{self.token.value}')"
        result += "\n"
        for child in self.children:
            result += child.to_simple_text(indent + 1)
        return result
    
    def to_dict(self) -> dict:
        """Convert tree to dictionary for JSON serialization"""
        result = {
            "symbol": self.symbol,
            "isTerminal": self.is_terminal(),
            "children": [child.to_dict() for child in self.children]
        }
        if self.token:
            result["value"] = self.token.value
        if self.production_index is not None:
            result["production"] = self.production_index
        return result
    
    def to_mermaid(self) -> str:
        """Convert tree to Mermaid diagram format"""
        lines = ["graph TD"]
        node_counter = [0]
        
        def add_node(node: "TreeNode", parent_id: Optional[str] = None) -> str:
            node_id = f"N{node_counter[0]}"
            node_counter[0] += 1
            
            if node.is_terminal():
                if node.token:
                    label = f'{node.symbol}: "{node.token.value}"'
                else:
                    label = node.symbol
                lines.append(f'    {node_id}["{label}"]')
                lines.append(f'    style {node_id} fill:#90EE90')
            else:
                lines.append(f'    {node_id}(("{node.symbol}"))')
            
            if parent_id:
                lines.append(f'    {parent_id} --> {node_id}')
            
            for child in node.children:
                add_node(child, node_id)
            
            return node_id
        
        add_node(self)
        return "\n".join(lines)
    
    def to_d3_json(self) -> str:
        """Convert tree to D3.js hierarchical format"""
        def convert(node: "TreeNode") -> dict:
            result = {"name": node.symbol}
            if node.token:
                result["value"] = node.token.value
                result["type"] = "terminal"
            else:
                result["type"] = "nonterminal"
            if node.children:
                result["children"] = [convert(child) for child in node.children]
            return result
        
        return json.dumps(convert(self), indent=2)


class SimpleTokenizer:
    """Simple tokenizer that splits input based on grammar terminals"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        # Sort terminals by length (longest first) for proper matching
        self.terminals = sorted(
            [str(t) for t in grammar.terminals],
            key=lambda x: -len(x)
        )
    
    def tokenize(self, text: str) -> List[Token]:
        """Tokenize input text"""
        tokens = []
        pos = 0
        text = text.strip()
        
        while pos < len(text):
            # Skip whitespace
            while pos < len(text) and text[pos].isspace():
                pos += 1
            
            if pos >= len(text):
                break
            
            matched = False
            
            # Try to match terminals
            for terminal in self.terminals:
                if text[pos:].startswith(terminal):
                    # Check word boundary for identifiers
                    end_pos = pos + len(terminal)
                    if terminal.isalnum() and end_pos < len(text) and text[end_pos].isalnum():
                        continue
                    
                    tokens.append(Token(terminal, terminal, pos))
                    pos += len(terminal)
                    matched = True
                    break
            
            if not matched:
                # Match an identifier or number
                if text[pos].isalpha() or text[pos] == '_':
                    start = pos
                    while pos < len(text) and (text[pos].isalnum() or text[pos] == '_'):
                        pos += 1
                    word = text[start:pos]
                    
                    # Check if it's a keyword/terminal
                    if word in self.terminals:
                        tokens.append(Token(word, word, start))
                    else:
                        # It's an identifier
                        tokens.append(Token("id", word, start))
                
                elif text[pos].isdigit():
                    start = pos
                    while pos < len(text) and (text[pos].isdigit() or text[pos] == '.'):
                        pos += 1
                    tokens.append(Token("number", text[start:pos], start))
                
                else:
                    # Single character operator
                    tokens.append(Token(text[pos], text[pos], pos))
                    pos += 1
        
        return tokens


class DerivationTreeBuilder:
    """Builds derivation trees from input using LL(1) parsing"""
    
    def __init__(self, grammar: Grammar, analyzer: LL1Analyzer):
        self.grammar = grammar
        self.analyzer = analyzer
        if not analyzer.ll1_table:
            analyzer.analyze()
        self.tokenizer = SimpleTokenizer(grammar)
    
    def parse(self, input_text: str) -> Tuple[Optional[TreeNode], List[str], List[dict]]:
        """
        Parse input text and return (tree, errors, derivation_steps)
        """
        tokens = self.tokenizer.tokenize(input_text)
        errors = []
        derivation_steps = []
        
        if not tokens:
            errors.append("No input tokens")
            return None, errors, derivation_steps
        
        # Add end marker
        tokens.append(Token("$", "$", len(input_text)))
        
        try:
            tree, steps = self._parse_ll1(tokens)
            return tree, errors, steps
        except ParseError as e:
            errors.append(str(e))
            return None, errors, derivation_steps
    
    def _parse_ll1(self, tokens: List[Token]) -> Tuple[TreeNode, List[dict]]:
        """LL(1) table-driven parsing with tree construction"""
        start = str(self.grammar.start_symbol)
        root = TreeNode(start)
        
        # Stack: (symbol_str, tree_node_or_none)
        stack: List[Tuple[str, Optional[TreeNode]]] = [("$", None), (start, root)]
        token_idx = 0
        derivation_steps = []
        
        step_num = 0
        
        while stack:
            top_symbol, node = stack.pop()
            current_token = tokens[token_idx] if token_idx < len(tokens) else Token("$", "$")
            la = current_token.type
            
            step_num += 1
            step = {
                "step": step_num,
                "stack": [s for s, _ in stack] + [top_symbol],
                "input": [t.type for t in tokens[token_idx:]],
                "action": ""
            }
            
            if top_symbol == "$":
                if la == "$":
                    step["action"] = "Accept"
                    derivation_steps.append(step)
                    break
                else:
                    raise ParseError(f"Expected end of input, got '{la}'")
            
            if top_symbol == "ε":
                step["action"] = "Skip ε"
                derivation_steps.append(step)
                continue
            
            # Check if terminal
            symbol_obj = self.grammar.get_symbol_by_name(top_symbol)
            is_terminal = symbol_obj and symbol_obj.is_terminal()
            
            if not symbol_obj:
                # Check if it matches current token directly
                is_terminal = top_symbol not in [str(nt) for nt in self.grammar.non_terminals]
            
            if is_terminal:
                if top_symbol == la:
                    step["action"] = f"Match '{la}'"
                    derivation_steps.append(step)
                    
                    if node:
                        node.token = current_token
                    token_idx += 1
                else:
                    raise ParseError(f"Expected '{top_symbol}', got '{la}' at position {current_token.position}")
            
            else:
                # Non-terminal - look up in table
                key = (symbol_obj, self.grammar.get_symbol_by_name(la))
                
                # Try different key formats
                productions = None
                for (nt, term), prods in self.analyzer.ll1_table.table.items():
                    if str(nt) == top_symbol and str(term) == la:
                        productions = prods
                        break
                
                if not productions:
                    expected = []
                    for (nt, term), _ in self.analyzer.ll1_table.table.items():
                        if str(nt) == top_symbol:
                            expected.append(str(term))
                    raise ParseError(
                        f"No production for {top_symbol} with lookahead '{la}'. "
                        f"Expected: {', '.join(expected)}"
                    )
                
                production = productions[0]
                step["action"] = f"Apply: {production}"
                derivation_steps.append(step)
                
                # Push production body in reverse
                if production.is_epsilon_production():
                    epsilon_node = TreeNode("ε")
                    if node:
                        node.add_child(epsilon_node)
                else:
                    children_nodes = []
                    for sym in production.body:
                        child = TreeNode(str(sym))
                        children_nodes.append(child)
                        if node:
                            node.add_child(child)
                    
                    for child in reversed(children_nodes):
                        stack.append((child.symbol, child))
        
        return root, derivation_steps


class ParseError(Exception):
    """Raised when parsing fails"""
    pass


def build_derivation_tree(grammar_text: str, input_text: str) -> dict:
    """
    High-level function to build a derivation tree.
    Uses Lark parser for tree construction.
    Returns a dictionary with all results.
    """
    from .lark_parser import build_derivation_tree_lark
    
    # Use Lark-based parsing
    return build_derivation_tree_lark(grammar_text, input_text)
