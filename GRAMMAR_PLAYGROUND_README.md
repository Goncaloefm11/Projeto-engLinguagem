# Grammar Playground (GP)
## LL(1) Grammar Analysis & Parse Tree Builder

Projeto de Engenharia de Linguagens - 2º Semestre 2026

### Visão Geral

O Grammar Playground é um ambiente gráfico interativo para analisar e trabalhar com gramáticas independentes de contexto do tipo LL(1). O sistema fornece análise completa de gramáticas, detecção de conflitos e construção de árvores de derivação.

### Funcionalidades

#### Fase 1 (Implementado)

- ✅ **Análise de Gramáticas**
  - Carregamento e parsing de definições de gramática
  - Extração de símbolos terminais e não-terminais
  - Análise de produções

- ✅ **Análise LL(1)**
  - Cálculo automático de conjuntos FIRST
  - Cálculo automático de conjuntos FOLLOW
  - Construção da tabela de parsing LL(1)
  - Detecção de conflitos (FIRST/FIRST, FIRST/FOLLOW)

- ✅ **Construção de Árvores de Derivação**
  - Parsing de frases de entrada
  - Construção de árvore de derivação em tempo real
  - Visualização de árvore em formato textual
  - Suporte a múltiplos formatos de saída

- ✅ **Interface Gráfica Web**
  - Dashboard moderno e responsivo
  - Análise em tempo real
  - Visualização de resultados tabulares
  - Exemplos pré-configurados

#### Fase 2 (Futuro)

- Geração de ontologia OWL/RDF para gramáticas
- Verificação de conflitos em representação RDF
- Sugestão automática de estrutura de funções de visita
- Geração de código a partir de árvores de derivação

### Instalação

1. **Clonar o repositório**
```bash
cd Projeto-engLinguagem
```

2. **Instalar dependências**
```bash
pip install -r requirements.txt
```

3. **Executar a aplicação**
```bash
python app.py
```

4. **Acessar a interface**
Abra o navegador em `http://localhost:5000`

### Uso

#### Analisar uma Gramática

1. Insira a definição da gramática em formato padrão:
```
Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;
```

2. Clique em "Analisar Gramática"

3. Visualize os resultados:
   - **FIRST Sets**: Conjuntos FIRST de cada símbolo
   - **FOLLOW Sets**: Conjuntos FOLLOW de cada símbolo
   - **LL(1) Tabela**: Tabela de parsing para análise dirigida por tabela
   - **Conflitos**: Indicação de conflitos detectados

#### Analisar uma Frase

1. Depois de analisar uma gramática, insira uma frase na seção "Analisar Entrada"
2. Clique em "Construir Árvore de Derivação"
3. Visualize a árvore gerada em formato textual

### Formato de Gramática

A gramática deve ser especificada em um formato simples e intuitivo:

```
<não-terminal> → <alternativa1> | <alternativa2> | ε;
```

**Exemplos:**

- **Produção simples**: `Expr → Term`
- **Múltiplas alternativas**: `Expr → Term | Expr + Term`
- **Produção vazia**: `Expr → ε`
- **Símbolos múltiplos**: `Stmt → id := Expr + number`

**Símbolos:**
- **Não-terminais**: Começam com letra maiúscula (ex: `Program`, `Expr`, `Stmt'`)
- **Terminais**: Começam com letra minúscula ou são números (ex: `id`, `number`, `+`, `:=`)
- **Epsilon**: Representado como `ε` ou `else` (produção vazia)

### Estrutura do Projeto

```
Projeto-engLinguagem/
├── app.py                          # Aplicação Flask principal
├── requirements.txt                # Dependências Python
├── README.md                       # Este arquivo
├── deteta_vuln/
│   ├── grammar_analyzer.py        # Analisador de gramáticas LL(1)
│   ├── parse_tree_builder.py      # Construtor de árvores de derivação
│   ├── grammar_language.lark      # Gramática Lark para definição de gramáticas
│   ├── analyser.py                # Analisador estático (vulnerabilidades)
│   ├── cfg_maker.py               # Gerador de grafos de controle de fluxo
│   ├── scope.py                   # Análise de escopo
│   ├── rules.json                 # Regras de análise
│   └── exemplo.ipl                # Exemplo de código
├── templates/
│   └── index.html                 # Interface web principal
├── static/                        # Arquivos estáticos (CSS, JS)
└── core/
    ├── parser_logic.py            # Lógica de parsing (legado)
    └── utils.py                   # Funções utilitárias
```

