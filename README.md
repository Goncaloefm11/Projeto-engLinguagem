# Grammar Playground (Projeto de Engenharia de Linguagens)

## Overview

**Grammar Playground** é uma ferramenta interativa para análise e processamento de gramáticas formais. O projeto implementa um compilador/interpretador completo para trabalhar com gramáticas LL(1), desde o carregamento até à geração automática de parsers e análise de conflitos.

## Pipeline Geral

A pipeline do projeto funciona em três fases principais:

```
1. ANÁLISE DA GRAMÁTICA
   ├─ Carregar gramática (Loader)
   ├─ Calcular FIRST Sets
   ├─ Calcular FOLLOW Sets
   └─ Gerar tabela LL(1)

2. PROCESSAMENTO
   ├─ Detectar conflitos LL(1)
   ├─ (Opcional) Propor correções (Refactoring)
   ├─ Tokenizar frase de entrada (Lexer)
   └─ Parse com tabela LL(1)

3. GERAÇÃO DE ARTEFATOS
   ├─ Gerar código parser recursivo-descendente
   ├─ Gerar código visitor para AST
   ├─ Gerar ontologia Turtle (TTL)
   └─ Salvar ficheiros em /gerado
```

## ✅ Objetivos Satisfeitos

Este projeto implementa completamente todos os requisitos especificados para a Engenharia de Linguagens:

### **Primeira Fase**

| # | Objetivo | Status | Implementação |
|---|----------|--------|---|
| 1 | Detetar conflitos na gramática | ✅ | `parser_LL1.gerar_tabela_ll1()` deteta FIRST/FIRST e FIRST/FOLLOW |
| 2 | Sugerir correções à gramática | ✅ | `refactor.propor_correcoes()` aplica eliminação de recursão esquerda e fatorização |
| 3 | Gerar parser recursivo-descendente | ✅ | `generator.gerar_codigo_parser()` gera código Python com `rec_<NT>()` |
| 4 | Gerar parser Top-Down tabela-driven | ✅ | `generator.gerar_codigo_parser_table()` com runtime baseado em tabela LL(1) |
| 5a | Análise léxica | ✅ | `lexer.tokenizar_frase()` com suporte a literais e regex |
| 5b | Análise sintática | ✅ | `parser_LL1.gerar_arvore_derivacao_com_erro()` constrói árvore de derivação |
| 5c | Árvore textual | ✅ | `parser_LL1.arvore_para_texto()` formato indentado legível |
| 5d | Árvore gráfica (Mermaid) | ✅ | `parser_LL1.arvore_para_mermaid()` renderiza diagrama interativo |
| 6 | Funções de visita para AST | ✅ | `generator.gerar_codigo_visitor()` com padrão Visitor clássico |

### **Segunda Fase**

| # | Objetivo | Status | Implementação |
|---|----------|--------|---|
| 7 | Gerar ontologia OWL/RDF | ✅ | `ontology.gerar_ontologia()` formato W3C Turtle com classes/properties OWL |
| 8 | Verificar conflitos em RDF | ✅ | Conflitos registados como indivíduos OWL classe `Conflict` |
| 9 | Sugerir estrutura de visita | ✅ | `generator.gerar_codigo_visitor()` com template `visit_<NT>()` para cada NT |

---

## Arquitetura do Projeto

```
Projeto-engLinguagem/
├── core/                  # Motor de análise de gramáticas
│   ├── loader.py         # Carrega e parseia gramáticas
│   ├── lexer.py          # Análise léxica (tokenização)
│   ├── parser_LL1.py     # Cálculo de FIRST/FOLLOW, tabela LL(1), parse
│   ├── generator.py      # Gera código parser e visitor
│   ├── ontology.py       # Gera ontologia Turtle para a gramática
│   ├── refactor.py       # Propõe correções para conflitos
│   └── __init__.py
├── web/                   # Interface web Flask
│   ├── app.py            # Servidor Flask principal
│   ├── static/           # CSS, JS
│   └── templates/        # HTML templates
├── examples/             # Exemplos de gramáticas e frases
├── gerado/               # Ficheiros gerados automaticamente
├── tests/                # Testes
├── main.py              # Script CLI de exemplo
└── README.md            # Este ficheiro
```

