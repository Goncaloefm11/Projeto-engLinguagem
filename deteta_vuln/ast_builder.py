"""
AST Builder - Converts parse trees to Abstract Syntax Trees
Performs syntax analysis and builds semantic representation
"""

from typing import Optional, List, Dict, Any
from lark import Tree, Token
from ast_nodes import *


class ASTBuilder:
    """Builds Abstract Syntax Tree from parse tree"""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def error(self, message: str):
        """Record a semantic error"""
        self.errors.append(message)
    
    def build(self, parse_tree: Tree) -> Optional[Program]:
        """Build AST from parse tree"""
        try:
            statements = []
            for child in parse_tree.children:
                if isinstance(child, Tree):
                    stmt = self.build_statement(child)
                    if stmt:
                        statements.append(stmt)
            
            return Program(statements)
        except Exception as e:
            self.error(f"Error building AST: {str(e)}")
            return None
    
    def build_statement(self, node: Tree) -> Optional[ASTNode]:
        """Build a statement AST node"""
        if node.data == 'instruction':
            return self.build_statement(node.children[0])
        
        elif node.data == 'assignment':
            return self.build_assignment(node)
        
        elif node.data == 'conditional':
            return self.build_if_statement(node)
        
        elif node.data == 'while_loop':
            return self.build_while_statement(node)
        
        elif node.data == 'do_while_loop':
            return self.build_do_while_statement(node)
        
        elif node.data == 'for_loop':
            return self.build_for_statement(node)
        
        elif node.data == 'block':
            return self.build_block(node)
        
        elif node.data == 'print_stmt':
            return self.build_print_statement(node)
        
        elif node.data == 'exec_stmt':
            return self.build_exec_statement(node)
        
        elif node.data == 'try_catch_stmt':
            return self.build_try_statement(node)
        
        elif node.data == 'throw_stmt':
            return self.build_throw_statement(node)
        
        elif node.data == 'return_stmt':
            return self.build_return_statement(node)
        
        elif node.data == 'break_stmt':
            return BreakStatement()
        
        elif node.data == 'continue_stmt':
            return ContinueStatement()
        
        else:
            return None
    
    def build_assignment(self, node: Tree) -> Optional[Assignment]:
        """Build assignment statement"""
        if len(node.children) > 0:
            assign_expr = node.children[0]
            if isinstance(assign_expr, Tree) and assign_expr.data == 'assign_expr':
                target = assign_expr.children[0].value
                value = self.build_expression(assign_expr.children[1])
                return Assignment(target, value)
        return None
    
    def build_if_statement(self, node: Tree) -> Optional[IfStatement]:
        """Build if statement"""
        condition = self.build_expression(node.children[0])
        then_block = self.build_block_statements(node.children[1])
        
        else_block = None
        if len(node.children) > 2:
            else_block = self.build_block_statements(node.children[2])
        
        return IfStatement(condition, then_block, else_block)
    
    def build_while_statement(self, node: Tree) -> Optional[WhileStatement]:
        """Build while statement"""
        condition = self.build_expression(node.children[0])
        body = self.build_block_statements(node.children[1])
        return WhileStatement(condition, body)
    
    def build_do_while_statement(self, node: Tree) -> Optional[DoWhileStatement]:
        """Build do-while statement"""
        body = self.build_block_statements(node.children[0])
        condition = self.build_expression(node.children[1])
        return DoWhileStatement(body, condition)
    
    def build_for_statement(self, node: Tree) -> Optional[ForStatement]:
        """Build for statement"""
        init = None
        if node.children[0]:
            init = self.build_statement(node.children[0])
        
        condition = None
        if node.children[1]:
            condition = self.build_expression(node.children[1])
        
        update = None
        if node.children[2]:
            update = self.build_statement(node.children[2])
        
        body = self.build_block_statements(node.children[3])
        return ForStatement(init, condition, update, body)
    
    def build_block(self, node: Tree) -> Optional[Block]:
        """Build block statement"""
        statements = self.build_block_statements(node)
        return Block(statements)
    
    def build_block_statements(self, node: Tree) -> List[ASTNode]:
        """Build list of statements from block"""
        statements = []
        
        if isinstance(node, Tree):
            for child in node.children:
                if isinstance(child, Tree):
                    # Skip tokens, process only trees
                    if child.data == 'instruction':
                        stmt = self.build_statement(child)
                        if stmt:
                            statements.append(stmt)
        
        return statements
    
    def build_print_statement(self, node: Tree) -> Optional[PrintStatement]:
        """Build print statement"""
        args = []
        for child in node.children:
            expr = self.build_expression(child)
            if expr:
                args.append(expr)
        return PrintStatement(args)
    
    def build_exec_statement(self, node: Tree) -> Optional[ExecStatement]:
        """Build exec statement"""
        expr = self.build_expression(node.children[0])
        return ExecStatement(expr)
    
    def build_try_statement(self, node: Tree) -> Optional[TryStatement]:
        """Build try-catch statement"""
        try_block = self.build_block_statements(node.children[0])
        
        catch_var = None
        catch_block = []
        
        if len(node.children) > 1:
            # Check if second child is a variable token
            if isinstance(node.children[1], Token):
                catch_var = node.children[1].value
                catch_block = self.build_block_statements(node.children[2])
            else:
                catch_block = self.build_block_statements(node.children[1])
        
        return TryStatement(try_block, catch_var, catch_block)
    
    def build_throw_statement(self, node: Tree) -> Optional[ThrowStatement]:
        """Build throw statement"""
        expr = self.build_expression(node.children[0])
        return ThrowStatement(expr)
    
    def build_return_statement(self, node: Tree) -> Optional[ReturnStatement]:
        """Build return statement"""
        value = None
        if len(node.children) > 0:
            value = self.build_expression(node.children[0])
        return ReturnStatement(value)
    
    def build_expression(self, node) -> Optional[ASTNode]:
        """Build expression AST node"""
        if isinstance(node, Token):
            if node.type == 'SIGNED_NUMBER':
                return NumberLiteral(float(node.value))
            elif node.type == 'ESCAPED_STRING':
                # Remove quotes
                value = node.value.strip('"\'')
                return StringLiteral(value)
            elif node.type == 'VAR':
                return Identifier(node.value)
            else:
                return Identifier(node.value)
        
        if not isinstance(node, Tree):
            return None
        
        # Handle logical operations
        if node.data == 'logical_or':
            return self.build_binary_op(node, 'or')
        
        elif node.data == 'logical_and':
            return self.build_binary_op(node, 'and')
        
        elif node.data == 'comparison':
            return self.build_comparison(node)
        
        elif node.data == 'sum':
            return self.build_arithmetic_op(node, ['+', '-'])
        
        elif node.data == 'product':
            return self.build_arithmetic_op(node, ['*', '/', '%'])
        
        elif node.data == 'atom':
            return self.build_atom(node)
        
        elif node.data == 'list':
            return self.build_list_literal(node)
        
        elif node.data == 'dict':
            return self.build_dict_literal(node)
        
        else:
            # Try to handle as expression tree with single child
            if len(node.children) == 1:
                return self.build_expression(node.children[0])
            
            return None
    
    def build_binary_op(self, node: Tree, default_op: str) -> Optional[BinaryOp]:
        """Build binary operation"""
        if len(node.children) < 2:
            return self.build_expression(node.children[0]) if len(node.children) > 0 else None
        
        left = self.build_expression(node.children[0])
        
        for i in range(1, len(node.children)):
            child = node.children[i]
            
            if isinstance(child, Token):
                op = child.value
            else:
                op = default_op
                right = self.build_expression(child)
                left = BinaryOp(left, op, right)
                continue
            
            if i + 1 < len(node.children):
                right = self.build_expression(node.children[i + 1])
                left = BinaryOp(left, op, right)
        
        return left if isinstance(left, BinaryOp) else left
    
    def build_comparison(self, node: Tree) -> Optional[ASTNode]:
        """Build comparison operation"""
        left = self.build_expression(node.children[0])
        
        for i in range(1, len(node.children), 2):
            if i + 1 < len(node.children):
                op = node.children[i].value if isinstance(node.children[i], Token) else '=='
                right = self.build_expression(node.children[i + 1])
                left = BinaryOp(left, op, right)
        
        return left
    
    def build_arithmetic_op(self, node: Tree, operators: List[str]) -> Optional[ASTNode]:
        """Build arithmetic operation"""
        left = self.build_expression(node.children[0])
        
        for i in range(1, len(node.children), 2):
            if i + 1 < len(node.children):
                op_token = node.children[i]
                op = op_token.value if isinstance(op_token, Token) else operators[0]
                right = self.build_expression(node.children[i + 1])
                left = BinaryOp(left, op, right)
        
        return left
    
    def build_atom(self, node: Tree) -> Optional[ASTNode]:
        """Build atomic expression"""
        if len(node.children) == 0:
            return None
        
        child = node.children[0]
        
        if isinstance(child, Tree):
            # Could be a function call, index access, etc.
            return self.build_expression(child)
        
        # Token
        if child.type == 'NUMBER':
            return NumberLiteral(float(child.value))
        
        elif child.type == 'STRING':
            value = child.value.strip('"\'')
            return StringLiteral(value)
        
        elif child.type in ('TRUE', 'FALSE'):
            return BooleanLiteral(child.type == 'TRUE')
        
        elif child.type == 'VAR':
            return Identifier(child.value)
        
        else:
            return Identifier(str(child))
    
    def build_list_literal(self, node: Tree) -> Optional[ListLiteral]:
        """Build list literal"""
        elements = []
        
        for child in node.children:
            if isinstance(child, Tree):
                expr = self.build_expression(child)
                if expr:
                    elements.append(expr)
        
        return ListLiteral(elements)
    
    def build_dict_literal(self, node: Tree) -> Optional[DictLiteral]:
        """Build dictionary literal"""
        pairs = []
        
        for child in node.children:
            if isinstance(child, Tree) and child.data == 'pair':
                if len(child.children) == 2:
                    key = self.build_expression(child.children[0])
                    value = self.build_expression(child.children[1])
                    if key and value:
                        pairs.append((key, value))
        
        return DictLiteral(pairs)
