"""
Parse Tree Builder - Generates parse trees using Lark
Builds both textual and graphical representations of derivation trees
"""

from lark import Lark, Tree, Token, Transformer, v_args
from typing import Dict, List, Optional, Union, Tuple
import json


class ParseTreeBuilder:
    """Builds parse trees for sentences using a given grammar"""
    
    def __init__(self, grammar_dict: Dict[str, List[List[str]]]):
        """Initialize with grammar definition"""
        self.grammar_dict = grammar_dict
        self.lark_grammar = self._convert_to_lark_grammar(grammar_dict)
        
        try:
            self.parser = Lark(
                self.lark_grammar,
                start='start' if 'start' in grammar_dict else next(iter(grammar_dict.keys())),
                parser='earley'  # Use Earley parser for flexibility
            )
        except Exception as e:
            self.parser = None
            self.error = str(e)
    
    def _convert_to_lark_grammar(self, grammar_dict: Dict[str, List[List[str]]]) -> str:
        """Convert grammar dict to Lark format"""
        start_symbol = next(iter(grammar_dict.keys()))
        rules = []
        
        for nonterminal, productions in grammar_dict.items():
            alternatives = []
            for i, body in enumerate(productions):
                if not body:  # Epsilon
                    alternatives.append('') 
                else:
                    # Convert symbols to valid Lark identifiers
                    symbols = []
                    for symbol in body:
                        # Add quotes around terminals if needed
                        if symbol[0].islower() or not symbol[0].isalpha():
                            symbols.append(f'"{symbol}"')
                        else:
                            symbols.append(symbol)
                    alternatives.append(' '.join(symbols))
            
            # Create rule
            rule = f'{nonterminal.lower()}: {" | ".join(alternatives)}'
            rules.append(rule)
        
        # Update terminals to be recognized
        rules.append('%import common.WS')
        rules.append('%ignore WS')
        
        return '\n'.join(rules)
    
    def parse(self, input_text: str) -> Optional[Tuple[bool, Union[Tree, str]]]:
        """
        Parse input text and return parse tree or error message
        Returns: (success, result) where result is Tree or error string
        """
        if not self.parser:
            return False, f"Parser error: {self.error}"
        
        try:
            tree = self.parser.parse(input_text)
            return True, tree
        except Exception as e:
            return False, str(e)
    
    def tree_to_dict(self, tree: Tree) -> Dict:
        """Convert parse tree to dictionary representation"""
        return {
            'label': tree.data,
            'children': [
                self.tree_to_dict(child) if isinstance(child, Tree)
                else {'label': f'"{child.value}"', 'terminal': True}
                for child in tree.children
            ]
        }
    
    def tree_to_string(self, tree: Union[Tree, Token], indent: int = 0) -> str:
        """Convert parse tree to pretty-printed string"""
        result = ""
        
        if isinstance(tree, Token):
            return " " * indent + f'"{tree.value}"'
        
        if isinstance(tree, Tree):
            result += " " * indent + tree.data + "\n"
            for child in tree.children:
                result += self.tree_to_string(child, indent + 2) + "\n"
        
        return result
    
    def tree_to_levels(self, tree: Union[Tree, Token]) -> List[List[Dict]]:
        """Convert tree to level-based representation for visualization"""
        def process_node(node, level=0):
            if isinstance(node, Token):
                return {
                    'label': f'"{node.value}"',
                    'level': level,
                    'terminal': True,
                    'children': []
                }
            
            children = []
            if isinstance(node, Tree):
                for child in node.children:
                    children.append(process_node(child, level + 1))
            
            return {
                'label': node.data if isinstance(node, Tree) else str(node),
                'level': level,
                'terminal': isinstance(node, Token),
                'children': children
            }
        
        # Group by levels
        def collect_levels(node, level=0, levels=None):
            if levels is None:
                levels = {}
            
            if level not in levels:
                levels[level] = []
            
            if isinstance(node, Token):
                levels[level].append({
                    'label': f'"{node.value}"',
                    'terminal': True
                })
            elif isinstance(node, Tree):
                levels[level].append({
                    'label': node.data,
                    'terminal': False
                })
                for child in node.children:
                    collect_levels(child, level + 1, levels)
            
            return levels
        
        levels_dict = collect_levels(tree)
        return [levels_dict[i] for i in sorted(levels_dict.keys())]


class TreeVisualizer:
    """Generates visualization data for parse trees"""
    
    @staticmethod
    def tree_to_mermaid(tree: Tree) -> str:
        """Convert parse tree to Mermaid diagram format"""
        lines = ['graph TD']
        node_counter = [0]
        
        def process_node(node, parent_id=None):
            node_id = f"N{node_counter[0]}"
            node_counter[0] += 1
            
            if isinstance(node, Token):
                label = f'"{node.value}"'
                lines.append(f'{node_id}["{label}"]')
            elif isinstance(node, Tree):
                lines.append(f'{node_id}["{node.data}"]')
                for child in node.children:
                    child_id = process_node(child, node_id)
                    lines.append(f'{node_id} --> {child_id}')
            
            return node_id
        
        process_node(tree)
        return '\n'.join(lines)
    
    @staticmethod
    def tree_to_json(tree: Tree) -> str:
        """Convert parse tree to JSON representation"""
        def process_node(node):
            if isinstance(node, Token):
                return {
                    'type': 'terminal',
                    'value': node.value
                }
            elif isinstance(node, Tree):
                return {
                    'type': 'nonterminal',
                    'rule': node.data,
                    'children': [process_node(child) for child in node.children]
                }
        
        return json.dumps(process_node(tree), indent=2)
    
    @staticmethod
    def tree_to_svg(tree: Tree, title: str = "Parse Tree") -> str:
        """Generate SVG representation of parse tree (simplified)"""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">',
            f'<text x="10" y="20" font-size="16" font-weight="bold">{title}</text>',
        ]
        
        # Simple text-based SVG representation
        y = 50
        lines.append(f'<text x="20" y="{y}" font-family="monospace" font-size="12">')
        tree_str = TreeVisualizer._tree_to_text(tree, 0)
        for line in tree_str.split('\n'):
            lines.append(f'<tspan x="20" dy="1.2em">{line}</tspan>')
        lines.append('</text>')
        lines.append('</svg>')
        
        return '\n'.join(lines)
    
    @staticmethod
    def _tree_to_text(node, indent=0):
        result = ""
        prefix = "  " * indent
        
        if isinstance(node, Token):
            result += f'{prefix}"{node.value}"\n'
        elif isinstance(node, Tree):
            result += f'{prefix}{node.data}\n'
            for child in node.children:
                result += TreeVisualizer._tree_to_text(child, indent + 1)
        
        return result
