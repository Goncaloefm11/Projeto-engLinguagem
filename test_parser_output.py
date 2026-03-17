import sys
sys.path.insert(0, '.')

from core.grammar import GrammarParser
from core.ll1_analyzer import LL1Analyzer
from core.parser_generator import RecursiveDescentGenerator

# Simple test grammar
grammar_text = """
E -> T E_prime
E_prime -> + T E_prime | ε
T -> id
"""

grammar = GrammarParser.parse(grammar_text)
analyzer = LL1Analyzer(grammar)
analyzer.analyze()

generator = RecursiveDescentGenerator(grammar, analyzer)
code = generator.generate("python")

# Show first 70 lines
lines = code.split('\n')
print("=" * 80)
print("GENERATED PARSER CODE (ACADEMIC STYLE)")
print("=" * 80)
for i, line in enumerate(lines[:70]):
    print(f"{i+1:3d}: {line}")
    
if len(lines) > 70:
    print(f"\n... ({len(lines) - 70} more lines)")