## Componentes Principais

### 1. **Loader** (`core/loader.py`)
- **Função**: Carregar gramática em formato texto
- **Entrada**: String com produções BNF estendida
- **Saída**: Dicionário com estrutura interna (terminais, não-terminais, produções, símbolo inicial)
- **Formato aceito**:
  ```
  A -> a b | c
  B -> x y
       | z       # Alternativa em linha seguinte
  ```

### 2. **Lexer** (`core/lexer.py`)
- **Função**: Tokenização de frases de entrada
- **Entrada**: Frase texto e gramática
- **Saída**: Lista de tokens com tipo e valor
- **Suporta**: Literais (ex: `<nome>`) e regras léxicas (ex: `[a-zA-Z]+`)

### 3. **Parser LL(1)** (`core/parser_LL1.py`)
- **Função**: Análise sintática e cálculos teóricos
- **Componentes**:
  - `calcular_first()`: Conjuntos FIRST para cada não-terminal
  - `calcular_follow()`: Conjuntos FOLLOW para cada não-terminal
  - `gerar_tabela_ll1()`: Tabela de parsing LL(1) e detecção de conflitos
  - `gerar_arvore_derivacao_com_erro()`: Parse e geração de árvore de derivação
- **Saída**: Árvore de derivação (formato dict) ou mensagens de erro

### 4. **Generator** (`core/generator.py`)
- **Função**: Geração automática de código
- **Gera**:
  - `gerar_codigo_parser()`: Código Python para parser recursivo-descendente
  - `gerar_codigo_visitor()`: Esqueleto de visitor para processar AST

### 5. **Ontology** (`core/ontology.py`)
- **Função**: Gerar representação semântica em RDF/Turtle
- **Saída**: Ficheiro `.ttl` com definições da gramática em OWL/Turtle

### 6. **Refactor** (`core/refactor.py`)
- **Função**: Propor correções automáticas para conflitos LL(1)
- **Estratégias**: Eliminação de recursão esquerda, factorização de prefixos comuns

## Como Usar

### Opção 1: Interface Web (Recomendada)

#### Setup
```bash
cd web
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install flask
python app.py
```

#### Acesso
- Abrir browser em `http://localhost:5000`
- Carregar exemplo ou escrever gramática
- (Opcional) Escrever frase para testar parsing
- Sistema gera automaticamente:
  - Tabela LL(1)
  - Árvore de derivação (Mermaid)
  - Código parser e visitor
  - Arquivos em `/gerado`

#### Fluxo Web
1. **Carregar/Escrever Gramática**: Cole ou selecione exemplo
2. **Análise**: Sistema calcula FIRST, FOLLOW, tabela LL(1)
3. **Detectar Conflitos**: Se houver, sugere correções
4. **Testar Frase** (opcional): Escreva frase para validar parser
5. **Download**: Descarregue ficheiros gerados (parser.py, visitor.py, grammar.ttl)

---

### Opção 2: Interface CLI

#### Uso Básico
```bash
python main.py
```

#### Exemplo de código Python
```python
from core.loader import carregar_gramatica_da_string
from core.parser_LL1 import calcular_first, calcular_follow, gerar_tabela_ll1

# 1. Carregar gramática
gramatica_texto = """
E -> T E'
E' -> '+' T E' | ε
T -> F T'
T' -> '*' F T' | ε
F -> '(' E ')' | id | number
id -> [a-zA-Z_][a-zA-Z0-9_]*
number -> [0-9]+
"""

gramatica = carregar_gramatica_da_string(gramatica_texto)

# 2. Calcular FIRST e FOLLOW
firsts = calcular_first(gramatica)
follows = calcular_follow(gramatica, firsts)
tabela, conflitos = gerar_tabela_ll1(gramatica, firsts, follows)

# 3. Verificar resultado
print(f"Conflitos: {conflitos}")
if not conflitos:
    print("✓ Gramática LL(1) válida!")
else:
    print("✗ Há conflitos LL(1)")
    # Propor correções
    from core.refactor import propor_correcoes
    sugestao = propor_correcoes(gramatica)
    if sugestao:
        print("Sugestão de correção:")
        print(sugestao['texto_novo'])
```

