"""
Grammar Playground - Core Module
"""

from .grammar import (
    Grammar,
    Symbol,
    Production,
    SymbolType,
    GrammarParser,
    EPSILON,
    END_MARKER
)
from .ll1_analyzer import (
    LL1Analyzer,
    LL1Table,
    Conflict
)
from .parser_generator import (
    RecursiveDescentGenerator,
    # TableDrivenGenerator  # Removido da API pública
)
from .derivation_tree import (
    TreeNode,
    Token,
    DerivationTreeBuilder,
    SimpleTokenizer,
    build_derivation_tree,
    ParseError
)
from .lark_parser import (
    LarkTreeBuilder,
    LarkTreeNode,
    LarkGrammarConverter,
    build_derivation_tree_lark
)

__all__ = [
    'Grammar',
    'Symbol',
    'Production',
    'SymbolType',
    'GrammarParser',
    'EPSILON',
    'END_MARKER',
    'LL1Analyzer',
    'LL1Table',
    'Conflict',
    'RecursiveDescentGenerator',
    # 'TableDrivenGenerator',  # Removido da API pública
    'TreeNode',
    'Token',
    'DerivationTreeBuilder',
    'SimpleTokenizer',
    'build_derivation_tree',
    'ParseError',
    'LarkTreeBuilder',
    'LarkTreeNode',
    'LarkGrammarConverter',
    'build_derivation_tree_lark'
]
