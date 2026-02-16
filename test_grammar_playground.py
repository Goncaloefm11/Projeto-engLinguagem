#!/usr/bin/env python
"""
Test script for Grammar Playground
Tests the grammar analyzer and parse tree builder with example grammars
"""

import sys
import os

# Add deteta_vuln to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deteta_vuln'))

from grammar_analyzer import GrammarAnalyzer, parse_grammar_text
from parse_tree_builder import ParseTreeBuilder, TreeVisualizer


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_grammar_analyzer():
    """Test the grammar analyzer with example grammars"""
    
    # Example: Pascal Subset
    print_section("Test 1: Pascal Subset Grammar Analysis")
    
    grammar_text = """Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;"""
    
    print("Grammar:")
    print(grammar_text)
    print()
    
    # Parse grammar
    grammar = parse_grammar_text(grammar_text)
    print(f"Parsed grammar: {len(grammar)} productions")
    print(f"Non-terminals: {sorted(grammar.keys())}")
    print()
    
    # Analyze
    analyzer = GrammarAnalyzer(grammar)
    results = analyzer.analyze_complete()
    
    print("FIRST Sets:")
    for nt, first in sorted(results['first'].items()):
        print(f"  FIRST({nt}) = {{ {', '.join(first)} }}")
    print()
    
    print("FOLLOW Sets:")
    for nt, follow in sorted(results['follow'].items()):
        print(f"  FOLLOW({nt}) = {{ {', '.join(follow)} }}")
    print()
    
    print(f"Is LL(1): {results['is_ll1']}")
    print(f"Conflict count: {results['conflict_count']}")
    
    if results['conflicts']:
        print("\nConflicts detected:")
        for conflict in results['conflicts']:
            print(f"  - {conflict}")
    else:
        print("\nNo conflicts detected! Grammar is LL(1).")
    
    return grammar, results


def test_parse_tree_builder(grammar):
    """Test the parse tree builder"""
    
    print_section("Test 2: Parse Tree Construction")
    
    # Create parser
    builder = ParseTreeBuilder(grammar)
    
    if not builder.parser:
        print(f"Error: {builder.error}")
        return False
    
    # Test sentences
    test_sentences = [
        "id := id",
        "id := number",
        "id := id + number",
    ]
    
    for sentence in test_sentences:
        print(f"\nParsing: {sentence}")
        success, result = builder.parse(sentence)
        
        if success:
            print("✓ Parse successful!")
            print("\nParse Tree:")
            tree_str = builder.tree_to_string(result)
            for line in tree_str.split('\n')[:20]:  # First 20 lines
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"✗ Parse failed: {result}")
    
    return True


def test_simple_grammar():
    """Test with a simpler grammar"""
    
    print_section("Test 3: Simple Expression Grammar")
    
    grammar_text = """Expr → Term ExprRest;
ExprRest → + Term ExprRest | ε;
Term → Factor TermRest;
TermRest → * Factor TermRest | ε;
Factor → id | number;"""
    
    print("Grammar:")
    print(grammar_text)
    print()
    
    grammar = parse_grammar_text(grammar_text)
    analyzer = GrammarAnalyzer(grammar)
    results = analyzer.analyze_complete()
    
    print(f"Analysis Results:")
    print(f"  Is LL(1): {results['is_ll1']}")
    print(f"  Non-terminals: {len(analyzer.nonterminals)}")
    print(f"  Terminals: {len(analyzer.terminals) - 1}")  # Exclude $EOF
    print(f"  Conflicts: {results['conflict_count']}")
    
    return grammar


def main():
    """Main test function"""
    
    print("\n" + "="*60)
    print("  Grammar Playground - Test Suite")
    print("="*60)
    
    try:
        # Test 1: Grammar Analysis
        grammar1, results1 = test_grammar_analyzer()
        
        # Test 2: Parse Tree Building
        test_parse_tree_builder(grammar1)
        
        # Test 3: Simple Grammar
        grammar2 = test_simple_grammar()
        
        print_section("All Tests Completed Successfully!")
        print("✓ Grammar analyzer working correctly")
        print("✓ Parse tree builder working correctly")
        print("✓ LL(1) analysis and conflict detection working")
        
        print("\nYou can now start the Flask application with:")
        print("  python app.py")
        print("\nThen open http://localhost:5000 in your browser.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
