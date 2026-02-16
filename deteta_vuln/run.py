from lark import Lark

# Ler a gramática
with open("grammar.lark", "r", encoding="utf-8") as f:
    grammar = f.read()

# Ler o exemplo
with open("exemplo.ipl", "r", encoding="utf-8") as f:
    code = f.read()

# Processar
parser = Lark(grammar, start='start', parser='lalr')
tree = parser.parse(code)

# Mostrar a árvore
print(tree.pretty())