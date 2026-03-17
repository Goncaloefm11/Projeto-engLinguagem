from core.grammar import GrammarParser
from core.ll1_analyzer import LL1Analyzer


def test_first_first_k2_prefers_factoring_suggestion_over_requires_ll2():
    grammar_text = """
Lista -> [ ] | [ Elems ]
Elems -> id
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    assert report["conflicts"], "Expected at least one conflict"
    conflict = report["conflicts"][0]

    assert conflict["type"] == "FIRST/FIRST"
    assert "REQUIRES_LL(2)" not in conflict["type"]
    assert "Fatoração" in conflict["suggestion"] or "fatoração" in conflict["suggestion"]


def test_left_recursion_is_classified_as_critical_conflict():
    grammar_text = """
Expr -> Expr + Term | Term
Term -> id
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    assert report["conflicts"], "Expected conflict for left-recursive grammar"
    types = [c["type"] for c in report["conflicts"]]
    assert "LEFT-RECURSION" in types


def test_left_recursion_checked_before_first_follow():
    """LEFT-RECURSION should be detected first, not masked by FIRST/FOLLOW."""
    grammar_text = """
A -> A a | ε
"""
    grammar = GrammarParser.parse(grammar_text)
    analyzer = LL1Analyzer(grammar)
    report = analyzer.get_analysis_report()

    # Should detect left-recursion first
    types = [c["type"] for c in report["conflicts"]]
    assert "LEFT-RECURSION" in types
    
    # If both conflicts reported, LEFT-RECURSION comes first
    if len(report["conflicts"]) > 0:
        assert report["conflicts"][0]["type"] == "LEFT-RECURSION"
