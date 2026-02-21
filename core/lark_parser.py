"""
Grammar Playground - Lark-based Parser
Converts custom grammar format to Lark and uses Lark to build parse trees
"""

from typing import Optional, Tuple, List, Dict
import re
from lark import Lark, Tree, Token as LarkToken
from lark.exceptions import LarkError, UnexpectedInput

from .grammar import Grammar, GrammarParser


class LarkGrammarConverter:
    """Converts custom grammar format to Lark EBNF format"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self._terminal_rules: Dict[str, str] = {}
        self._rule_counter = 0
    
    def _sanitize_rule_name(self, name: str) -> str:
        """Convert a non-terminal name to a valid Lark rule name (lowercase)"""
        # Replace special characters like apostrophes
        sanitized = name.replace("'", "_prime")
        sanitized = sanitized.replace("-", "_")
        # Lark rules must be lowercase
        return sanitized.lower()
    
    def _sanitize_terminal_name(self, name: str) -> str:
        """Convert a terminal name to a valid Lark terminal name (UPPERCASE)"""
        if name in self._terminal_rules:
            return self._terminal_rules[name]
        
        self._rule_counter += 1
        
        # Handle special characters
        if name == ':=':
            terminal_name = 'ASSIGN'
        elif name == '+':
            terminal_name = 'PLUS'
        elif name == '-':
            terminal_name = 'MINUS'
        elif name == '*':
            terminal_name = 'STAR'
        elif name == '/':
            terminal_name = 'SLASH'
        elif name == '(':
            terminal_name = 'LPAREN'
        elif name == ')':
            terminal_name = 'RPAREN'
        elif name == ';':
            terminal_name = 'SEMICOLON'
        elif name == ',':
            terminal_name = 'COMMA'
        elif name == '==':
            terminal_name = 'EQ'
        elif name == '!=':
            terminal_name = 'NEQ'
        elif name == '<=':
            terminal_name = 'LE'
        elif name == '>=':
            terminal_name = 'GE'
        elif name == '<':
            terminal_name = 'LT'
        elif name == '>':
            terminal_name = 'GT'
        elif name == 'id':
            terminal_name = 'ID'
        elif name == 'number':
            terminal_name = 'NUMBER'
        elif name.isalnum() and name[0].islower():
            terminal_name = name.upper()
        else:
            terminal_name = f'TERM_{self._rule_counter}'
        
        self._terminal_rules[name] = terminal_name
        return terminal_name
    
    def _escape_terminal_value(self, value: str) -> str:
        """Escape a terminal value for use in Lark regex"""
        # Escape regex special characters
        special_chars = r'\.^$*+?{}[]|()'
        escaped = ''
        for char in value:
            if char in special_chars:
                escaped += '\\' + char
            else:
                escaped += char
        return escaped
    
    def convert(self) -> str:
        """Convert the grammar to Lark EBNF format"""
        lines = []
        
        # Track which terminals we need to define
        terminals_used = set()
        
        # Build rules for each non-terminal
        rules_by_head = {}
        for prod in self.grammar.productions:
            head_name = str(prod.head)
            if head_name not in rules_by_head:
                rules_by_head[head_name] = []
            rules_by_head[head_name].append(prod)
        
        # Generate rules
        for head_name, productions in rules_by_head.items():
            rule_name = self._sanitize_rule_name(head_name)
            alternatives = []
            
            for prod in productions:
                if prod.is_epsilon_production():
                    # Empty alternative (epsilon)
                    alternatives.append('')
                else:
                    parts = []
                    for symbol in prod.body:
                        if symbol.is_terminal():
                            term_name = self._sanitize_terminal_name(str(symbol))
                            terminals_used.add(str(symbol))
                            parts.append(term_name)
                        elif symbol.is_non_terminal():
                            parts.append(self._sanitize_rule_name(str(symbol)))
                    alternatives.append(' '.join(parts))
            
            # Build the rule
            # Handle empty alternatives (epsilon)
            non_empty = [a for a in alternatives if a]
            empty_count = len(alternatives) - len(non_empty)
            
            if empty_count > 0 and non_empty:
                # Has both epsilon and non-epsilon alternatives
                # Use optional syntax or just include empty
                rule_body = ' | '.join(non_empty + [''])
            elif empty_count > 0:
                # Only epsilon
                rule_body = ''
            else:
                rule_body = ' | '.join(non_empty)
            
            lines.append(f'{rule_name}: {rule_body}')
        
        # Add a blank line before terminals
        lines.append('')
        
        # Generate terminal definitions
        for terminal_name in terminals_used:
            lark_name = self._terminal_rules.get(terminal_name)
            if lark_name:
                if terminal_name == 'id':
                    lines.append(f'{lark_name}: /[a-zA-Z_][a-zA-Z0-9_]*/')
                elif terminal_name == 'number':
                    lines.append(f'{lark_name}: /[0-9]+\\.?[0-9]*/')
                else:
                    # Escape the terminal for regex
                    escaped = self._escape_terminal_value(terminal_name)
                    lines.append(f'{lark_name}: "{terminal_name}"')
        
        # Add whitespace handling
        lines.append('')
        lines.append('%import common.WS')
        lines.append('%ignore WS')
        
        return '\n'.join(lines)


class LarkTreeNode:
    """Node in the derivation tree (compatible with existing TreeNode)"""
    
    def __init__(self, symbol: str, children: List["LarkTreeNode"] = None, 
                 token_value: str = None, is_terminal: bool = False):
        self.symbol = symbol
        self.children = children or []
        self.token_value = token_value
        self._is_terminal = is_terminal
    
    def is_terminal(self) -> bool:
        return self._is_terminal
    
    def add_child(self, child: "LarkTreeNode"):
        self.children.append(child)
    
    def to_simple_text(self, indent: int = 0) -> str:
        """Simple indented text representation"""
        result = "  " * indent + self.symbol
        if self.token_value:
            result += f" ('{self.token_value}')"
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
        if self.token_value:
            result["value"] = self.token_value
        return result
    
    def to_mermaid(self) -> str:
        """Convert tree to Mermaid diagram format"""
        lines = ["graph TD"]
        node_counter = [0]
        
        def add_node(node: "LarkTreeNode", parent_id: Optional[str] = None) -> str:
            node_id = f"N{node_counter[0]}"
            node_counter[0] += 1
            
            if node.is_terminal():
                if node.token_value:
                    # Escape quotes for mermaid
                    safe_value = node.token_value.replace('"', "'")
                    label = f'{node.symbol}: "{safe_value}"'
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
        import json
        
        def convert(node: "LarkTreeNode") -> dict:
            result = {"name": node.symbol}
            if node.token_value:
                result["value"] = node.token_value
                result["type"] = "terminal"
            else:
                result["type"] = "nonterminal"
            if node.children:
                result["children"] = [convert(child) for child in node.children]
            return result
        
        return json.dumps(convert(self), indent=2)


class LarkTreeBuilder:
    """Builds derivation trees using Lark parser"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.converter = LarkGrammarConverter(grammar)
        self.lark_grammar = None
        self.parser = None
        self._reverse_terminal_map: Dict[str, str] = {}
    
    def _build_parser(self) -> None:
        """Build the Lark parser from the grammar"""
        self.lark_grammar = self.converter.convert()
        
        # Build reverse map: Lark terminal name -> original terminal name
        self._reverse_terminal_map = {v: k for k, v in self.converter._terminal_rules.items()}
        
        # Get the start rule (first non-terminal, converted to lowercase)
        start_rule = self.converter._sanitize_rule_name(str(self.grammar.start_symbol))
        
        try:
            self.parser = Lark(
                self.lark_grammar,
                start=start_rule,
                parser='lalr',  # Use LALR parser for efficiency
                ambiguity='explicit'  # Show ambiguities if any
            )
        except LarkError as e:
            # Try with earley parser which is more permissive
            try:
                self.parser = Lark(
                    self.lark_grammar,
                    start=start_rule,
                    parser='earley',
                    ambiguity='resolve'
                )
            except LarkError:
                raise ValueError(f"Could not create Lark parser: {e}")
    
    def _convert_lark_tree(self, lark_tree) -> LarkTreeNode:
        """Convert a Lark Tree/Token to our LarkTreeNode format"""
        if isinstance(lark_tree, LarkToken):
            # It's a terminal token
            original_name = self._reverse_terminal_map.get(lark_tree.type, lark_tree.type)
            return LarkTreeNode(
                symbol=original_name,
                token_value=str(lark_tree.value),
                is_terminal=True
            )
        elif isinstance(lark_tree, Tree):
            # It's a non-terminal
            # Convert rule name back to original format
            symbol = lark_tree.data
            # Try to find original non-terminal name
            for nt in self.grammar.non_terminals:
                if self.converter._sanitize_rule_name(str(nt)) == symbol:
                    symbol = str(nt)
                    break
            
            node = LarkTreeNode(symbol=symbol, is_terminal=False)
            
            for child in lark_tree.children:
                if child is not None:  # Skip None children (from epsilon)
                    child_node = self._convert_lark_tree(child)
                    node.add_child(child_node)
            
            # If no children, it might be epsilon
            if not node.children and not lark_tree.children:
                epsilon_node = LarkTreeNode(symbol="ε", is_terminal=True)
                node.add_child(epsilon_node)
            
            return node
        else:
            # Handle other types (shouldn't happen normally)
            return LarkTreeNode(symbol=str(lark_tree), is_terminal=True)
    
    def parse(self, input_text: str) -> Tuple[Optional[LarkTreeNode], List[str]]:
        """
        Parse input text and return (tree, errors)
        """
        errors = []
        
        if not input_text.strip():
            errors.append("No input provided")
            return None, errors
        
        try:
            if self.parser is None:
                self._build_parser()
            
            lark_tree = self.parser.parse(input_text)
            tree = self._convert_lark_tree(lark_tree)
            
            return tree, errors
            
        except UnexpectedInput as e:
            errors.append(f"Parse error at position {e.pos_in_stream}: {str(e)}")
            return None, errors
        except LarkError as e:
            errors.append(f"Lark error: {str(e)}")
            return None, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return None, errors
    
    def get_lark_grammar(self) -> str:
        """Return the generated Lark grammar (for debugging)"""
        if self.lark_grammar is None:
            self._build_parser()
        return self.lark_grammar


def build_derivation_tree_lark(grammar_text: str, input_text: str) -> dict:
    """
    Build a derivation tree using Lark parser.
    Returns a dictionary with all results.
    """
    try:
        grammar = GrammarParser.parse(grammar_text)
        validation_errors = grammar.validate()
        
        if validation_errors:
            return {
                "success": False,
                "errors": validation_errors,
                "tree": None,
                "derivation_steps": []
            }
        
        builder = LarkTreeBuilder(grammar)
        tree, errors = builder.parse(input_text)
        
        if errors:
            return {
                "success": False,
                "errors": errors,
                "tree": None,
                "lark_grammar": builder.get_lark_grammar() if builder.lark_grammar else None,
                "derivation_steps": []
            }
        
        return {
            "success": True,
            "errors": [],
            "tree": tree.to_dict() if tree else None,
            "tree_text": tree.to_simple_text() if tree else "",
            "tree_mermaid": tree.to_mermaid() if tree else "",
            "tree_d3": tree.to_d3_json() if tree else "",
            "lark_grammar": builder.get_lark_grammar(),
            "derivation_steps": []  # Lark doesn't provide step-by-step derivation
        }
        
    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)],
            "tree": None,
            "derivation_steps": []
        }
