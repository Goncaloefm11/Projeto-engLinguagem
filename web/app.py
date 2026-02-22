from flask import Flask, render_template, request, jsonify
import os
import sys


# Add parent directory to path for imports
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grammar import Grammar, GrammarParser
from core.ll1_analyzer import LL1Analyzer
from core.parser_generator import RecursiveDescentGenerator
from core.derivation_tree import DerivationTreeBuilder, build_derivation_tree


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'grammar-playground-secret-key')


# Example grammars
EXAMPLE_GRAMMARS = {
    "pascal_subset": """Program → StmtList
StmtList → Stmt StmtList'
StmtList' → ; Stmt StmtList' | ε
Stmt → id := Expr
Expr → Term Expr'
Expr' → + Term Expr' | ε
Term → id | number""",
    
    "arithmetic": """E → T E'
E' → + T E' | ε
T → F T'
T' → * F T' | ε
F → ( E ) | id | number""",
    
    "simple": """S → A B
A → a | ε
B → b | c"""
}


@app.route('/')
def index():
    """Main page with grammar input"""
    return render_template('index.html', examples=EXAMPLE_GRAMMARS)


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a grammar and return LL(1) analysis results"""
    data = request.get_json()
    grammar_text = data.get('grammar', '')
    
    if not grammar_text.strip():
        return jsonify({
            'success': False,
            'error': 'No grammar provided'
        })
    
    try:
        grammar = GrammarParser.parse(grammar_text)
        validation_errors = grammar.validate()
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Grammar validation errors',
                'details': validation_errors
            })
        
        analyzer = LL1Analyzer(grammar)
        report = analyzer.get_analysis_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/generate-parser', methods=['POST'])
def generate_parser():
    """Generate parser code from grammar"""
    data = request.get_json()
    grammar_text = data.get('grammar', '')
    language = data.get('language', 'python')
    
    if not grammar_text.strip():
        return jsonify({
            'success': False,
            'error': 'No grammar provided'
        })
    
    try:
        grammar = GrammarParser.parse(grammar_text)
        validation_errors = grammar.validate()
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Grammar validation errors',
                'details': validation_errors
            })
        
        analyzer = LL1Analyzer(grammar)
        analyzer.analyze()
        
        if analyzer.ll1_table.has_conflicts():
            return jsonify({
                'success': False,
                'error': 'Grammar has LL(1) conflicts. Cannot generate parser.',
                'conflicts': [
                    {
                        'type': c.type,
                        'description': c.description,
                        'suggestion': c.suggestion
                    }
                    for c in analyzer.ll1_table.conflicts
                ]
            })
        
        generator = RecursiveDescentGenerator(grammar, analyzer)
        code = generator.generate(language)
        
        return jsonify({
            'success': True,
            'code': code,
            'type': 'recursive',
            'language': language
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/parse', methods=['POST'])
def parse_input():
    """Parse input text using the grammar"""
    data = request.get_json()
    grammar_text = data.get('grammar', '')
    input_text = data.get('input', '')
    
    if not grammar_text.strip():
        return jsonify({
            'success': False,
            'error': 'No grammar provided'
        })
    
    if not input_text.strip():
        return jsonify({
            'success': False,
            'error': 'No input provided'
        })
    
    try:
        result = build_derivation_tree(grammar_text, input_text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/examples')
def get_examples():
    """Return available example grammars"""
    return jsonify(EXAMPLE_GRAMMARS)


@app.route('/api/grammar/validate', methods=['POST'])
def validate_grammar():
    """Validate grammar syntax"""
    data = request.get_json()
    grammar_text = data.get('grammar', '')
    
    try:
        grammar = GrammarParser.parse(grammar_text)
        errors = grammar.validate()
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'terminals': [str(t) for t in grammar.terminals],
            'non_terminals': [str(nt) for nt in grammar.non_terminals],
            'start_symbol': str(grammar.start_symbol) if grammar.start_symbol else None,
            'num_productions': len(grammar.productions)
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [str(e)]
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