---

## Exemplos de Gramáticas Incluídas

O projeto inclui 10+ exemplos pré-configurados:

| Nome | Descrição |
|------|-----------|
| **Lista** | Listas simples com elementos |
| **Pascal_sub** | Subset de Pascal com atribuições e expressões |
| **Agenda** | XML estruturado para agenda de contactos |
| **Arithmetic** | Expressões aritméticas com precedência |
| **Filesystem** | Estrutura de diretórios e ficheiros |
| **SQL** | Queries SQL simplificadas |
| **SExp** | S-expressions (Lisp-like) |
| **JSON** | Formato JSON completo |

---

## Fluxo Detalhado de um Exemplo

### Entrada
```
Gramática:
E -> T E'
E' -> '+' T E' | ε
T -> F
F -> '(' E ')' | 'x'

Frase: ( x + x )
```

### Fase 1: Análise
- **FIRST**:
  - FIRST(E) = {(, x}
  - FIRST(T) = {(, x}
  - ...
- **FOLLOW**:
  - FOLLOW(E) = {$, )}
  - ...
- **Tabela LL(1)**: Sem conflitos ✓

### Fase 2: Tokenização
```
Frase: ( x + x )
Tokens: [
  {'type': '(', 'value': '('},
  {'type': 'x', 'value': 'x'},
  {'type': '+', 'value': '+'},
  {'type': 'x', 'value': 'x'},
  {'type': ')', 'value': ')'}
]
```

### Fase 3: Parse
```
Árvore de derivação:
    E
   / \
  T   E'
  |   / \
  F  +   T
  |      |
  x      F
         |
         x
```

### Fase 4: Geração (Automática)
- `parser_generated.py`: Código Python executável
- `visitor_generated.py`: Esqueleto para processar árvore
- `grammar.ttl`: Ontologia RDF

---

## Configuração e Dependências

### Requisitos
- Python 3.8+
- Flask (apenas para web UI)

### Instalação
```bash
# Clonar repositório
git clone https://github.com/Goncaloefm11/Projeto-engLinguagem.git
cd Projeto-engLinguagem

# Para usar CLI
python main.py

# Para usar Web UI
cd web
pip install flask
python app.py
```

---

## Resolução de Problemas

### "Gramática tem conflitos LL(1)"
- Sistema propõe correções automáticas
- Clique em "Aplicar Sugestão" para aceitar
- Se persistir: Refatore manualmente eliminando recursão esquerda

### "Token não reconhecido"
- Verifique se a frase usa símbolos definidos na gramática
- Revise as regras léxicas (padrões regex)

### Ficheiros não aparecem em `/gerado`
- Verifique permissões de escrita no diretório
- Confirme que a gramática é válida (sem conflitos)

---

## Notas Técnicas

- **Parser**: Recursivo-descendente com tabela LL(1)
- **Análise Léxica**: Suporta literais (ex: `'<tag>'`) e regex (ex: `[0-9]+`)
- **Geração de Código**: Python com funções `rec_<NT>()` para cada não-terminal
- **Ontologia**: W3C Turtle format com classes e propriedades OWL

---

## Referências

- LL(1) Parsing: Dragon Book (Aho, Sethi, Ullman)
- FIRST/FOLLOW: Compiladores - Principios, técnicas e ferramentas
- Turtle Format: https://www.w3.org/TR/turtle/

---

## Autores

- Projeto de Engenharia de Linguagens
- Universidade do Minho, 2025-2026


