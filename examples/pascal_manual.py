# examples/pascal_manual.py

class MockLexer:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def token(self):
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        return None

# --- Inicialização Global
prox_simb = None
lexer = None

def parserError(simb):
    print(f"Erro sintático! Token inesperado: {simb}")

def rec_term(simb):
    global prox_simb
    if prox_simb.type == simb:
        prox_simb = lexer.token()
    else:
        parserError(prox_simb)
        prox_simb = ('erro', '', 0, 0)

# ----------------------------------------------------------
# --- Reconhecimento dos Símbolos Não-Terminais (PASCAL)
# ----------------------------------------------------------

# Program -> StmtList
def rec_Program():
    rec_StmtList()
    print("Program --> StmtList")

# StmtList -> Stmt StmtList'
def rec_StmtList():
    rec_Stmt()
    rec_StmtList_prime()
    print("StmtList --> Stmt StmtList'")

# StmtList' -> Stmt StmtList' | ε 
def rec_StmtList_prime():
    global prox_simb
    # FIRST(Stmt) é 'id'
    if prox_simb and prox_simb.type == 'id':
        rec_Stmt()
        rec_StmtList_prime()
        print("StmtList' --> Stmt StmtList'")
    else:
        # Regra vazia (ε)
        print("StmtList' --> ε")

# Stmt -> id : Expr [cite: 31, 33]
def rec_Stmt():
    rec_term('id')
    rec_term(':')
    rec_Expr()
    print("Stmt --> id : Expr")

# --- Expr --> Term Expr'
def rec_Expr():
    rec_Term()
    rec_Expr_prime()
    print("Expr --> Term Expr'")

# --- Expr' --> + Term Expr'
#             | ε
def rec_Expr_prime():
    global prox_simb
    # Verificamos se o próximo símbolo é o terminal '+' 
    if prox_simb and prox_simb.type == '+':
        rec_term('+')
        rec_Term()
        rec_Expr_prime()
        print("Expr' --> + Term Expr'")
    else:
        # Se não for '+', a regra é vazia (ε) 
        print("Expr' --> ε")

# --- Term --> id
#            | number
def rec_Term():
    global prox_simb
    # Aqui temos dois terminais possíveis para o mesmo não-terminal 
    if prox_simb and prox_simb.type == 'id':
        rec_term('id')
        print("Term --> id")
    elif prox_simb and prox_simb.type == 'number':
        rec_term('number')
        print("Term --> number")
    else:
        parserError(prox_simb)

# ----------------------------------------------------------
# --- Função Principal de Teste
# ----------------------------------------------------------
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

def test_parser():
    global prox_simb, lexer
    # Exemplo de tokens: "id : id + number"
    tokens_exemplo = [
        Token('id', 'x'), Token(':', ':'), Token('id', 'y'), 
        Token('+', '+'), Token('number', '10')
    ]
    lexer = MockLexer(tokens_exemplo)
    prox_simb = lexer.token()
    
    print("A iniciar parsing...")
    rec_Program()
    print("Parsing concluído.")

if __name__ == "__main__":
    test_parser()