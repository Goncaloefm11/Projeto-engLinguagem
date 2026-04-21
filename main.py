from core.loader import carregar_gramatica_da_string
from core.parser_LL1 import calcular_first, calcular_follow, gerar_tabela_ll1, gerar_arvore_derivacao_com_erro, arvore_para_texto, arvore_para_mermaid
from core.lexer import Lexer

texto_exemplo = """
Program -> StmtList
StmtList -> Stmt StmtList_P
StmtList_P -> Stmt StmtList_P | ε
Stmt -> id : Expr
"""

# 1. Ler o texto
gramatica = carregar_gramatica_da_string(texto_exemplo)

# 2. Processar lógica
firsts = calcular_first(gramatica)
follows = calcular_follow(gramatica, firsts)
tabela, conflitos = gerar_tabela_ll1(gramatica, firsts, follows)

print("Gramática carregada com sucesso!")
print(f"Terminais: {gramatica['terminais']}")
print(f"N-Terminais: {gramatica['nao_terminais']}")
print(f"Conflitos: {conflitos}")

# 3. Exemplo de uso do Lexer (análise léxica)
print("\n--- Exemplos de Tokenização ---")
lexer = Lexer(gramatica)

frase_teste = "x : y"
tokens, erro = lexer.tokenizar(frase_teste)
if erro:
    print(f"Erro: {erro}")
else:
    print(f"Frase: '{frase_teste}'")
    print(f"Tokens: {tokens}")