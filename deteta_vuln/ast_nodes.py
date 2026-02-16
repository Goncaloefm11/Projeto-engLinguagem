"""
Abstract Syntax Tree (AST) Node Definitions
Defines the structure of the abstract syntax tree for program representation
"""

from typing import List, Optional, Any, Dict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class ASTNode(ABC):
    """Base class for all AST nodes"""
    
    @abstractmethod
    def __repr__(self) -> str:
        """String representation of node"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        pass


# ============= LITERALS =============

@dataclass
class NumberLiteral(ASTNode):
    """Numeric literal (e.g., 42, 3.14)"""
    value: float
    
    def __repr__(self) -> str:
        return f"Number({self.value})"
    
    def to_dict(self) -> Dict:
        return {'type': 'NumberLiteral', 'value': self.value}


@dataclass
class StringLiteral(ASTNode):
    """String literal (e.g., "hello")"""
    value: str
    
    def __repr__(self) -> str:
        return f'String({repr(self.value)})'
    
    def to_dict(self) -> Dict:
        return {'type': 'StringLiteral', 'value': self.value}


@dataclass
class BooleanLiteral(ASTNode):
    """Boolean literal (true/false)"""
    value: bool
    
    def __repr__(self) -> str:
        return f"Boolean({self.value})"
    
    def to_dict(self) -> Dict:
        return {'type': 'BooleanLiteral', 'value': self.value}


@dataclass
class Identifier(ASTNode):
    """Identifier (variable name)"""
    name: str
    
    def __repr__(self) -> str:
        return f"Identifier({self.name})"
    
    def to_dict(self) -> Dict:
        return {'type': 'Identifier', 'name': self.name}


# ============= COLLECTIONS =============

@dataclass
class ListLiteral(ASTNode):
    """List literal [1, 2, 3]"""
    elements: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"List({self.elements})"
    
    def to_dict(self) -> Dict:
        return {'type': 'ListLiteral', 'elements': [e.to_dict() for e in self.elements]}


@dataclass
class DictLiteral(ASTNode):
    """Dictionary literal {"key": value}"""
    pairs: List[tuple]  # List of (key, value) tuples
    
    def __repr__(self) -> str:
        return f"Dict({self.pairs})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'DictLiteral',
            'pairs': [[k.to_dict(), v.to_dict()] for k, v in self.pairs]
        }


# ============= EXPRESSIONS =============

@dataclass
class BinaryOp(ASTNode):
    """Binary operation (e.g., a + b)"""
    left: ASTNode
    operator: str
    right: ASTNode
    
    def __repr__(self) -> str:
        return f"BinaryOp({self.left} {self.operator} {self.right})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'BinaryOp',
            'operator': self.operator,
            'left': self.left.to_dict(),
            'right': self.right.to_dict()
        }


@dataclass
class UnaryOp(ASTNode):
    """Unary operation (e.g., -x, not x)"""
    operator: str
    operand: ASTNode
    
    def __repr__(self) -> str:
        return f"UnaryOp({self.operator} {self.operand})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'UnaryOp',
            'operator': self.operator,
            'operand': self.operand.to_dict()
        }


@dataclass
class FunctionCall(ASTNode):
    """Function call (e.g., print(x))"""
    name: str
    arguments: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"Call({self.name}({', '.join(str(a) for a in self.arguments)}))"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'FunctionCall',
            'name': self.name,
            'arguments': [a.to_dict() for a in self.arguments]
        }


@dataclass
class IndexAccess(ASTNode):
    """Array/list index access (e.g., arr[0])"""
    object: ASTNode
    index: ASTNode
    
    def __repr__(self) -> str:
        return f"Index({self.object}[{self.index}])"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'IndexAccess',
            'object': self.object.to_dict(),
            'index': self.index.to_dict()
        }


@dataclass
class MemberAccess(ASTNode):
    """Member access (e.g., obj.member)"""
    object: ASTNode
    member: str
    
    def __repr__(self) -> str:
        return f"Member({self.object}.{self.member})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'MemberAccess',
            'object': self.object.to_dict(),
            'member': self.member
        }


# ============= STATEMENTS =============

@dataclass
class Assignment(ASTNode):
    """Variable assignment (e.g., x = 10)"""
    target: str
    value: ASTNode
    
    def __repr__(self) -> str:
        return f"Assign({self.target} = {self.value})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'Assignment',
            'target': self.target,
            'value': self.value.to_dict()
        }


@dataclass
class IfStatement(ASTNode):
    """If statement"""
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]] = None
    
    def __repr__(self) -> str:
        return f"If({self.condition})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'IfStatement',
            'condition': self.condition.to_dict(),
            'then_block': [stmt.to_dict() for stmt in self.then_block],
            'else_block': [stmt.to_dict() for stmt in self.else_block] if self.else_block else None
        }


@dataclass
class WhileStatement(ASTNode):
    """While loop"""
    condition: ASTNode
    body: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"While({self.condition})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'WhileStatement',
            'condition': self.condition.to_dict(),
            'body': [stmt.to_dict() for stmt in self.body]
        }


@dataclass
class DoWhileStatement(ASTNode):
    """Do-while loop"""
    body: List[ASTNode]
    condition: ASTNode
    
    def __repr__(self) -> str:
        return f"DoWhile()"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'DoWhileStatement',
            'body': [stmt.to_dict() for stmt in self.body],
            'condition': self.condition.to_dict()
        }


@dataclass
class ForStatement(ASTNode):
    """For loop"""
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"For({self.init}; {self.condition}; {self.update})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'ForStatement',
            'init': self.init.to_dict() if self.init else None,
            'condition': self.condition.to_dict() if self.condition else None,
            'update': self.update.to_dict() if self.update else None,
            'body': [stmt.to_dict() for stmt in self.body]
        }


@dataclass
class Block(ASTNode):
    """Code block { ... }"""
    statements: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"Block({len(self.statements)} stmts)"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'Block',
            'statements': [stmt.to_dict() for stmt in self.statements]
        }


@dataclass
class ReturnStatement(ASTNode):
    """Return statement"""
    value: Optional[ASTNode] = None
    
    def __repr__(self) -> str:
        return f"Return({self.value})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'ReturnStatement',
            'value': self.value.to_dict() if self.value else None
        }


@dataclass
class BreakStatement(ASTNode):
    """Break statement"""
    
    def __repr__(self) -> str:
        return "Break"
    
    def to_dict(self) -> Dict:
        return {'type': 'BreakStatement'}


@dataclass
class ContinueStatement(ASTNode):
    """Continue statement"""
    
    def __repr__(self) -> str:
        return "Continue"
    
    def to_dict(self) -> Dict:
        return {'type': 'ContinueStatement'}


@dataclass
class PrintStatement(ASTNode):
    """Print statement"""
    arguments: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"Print({', '.join(str(a) for a in self.arguments)})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'PrintStatement',
            'arguments': [a.to_dict() for a in self.arguments]
        }


@dataclass
class ExecStatement(ASTNode):
    """Exec statement"""
    expression: ASTNode
    
    def __repr__(self) -> str:
        return f"Exec({self.expression})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'ExecStatement',
            'expression': self.expression.to_dict()
        }


@dataclass
class TryStatement(ASTNode):
    """Try-catch statement"""
    try_block: List[ASTNode]
    catch_var: Optional[str]
    catch_block: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"Try-Catch({self.catch_var})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'TryStatement',
            'try_block': [stmt.to_dict() for stmt in self.try_block],
            'catch_var': self.catch_var,
            'catch_block': [stmt.to_dict() for stmt in self.catch_block]
        }


@dataclass
class ThrowStatement(ASTNode):
    """Throw statement"""
    expression: ASTNode
    
    def __repr__(self) -> str:
        return f"Throw({self.expression})"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'ThrowStatement',
            'expression': self.expression.to_dict()
        }


# ============= PROGRAM =============

@dataclass
class Program(ASTNode):
    """Root node representing entire program"""
    statements: List[ASTNode]
    
    def __repr__(self) -> str:
        return f"Program({len(self.statements)} statements)"
    
    def to_dict(self) -> Dict:
        return {
            'type': 'Program',
            'statements': [stmt.to_dict() for stmt in self.statements]
        }
