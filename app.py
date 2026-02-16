from flask import Flask, render_template, request, jsonify
import sys
import os
from pathlib import Path

# Add deteta_vuln to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deteta_vuln'))

from grammar_analyzer import GrammarAnalyzer, parse_grammar_text
from parse_tree_builder import ParseTreeBuilder, TreeVisualizer
from lexer import Lexer, LexerError
from ast_builder import ASTBuilder
from semantic_analyzer import Parser, ExecutionError

app = Flask(__name__, template_folder='templates', static_folder='static')


def parse_grammar_text_extended(texto):
    """Parse grammar text and return grammar dict"""
    return parse_grammar_text(texto)


@app.route('/')
def index():
    """Main page - Grammar Playground"""
    return render_template('index.html', 
        example_grammar="""Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;""")


@app.route('/api/analyze-grammar', methods=['POST'])
def analyze_grammar():
    """Analyze a grammar and return FIRST, FOLLOW, LL(1) table, and conflicts"""
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        
        # Parse grammar
        grammar = parse_grammar_text(grammar_text)
        
        if not grammar:
            return jsonify({'error': 'Invalid grammar format'}), 400
        
        # Analyze grammar
        analyzer = GrammarAnalyzer(grammar)
        results = analyzer.analyze_complete()
        
        return jsonify({
            'success': True,
            'grammar': {nt: len(prods) for nt, prods in grammar.items()},
            'nonterminals': sorted(list(analyzer.nonterminals)),
            'terminals': sorted([t for t in analyzer.terminals if t != analyzer.eof]),
            'first': results['first'],
            'follow': results['follow'],
            'll1_table': results['ll1_table'],
            'is_ll1': results['is_ll1'],
            'conflicts': results['conflicts'],
            'conflict_count': results['conflict_count']
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/parse-input', methods=['POST'])
def parse_input():
    """Parse input sentence according to grammar"""
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        input_text = data.get('input', '')
        
        # Parse grammar
        grammar = parse_grammar_text(grammar_text)
        
        if not grammar:
            return jsonify({'error': 'Invalid grammar format'}), 400
        
        # Build parser and parse input
        builder = ParseTreeBuilder(grammar)
        
        if not builder.parser:
            return jsonify({'error': f'Parser initialization error: {builder.error}'}), 400
        
        success, result = builder.parse(input_text)
        
        if not success:
            return jsonify({
                'success': False,
                'error': result,
                'parse_failed': True
            })
        
        # Convert tree to various formats
        tree_dict = builder.tree_to_dict(result)
        tree_string = builder.tree_to_string(result)
        tree_levels = builder.tree_to_levels(result)
        mermaid_diagram = TreeVisualizer.tree_to_mermaid(result)
        
        return jsonify({
            'success': True,
            'tree': tree_dict,
            'tree_string': tree_string,
            'tree_levels': tree_levels,
            'mermaid': mermaid_diagram
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/suggest-corrections', methods=['POST'])
def suggest_corrections():
    """Suggest corrections for grammar conflicts"""
    try:
        data = request.json
        grammar_text = data.get('grammar', '')
        
        # Parse grammar
        grammar = parse_grammar_text(grammar_text)
        analyzer = GrammarAnalyzer(grammar)
        analyzer.analyze_complete()
        
        suggestions = []
        for conflict in analyzer.conflicts:
            suggestions.append({
                'conflict': str(conflict),
                'suggestion': f'Eliminate ambiguity at ({conflict.nonterminal}, {conflict.terminal}) by restructuring productions'
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Return example grammars"""
    examples = {
        'pascal_subset': """Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;""",
        
        'simple_expr': """Expr → Term ExprRest;
ExprRest → + Term ExprRest | ε;
Term → Factor TermRest;
TermRest → * Factor TermRest | ε;
Factor → ( Expr ) | number | id;""",
        
        'simple_list': """List → List , Element | Element;
Element → id;"""
    }
    
    return jsonify(examples)


# ========== NEW: COMPLETE PARSING PIPELINE ROUTES ==========

@app.route('/api/lexical-analysis', methods=['POST'])
def lexical_analysis():
    """Perform lexical analysis (tokenization)"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Tokenize
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            token_list = []
            for token in tokens:
                token_list.append({
                    'type': token.type.name,
                    'value': token.value,
                    'line': token.line,
                    'column': token.column
                })
            
            return jsonify({
                'success': True,
                'tokens': token_list,
                'token_count': len(tokens) - 1,  # Exclude EOF
                'errors': []
            })
        
        except LexerError as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'tokens': [],
                'errors': [str(e)]
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/syntactic-analysis', methods=['POST'])
def syntactic_analysis():
    """Perform syntactic analysis (parsing)"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        try:
            # Tokenize
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            # Parse using grammar.lark
            from lark import Lark
            
            # Load the Lark grammar
            grammar_path = os.path.join(os.path.dirname(__file__), 'deteta_vuln', 'grammar.lark')
            with open(grammar_path, 'r', encoding='utf-8') as f:
                grammar = f.read()
            
            parser = Lark(grammar, start='start', parser='lalr')
            parse_tree = parser.parse(code)
            
            # Convert tree to dict representation
            def tree_to_dict(node):
                if isinstance(node, str):
                    return {'type': 'token', 'value': node}
                
                from lark import Tree, Token
                if isinstance(node, Token):
                    return {'type': 'terminal', 'value': str(node.value), 'token_type': node.type}
                
                if isinstance(node, Tree):
                    return {
                        'type': 'nonterminal',
                        'name': node.data,
                        'children': [tree_to_dict(child) for child in node.children]
                    }
                
                return {'type': 'unknown', 'value': str(node)}
            
            tree_dict = tree_to_dict(parse_tree)
            tree_str = parse_tree.pretty()
            
            return jsonify({
                'success': True,
                'parse_tree': tree_dict,
                'parse_tree_string': tree_str,
                'errors': []
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'errors': [str(e)]
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/build-ast', methods=['POST'])
def build_ast():
    """Build Abstract Syntax Tree"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        try:
            # Parse
            from lark import Lark
            
            grammar_path = os.path.join(os.path.dirname(__file__), 'deteta_vuln', 'grammar.lark')
            with open(grammar_path, 'r', encoding='utf-8') as f:
                grammar = f.read()
            
            parser = Lark(grammar, start='start', parser='lalr')
            parse_tree = parser.parse(code)
            
            # Build AST
            ast_builder = ASTBuilder()
            ast = ast_builder.build(parse_tree)
            
            if ast is None:
                return jsonify({
                    'success': False,
                    'error': 'Failed to build AST',
                    'errors': ast_builder.errors
                }), 400
            
            # Convert AST to dict
            ast_dict = ast.to_dict()
            
            return jsonify({
                'success': True,
                'ast': ast_dict,
                'ast_string': str(ast),
                'errors': ast_builder.errors
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'errors': [str(e)]
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/execute-parser', methods=['POST'])
def execute_parser():
    """Execute the parser (semantic analysis and code execution)"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        try:
            # Parse
            from lark import Lark
            
            grammar_path = os.path.join(os.path.dirname(__file__), 'deteta_vuln', 'grammar.lark')
            with open(grammar_path, 'r', encoding='utf-8') as f:
                grammar = f.read()
            
            parser_lark = Lark(grammar, start='start', parser='lalr')
            parse_tree = parser_lark.parse(code)
            
            # Build AST
            ast_builder = ASTBuilder()
            ast = ast_builder.build(parse_tree)
            
            if ast is None:
                return jsonify({
                    'success': False,
                    'error': 'Failed to build AST',
                    'errors': ast_builder.errors
                }), 400
            
            # Execute AST
            executor = Parser()
            result = executor.execute(ast)
            
            return jsonify({
                'success': result['success'],
                'output': result['output'],
                'errors': result['errors'],
                'result': str(result['result']) if result['result'] is not None else None,
                'ast_errors': ast_builder.errors
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'output': [],
                'errors': [str(e)],
                'result': None
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/complete-analysis', methods=['POST'])
def complete_analysis():
    """Run complete analysis pipeline: Lexical -> Syntactic -> AST -> Execution"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        result = {
            'lexical': None,
            'syntactic': None,
            'ast': None,
            'execution': None,
            'stages_completed': 0
        }
        
        try:
            # Stage 1: Lexical Analysis
            print("Stage 1: Lexical Analysis")
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            token_list = [{'type': t.type.name, 'value': t.value, 'line': t.line, 'column': t.column} for t in tokens]
            result['lexical'] = {
                'success': True,
                'tokens': token_list,
                'token_count': len(tokens) - 1
            }
            result['stages_completed'] += 1
            
            # Stage 2: Syntactic Analysis
            print("Stage 2: Syntactic Analysis")
            from lark import Lark
            
            grammar_path = os.path.join(os.path.dirname(__file__), 'deteta_vuln', 'grammar.lark')
            with open(grammar_path, 'r', encoding='utf-8') as f:
                grammar = f.read()
            
            parser_lark = Lark(grammar, start='start', parser='lalr')
            parse_tree = parser_lark.parse(code)
            
            result['syntactic'] = {
                'success': True,
                'parse_tree_string': parse_tree.pretty()[:500]  # First 500 chars
            }
            result['stages_completed'] += 1
            
            # Stage 3: AST Building
            print("Stage 3: AST Building")
            ast_builder = ASTBuilder()
            ast = ast_builder.build(parse_tree)
            
            if ast:
                result['ast'] = {
                    'success': True,
                    'ast_string': str(ast),
                    'errors': ast_builder.errors
                }
                result['stages_completed'] += 1
            else:
                result['ast'] = {
                    'success': False,
                    'errors': ast_builder.errors
                }
            
            # Stage 4: Execution
            print("Stage 4: Execution")
            if ast:
                executor = Parser()
                exec_result = executor.execute(ast)
                
                result['execution'] = {
                    'success': exec_result['success'],
                    'output': exec_result['output'],
                    'errors': exec_result['errors'],
                    'result': str(exec_result['result']) if exec_result['result'] is not None else None
                }
                result['stages_completed'] += 1
        
        except Exception as e:
            result['error'] = str(e)
        
        return jsonify({
            'success': result['stages_completed'] == 4,
            'analysis': result,
            'stages_completed': result['stages_completed']
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)