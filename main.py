from core.utils import carregar_gramatica
from core.parser_logic import AnalisadorGramatica

def main():
    print("--- Grammar Playground 2026 ---")
    prods = carregar_gramatica("gramatica.txt")
    analisador = AnalisadorGramatica(prods)
    
    first, follow = analisador.executar()
    
    print("\nConjuntos FIRST:")
    for nt, s in first.items(): print(f"{nt}: {s}")
        
    print("\nConjuntos FOLLOW:")
    for nt, s in follow.items(): print(f"{nt}: {s}")

if __name__ == "__main__":
    main()
