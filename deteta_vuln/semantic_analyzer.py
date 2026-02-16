"""
Semantic Analyzer & Parser Executor
Executes the AST and performs semantic analysis
"""

from typing import Any, Dict, List, Optional
import sys
from ast_nodes import *


class ExecutionError(Exception):
    """Runtime execution error"""
    pass


class BreakException(Exception):
    """Break flow control"""
    pass


class ContinueException(Exception):
    """Continue flow control"""
    pass


class ReturnException(Exception):
    """Return flow control"""
    def __init__(self, value):
        self.value = value


class Environment:
    """Variable environment/scope"""
    
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any):
        """Define variable in current scope"""
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        """Get variable value, looking up scope chain"""
        if name in self.variables:
            return self.variables[name]
        
        if self.parent:
            return self.parent.get(name)
        
        raise ExecutionError(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any):
        """Set variable value, looking up scope chain"""
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            # Create in current scope if not found
            self.variables[name] = value
    
    def exists(self, name: str) -> bool:
        """Check if variable exists"""
        if name in self.variables:
            return True
        return self.parent and self.parent.exists(name)


class Parser:
    """Parser/Interpreter for executing AST"""
    
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.errors: List[str] = []
        self.output: List[str] = []  # Captured output from print()
    
    def error(self, message: str):
        """Record execution error"""
        self.errors.append(message)
    
    def execute(self, program: Program) -> Dict[str, Any]:
        """Execute AST program"""
        try:
            result = self.execute_program(program)
            return {
                'success': len(self.errors) == 0,
                'output': self.output,
                'errors': self.errors,
                'result': result
            }
        except ExecutionError as e:
            self.error(str(e))
            return {
                'success': False,
                'output': self.output,
                'errors': self.errors,
                'result': None
            }
    
    def execute_program(self, node: Program) -> Any:
        """Execute program node"""
        result = None
        
        for statement in node.statements:
            result = self.execute_statement(statement)
        
        return result
    
    def execute_statement(self, node: ASTNode) -> Any:
        """Execute a statement"""
        if isinstance(node, Assignment):
            return self.execute_assignment(node)
        
        elif isinstance(node, IfStatement):
            return self.execute_if_statement(node)
        
        elif isinstance(node, WhileStatement):
            return self.execute_while_statement(node)
        
        elif isinstance(node, DoWhileStatement):
            return self.execute_do_while_statement(node)
        
        elif isinstance(node, ForStatement):
            return self.execute_for_statement(node)
        
        elif isinstance(node, Block):
            return self.execute_block(node)
        
        elif isinstance(node, PrintStatement):
            return self.execute_print_statement(node)
        
        elif isinstance(node, ExecStatement):
            return self.execute_exec_statement(node)
        
        elif isinstance(node, TryStatement):
            return self.execute_try_statement(node)
        
        elif isinstance(node, ThrowStatement):
            return self.execute_throw_statement(node)
        
        elif isinstance(node, ReturnStatement):
            return self.execute_return_statement(node)
        
        elif isinstance(node, BreakStatement):
            raise BreakException()
        
        elif isinstance(node, ContinueStatement):
            raise ContinueException()
        
        else:
            return self.evaluate_expression(node)
    
    def execute_assignment(self, node: Assignment) -> Any:
        """Execute assignment statement"""
        value = self.evaluate_expression(node.value)
        self.current_env.set(node.target, value)
        return value
    
    def execute_if_statement(self, node: IfStatement) -> Any:
        """Execute if statement"""
        condition = self.evaluate_expression(node.condition)
        
        if self.is_truthy(condition):
            return self.execute_block_statements(node.then_block)
        elif node.else_block:
            return self.execute_block_statements(node.else_block)
        
        return None
    
    def execute_while_statement(self, node: WhileStatement) -> Any:
        """Execute while loop"""
        result = None
        
        try:
            while self.is_truthy(self.evaluate_expression(node.condition)):
                try:
                    result = self.execute_block_statements(node.body)
                except ContinueException:
                    continue
        except BreakException:
            pass
        
        return result
    
    def execute_do_while_statement(self, node: DoWhileStatement) -> Any:
        """Execute do-while loop"""
        result = None
        
        try:
            while True:
                try:
                    result = self.execute_block_statements(node.body)
                except ContinueException:
                    pass
                
                if not self.is_truthy(self.evaluate_expression(node.condition)):
                    break
        except BreakException:
            pass
        
        return result
    
    def execute_for_statement(self, node: ForStatement) -> Any:
        """Execute for loop"""
        # Create new scope for loop variable
        new_env = Environment(self.current_env)
        old_env = self.current_env
        self.current_env = new_env
        
        result = None
        
        try:
            # Initialize
            if node.init:
                self.execute_statement(node.init)
            
            # Loop
            try:
                while True:
                    # Check condition
                    if node.condition:
                        if not self.is_truthy(self.evaluate_expression(node.condition)):
                            break
                    
                    # Execute body
                    try:
                        result = self.execute_block_statements(node.body)
                    except ContinueException:
                        pass
                    
                    # Update
                    if node.update:
                        self.execute_statement(node.update)
            except BreakException:
                pass
        finally:
            self.current_env = old_env
        
        return result
    
    def execute_block(self, node: Block) -> Any:
        """Execute code block"""
        # Create new scope
        new_env = Environment(self.current_env)
        old_env = self.current_env
        self.current_env = new_env
        
        try:
            return self.execute_block_statements(node.statements)
        finally:
            self.current_env = old_env
    
    def execute_block_statements(self, statements: List[ASTNode]) -> Any:
        """Execute list of statements"""
        result = None
        
        for statement in statements:
            result = self.execute_statement(statement)
        
        return result
    
    def execute_print_statement(self, node: PrintStatement) -> Any:
        """Execute print statement"""
        for arg in node.arguments:
            value = self.evaluate_expression(arg)
            output = self.format_value(value)
            self.output.append(output)
        
        return None
    
    def execute_exec_statement(self, node: ExecStatement) -> Any:
        """Execute exec statement"""
        # This would execute code - be careful with security!
        expr = self.evaluate_expression(node.expression)
        
        if isinstance(expr, str):
            try:
                # Use eval with restricted environment
                result = eval(expr, {"__builtins__": {}}, self.current_env.variables)
                return result
            except Exception as e:
                raise ExecutionError(f"Exec error: {str(e)}")
        
        return expr
    
    def execute_try_statement(self, node: TryStatement) -> Any:
        """Execute try-catch statement"""
        result = None
        
        try:
            result = self.execute_block_statements(node.try_block)
        except Exception as e:
            if node.catch_block:
                if node.catch_var:
                    self.current_env.define(node.catch_var, str(e))
                result = self.execute_block_statements(node.catch_block)
            else:
                raise
        
        return result
    
    def execute_throw_statement(self, node: ThrowStatement) -> Any:
        """Execute throw statement"""
        value = self.evaluate_expression(node.expression)
        raise ExecutionError(str(value))
    
    def execute_return_statement(self, node: ReturnStatement) -> Any:
        """Execute return statement"""
        value = None
        if node.value:
            value = self.evaluate_expression(node.value)
        raise ReturnException(value)
    
    def evaluate_expression(self, node: ASTNode) -> Any:
        """Evaluate expression node"""
        if isinstance(node, NumberLiteral):
            return node.value
        
        elif isinstance(node, StringLiteral):
            return node.value
        
        elif isinstance(node, BooleanLiteral):
            return node.value
        
        elif isinstance(node, Identifier):
            return self.current_env.get(node.name)
        
        elif isinstance(node, ListLiteral):
            return [self.evaluate_expression(elem) for elem in node.elements]
        
        elif isinstance(node, DictLiteral):
            result = {}
            for key, value in node.pairs:
                k = self.evaluate_expression(key)
                v = self.evaluate_expression(value)
                result[k] = v
            return result
        
        elif isinstance(node, BinaryOp):
            return self.evaluate_binary_op(node)
        
        elif isinstance(node, UnaryOp):
            return self.evaluate_unary_op(node)
        
        elif isinstance(node, FunctionCall):
            return self.evaluate_function_call(node)
        
        elif isinstance(node, IndexAccess):
            obj = self.evaluate_expression(node.object)
            idx = self.evaluate_expression(node.index)
            return obj[idx]
        
        elif isinstance(node, MemberAccess):
            obj = self.evaluate_expression(node.object)
            return getattr(obj, node.member)
        
        else:
            raise ExecutionError(f"Unknown expression type: {type(node)}")
    
    def evaluate_binary_op(self, node: BinaryOp) -> Any:
        """Evaluate binary operation"""
        left = self.evaluate_expression(node.left)
        right = self.evaluate_expression(node.right)
        
        op = node.operator
        
        # Arithmetic
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise ExecutionError("Division by zero")
            return left / right
        elif op == '%':
            return left % right
        
        # Comparison
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '<=':
            return left <= right
        elif op == '>':
            return left > right
        elif op == '>=':
            return left >= right
        
        # Logical
        elif op == 'and':
            return left and right
        elif op == 'or':
            return left or right
        
        else:
            raise ExecutionError(f"Unknown operator: {op}")
    
    def evaluate_unary_op(self, node: UnaryOp) -> Any:
        """Evaluate unary operation"""
        operand = self.evaluate_expression(node.operand)
        
        if node.operator == '-':
            return -operand
        elif node.operator == 'not':
            return not operand
        else:
            raise ExecutionError(f"Unknown unary operator: {node.operator}")
    
    def evaluate_function_call(self, node: FunctionCall) -> Any:
        """Evaluate function call"""
        args = [self.evaluate_expression(arg) for arg in node.arguments]
        
        # Handle built-in functions
        if node.name == 'len':
            return len(args[0]) if args else 0
        
        elif node.name == 'str':
            return str(args[0]) if args else ""
        
        elif node.name == 'int':
            return int(args[0]) if args else 0
        
        elif node.name == 'float':
            return float(args[0]) if args else 0.0
        
        elif node.name == 'type':
            return type(args[0]).__name__ if args else "None"
        
        else:
            raise ExecutionError(f"Unknown function: {node.name}")
    
    def is_truthy(self, value: Any) -> bool:
        """Check if value is truthy"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)
    
    def format_value(self, value: Any) -> str:
        """Format value for output"""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (list, dict)):
            return str(value)
        else:
            return str(value)
