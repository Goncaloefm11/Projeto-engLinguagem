"""
Lexical Analyzer (Lexer) - Tokenizes input strings
Converts raw input into tokens based on grammar definition
"""

from typing import List, Dict, NamedTuple, Optional
from enum import Enum
import re


class TokenType(Enum):
    """Token type enumeration"""
    # Literals
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # Operators
    PLUS = "PLUS"           # +
    MINUS = "MINUS"         # -
    MULTIPLY = "MULTIPLY"   # *
    DIVIDE = "DIVIDE"       # /
    MODULO = "MODULO"       # %
    
    # Comparison
    EQ = "EQ"               # =
    NEQ = "NEQ"             # !=
    LT = "LT"               # <
    LE = "LE"               # <=
    GT = "GT"               # >
    GE = "GE"               # >=
    ASSIGN = "ASSIGN"       # :=
    
    # Logical
    AND = "AND"             # and
    OR = "OR"               # or
    NOT = "NOT"             # not
    
    # Brackets
    LPAREN = "LPAREN"       # (
    RPAREN = "RPAREN"       # )
    LBRACE = "LBRACE"       # {
    RBRACE = "RBRACE"       # }
    LBRACKET = "LBRACKET"   # [
    RBRACKET = "RBRACKET"   # ]
    
    # Delimiters
    SEMICOLON = "SEMICOLON" # ;
    COMMA = "COMMA"         # ,
    COLON = "COLON"         # :
    DOT = "DOT"             # .
    ARROW = "ARROW"         # →
    
    # Keywords
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    DO = "DO"
    FOR = "FOR"
    RETURN = "RETURN"
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    TRY = "TRY"
    CATCH = "CATCH"
    THROW = "THROW"
    EXEC = "EXEC"
    PRINT = "PRINT"
    TRUE = "TRUE"
    FALSE = "FALSE"
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


class Token(NamedTuple):
    """Token representation"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, {self.line}:{self.column})"


class LexerError(Exception):
    """Lexer error"""
    pass


class Lexer:
    """Lexical analyzer - converts input string to token stream"""
    
    KEYWORDS = {
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'do': TokenType.DO,
        'for': TokenType.FOR,
        'return': TokenType.RETURN,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'try': TokenType.TRY,
        'catch': TokenType.CATCH,
        'throw': TokenType.THROW,
        'exec': TokenType.EXEC,
        'print': TokenType.PRINT,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }
    
    def __init__(self, input_text: str):
        """Initialize lexer with input text"""
        self.input = input_text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def error(self, message: str):
        """Raise lexer error with position info"""
        raise LexerError(f"Lexer error at {self.line}:{self.column}: {message}")
    
    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at character without consuming"""
        pos = self.pos + offset
        if pos < len(self.input):
            return self.input[pos]
        return None
    
    def advance(self) -> Optional[str]:
        """Consume and return next character"""
        if self.pos >= len(self.input):
            return None
        
        char = self.input[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.peek() and self.peek() in ' \t\r\n':
            self.advance()
    
    def skip_comment(self):
        """Skip comments (// ... to end of line)"""
        if self.peek() == '/' and self.peek(1) == '/':
            while self.peek() and self.peek() != '\n':
                self.advance()
            if self.peek() == '\n':
                self.advance()
            return True
        return False
    
    def read_string(self, quote: str) -> str:
        """Read string literal"""
        result = ""
        self.advance()  # Skip opening quote
        
        while self.peek() and self.peek() != quote:
            if self.peek() == '\\':
                self.advance()
                escaped = self.advance()
                if escaped == 'n':
                    result += '\n'
                elif escaped == 't':
                    result += '\t'
                elif escaped == 'r':
                    result += '\r'
                elif escaped == '\\':
                    result += '\\'
                elif escaped == quote:
                    result += quote
                else:
                    result += escaped
            else:
                result += self.advance()
        
        if self.peek() != quote:
            self.error(f"Unterminated string literal")
        
        self.advance()  # Skip closing quote
        return result
    
    def read_number(self) -> str:
        """Read numeric literal"""
        result = ""
        
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            result += self.advance()
        
        return result
    
    def read_identifier(self) -> str:
        """Read identifier or keyword"""
        result = ""
        
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            result += self.advance()
        
        return result
    
    def tokenize(self) -> List[Token]:
        """Tokenize input and return token list"""
        self.tokens = []
        
        while self.pos < len(self.input):
            self.skip_whitespace()
            
            if self.skip_comment():
                continue
            
            if self.pos >= len(self.input):
                break
            
            line = self.line
            column = self.column
            char = self.peek()
            
            # String literals
            if char in ('"', "'"):
                quote = self.advance()
                value = self.read_string(quote)
                self.tokens.append(Token(TokenType.STRING, value, line, column))
            
            # Numbers
            elif char.isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, line, column))
            
            # Identifiers and keywords
            elif char.isalpha() or char == '_':
                value = self.read_identifier()
                token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, value, line, column))
            
            # Operators and delimiters
            elif char == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', line, column))
            
            elif char == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', line, column))
            
            elif char == '*':
                self.advance()
                self.tokens.append(Token(TokenType.MULTIPLY, '*', line, column))
            
            elif char == '/':
                self.advance()
                self.tokens.append(Token(TokenType.DIVIDE, '/', line, column))
            
            elif char == '%':
                self.advance()
                self.tokens.append(Token(TokenType.MODULO, '%', line, column))
            
            elif char == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQ, '==', line, column))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', line, column))
            
            elif char == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NEQ, '!=', line, column))
                else:
                    self.error(f"Unexpected character: !")
            
            elif char == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LE, '<=', line, column))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', line, column))
            
            elif char == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GE, '>=', line, column))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', line, column))
            
            elif char == ':':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, ':=', line, column))
                else:
                    self.tokens.append(Token(TokenType.COLON, ':', line, column))
            
            elif char == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', line, column))
            
            elif char == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', line, column))
            
            elif char == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', line, column))
            
            elif char == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', line, column))
            
            elif char == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', line, column))
            
            elif char == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', line, column))
            
            elif char == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ';', line, column))
            
            elif char == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', line, column))
            
            elif char == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, '.', line, column))
            
            elif char == '→':
                self.advance()
                self.tokens.append(Token(TokenType.ARROW, '→', line, column))
            
            else:
                self.error(f"Unexpected character: {repr(char)}")
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    @staticmethod
    def tokenize_text(text: str) -> List[Token]:
        """Convenience method to tokenize text"""
        lexer = Lexer(text)
        return lexer.tokenize()