### Exemplos de Uso

#### Exemplo 1: Pascal Subset
```
Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;
```

**Frase válida**: `id := number`

#### Exemplo 2: Expressões Matemáticas
```
Expr → Term ExprRest;
ExprRest → + Term ExprRest | ε;
Term → Factor TermRest;
TermRest → * Factor TermRest | ε;
Factor → ( Expr ) | number | id;
```

**Frase válida**: `id + number * number`

#### Exemplo 3: Listas Simples
```
List → List , Element | Element;
Element → id;
```

**Frase válida**: `id , id , id`

### Componentes Principais

#### GrammarAnalyzer (`deteta_vuln/grammar_analyzer.py`)

Realiza análise completa de gramáticas LL(1):

```python
from grammar_analyzer import GrammarAnalyzer, parse_grammar_text

# Parsing da gramática
grammar = parse_grammar_text(grammar_text)

# Análise
analyzer = GrammarAnalyzer(grammar)
results = analyzer.analyze_complete()

# Resultados disponíveis
- results['first']: Conjuntos FIRST
- results['follow']: Conjuntos FOLLOW
- results['ll1_table']: Tabela de parsing
- results['is_ll1']: Booleano indicando se é LL(1)
- results['conflicts']: Lista de conflitos detectados
```

#### ParseTreeBuilder (`deteta_vuln/parse_tree_builder.py`)

Constrói árvores de derivação para frases de entrada:

```python
from parse_tree_builder import ParseTreeBuilder, TreeVisualizer

# Criar parser
builder = ParseTreeBuilder(grammar)

# Fazer parsing
success, result = builder.parse(input_text)

# Visualizações
if success:
    tree_string = builder.tree_to_string(result)
    tree_dict = builder.tree_to_dict(result)
    mermaid = TreeVisualizer.tree_to_mermaid(result)
```

### API Flask

#### `GET /`
Página principal com interface web

#### `POST /api/analyze-grammar`
Analisa uma gramática

**Request:**
```json
{
    "grammar": "Program → StmtList; ..."
}
```

**Response:**
```json
{
    "success": true,
    "first": {...},
    "follow": {...},
    "ll1_table": {...},
    "is_ll1": true,
    "conflicts": [],
    "conflict_count": 0
}
```

#### `POST /api/parse-input`
Faz parsing de uma entrada

**Request:**
```json
{
    "grammar": "Program → StmtList; ...",
    "input": "id := number"
}
```

**Response:**
```json
{
    "success": true,
    "tree": {...},
    "tree_string": "...",
    "tree_levels": [...]
}
```

#### `GET /api/examples`
Retorna exemplos de gramáticas

### Conceitos LL(1)

#### FIRST Set
Conjunto de terminais que podem aparecer no início de uma derivação:
- `FIRST(A) = {a | A ⇒* aβ} ∪ {ε | A ⇒* ε}`

#### FOLLOW Set
Conjunto de terminais que podem aparecer após um não-terminal:
- `FOLLOW(A) = {a | S ⇒* ... Aa ...}`

#### Conflitos LL(1)
- **FIRST/FIRST**: Duas produções de um não-terminal começam com o mesmo terminal
- **FIRST/FOLLOW**: Uma produção vazia compete com produções que começam com um terminal

### Troubleshooting

#### Erro: "Port already in use"
```bash
# Executar em porta diferente
python -c "from app import app; app.run(port=5001)"
```

#### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

#### Gramática não reconhecida
- Verifique se está usando `→` (não `->`)
- Termine cada produção com `;`
- Use `ε` para produções vazias (não `e` ou `epsilon`)
- Separadores: `|` para alternativas, espaço para símbolos

### Desenvolvido por

Estudantes de Engenharia de Linguagens  
Universidade do Minho - 2026

### Licença

Este projeto é parte do currículo acadêmico e pode ser livremente utilizado e modificado para fins educacionais.

### Referências

- Aho, Lam, Sethi, Ullman - *Compilers: Principles, Techniques, and Tools*
- Dragon Book - Análise Léxica e Sintática
- Sippu, Soisalon-Soininen - *Parsing Theory*

---

Para mais informações ou relatório de bugs, abra uma issue no repositório do projeto.
