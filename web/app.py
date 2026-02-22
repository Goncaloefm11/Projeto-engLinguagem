from flask import Flask, render_template, request, jsonify
import os
import sys


# Add parent directory to path for imports
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grammar import Grammar, GrammarParser
from core.ll1_analyzer import LL1Analyzer
from core.parser_generator import RecursiveDescentGenerator, TableDrivenGenerator
from core.derivation_tree import DerivationTreeBuilder, build_derivation_tree
from core.visitor import TreeVisitor
import traceback


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
    parser_type = data.get('type', 'recursive')  # 'recursive' or 'table'
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
        
        if parser_type == 'recursive':
            generator = RecursiveDescentGenerator(grammar, analyzer)
        else:
            generator = TableDrivenGenerator(grammar, analyzer)
        
        code = generator.generate(language)
        
        return jsonify({
            'success': True,
            'code': code,
            'type': parser_type,
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

@app.route('/execute-visitor', methods=['POST'])
def execute_visitor():
    """Gera a árvore e aplica o código de visita introduzido pelo utilizador"""
    data = request.get_json()
    grammar_text = data.get('grammar', '')
    input_text = data.get('input', '')
    visitor_code = data.get('visitor_code', '')
    
    if not visitor_code.strip():
        return jsonify({'success': False, 'error': 'Nenhum código de visita fornecido.'})
        
    try:
        # 1. Gerar a árvore primeiro (reutilizando a tua função existente)
        parse_result = build_derivation_tree(grammar_text, input_text)
        
        if not parse_result.get('success'):
            return jsonify({'success': False, 'error': 'Erro ao gerar a árvore.', 'details': parse_result.get('errors')})
            
        # Precisamos da árvore real (objetos Python) e não do dict JSON retornado pela build_derivation_tree.
        # Por isso, refazemos o parse interno rapidamente para ter os objetos:
        grammar = GrammarParser.parse(grammar_text)
        from core.lark_parser import LarkTreeBuilder
        builder = LarkTreeBuilder(grammar)
        tree_root, _ = builder.parse(input_text)
        
        # 2. Preparar o ambiente seguro (sandbox básica) para o exec()
        local_env = {}
        global_env = {'TreeVisitor': TreeVisitor} # Dá acesso apenas à classe base
        
        # 3. Executar o código do utilizador
        # O utilizador DEVE definir uma classe chamada 'MyVisitor' que herda de TreeVisitor
        exec(visitor_code, global_env, local_env)
        
        if 'MyVisitor' not in local_env:
            return jsonify({'success': False, 'error': 'O teu código deve conter uma classe chamada "MyVisitor".'})
            
        # 4. Instanciar e visitar a árvore
        visitor_instance = local_env['MyVisitor']()
        generated_code = visitor_instance.visit(tree_root)
        
        return jsonify({
            'success': True,
            'generated_code': generated_code
        })
        
    except Exception as e:
        # Apanha erros de sintaxe no código do utilizador
        error_trace = traceback.format_exc()
        return jsonify({
            'success': False, 
            'error': f'Erro na execução do Visitor: {str(e)}',
            'traceback': error_trace
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
