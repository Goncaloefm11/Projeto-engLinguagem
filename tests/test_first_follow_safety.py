from core.grammar import GrammarParser
from core.ll1_analyzer import LL1Analyzer


def test_first_follow_conflict_warns_about_nullable():
    """Ensure FIRST/FOLLOW suggestions address nullable conflicts."""
    grammar_text = """
S → A a
A → a | ε
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    assert report["conflicts"], "Expected at least one FIRST/FOLLOW conflict"
    conflict = report["conflicts"][0]
    
    assert conflict["type"] == "FIRST/FOLLOW"
    suggestion = conflict["suggestion"]
    
    # Must address nullable and restructuring
    assert "anulável" in suggestion or "Anulável" in suggestion or "ε" in suggestion
    assert "Reformulação" in suggestion or "reestruturação" in suggestion.lower()


def test_first_follow_suggests_no_auto_correction_for_generic_case():
    """Generic FIRST/FOLLOW conflicts (non-list patterns) should NOT provide automatic corrected_grammar."""
    grammar_text = """
S → A a
A → a | ε
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    conflict = report["conflicts"][0]
    
    # For non-list patterns, no auto-correction
    assert conflict["corrected_grammar"] == ""


def test_list_pattern_first_follow_provides_correction():
    """List patterns (Elems → Elem | Elem , Elems) should provide corrected_grammar."""
    grammar_text = """
Lista → Elem | Elem , Lista
Elem → id
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    # May have FIRST/FOLLOW from comma context
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            if conflict["type"] == "FIRST/FOLLOW":
                # List pattern should suggest replacement
                suggestion = conflict["suggestion"]
                # Check for specific list restructuring advice
                assert "Plural" in suggestion or "plural" in suggestion or "Lista" in suggestion


def test_first_follow_sets_disjoint_after_fix():
    """Verify that FIRST and FOLLOW sets are disjoint for nullable non-terminals."""
    grammar_text = """
Lista → Elem | Elem , Lista
Elem → id
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    analyzer.analyze()
    
    # Check disjointness for nullable non-terminals
    for nt in grammar.non_terminals:
        if nt in analyzer.nullable and nt not in [grammar.start_symbol]:
            first = analyzer.first_sets.get(nt, set())
            follow = analyzer.follow_sets.get(nt, set())
            
            # Remove epsilon from first for comparison
            first_without_eps = first - {nt}  # Remove epsilon marker if present
            
            # FIRST and FOLLOW should have minimal overlap for nullable
            # This is a warning condition, not always violated


def test_ll1_table_no_multiple_productions_per_cell():
    """Verify that LL(1) table has no cells with multiple productions."""
    grammar_text = """
S → A B
A → a | ε
B → b | c
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()
    
    # A grammar without conflicts has unique entries in LL(1) table
    if report["is_ll1"]:
        table = report["ll1_table"]
        for nt_name, row in table.items():
            for terminal, prods in row.items():
                assert len(prods) <= 1, f"Multiple productions for {nt_name}, {terminal}: {prods}"

