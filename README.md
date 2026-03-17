# Grammar Playground

Projeto de Engenharia de Linguagens, 2.º semestre de 2026.

A Grammar Playground é uma aplicação web para trabalhar com gramáticas independentes de contexto com foco em LL(1). O sistema permite:
O sistema cumpre todos os requisitos exigidos no guião:
- ✅ **Meta-Gramática Formal:** Análise estrita de gramáticas de input usando um parser formal (EBNF), rejeitando sintaxes inválidas.
- ✅ **Conceitos LL(1):** Cálculo automático de produções anuláveis (ε) e conjuntos `FIRST` e `FOLLOW`.
- ✅ **Tabela LL(1) e Deteção de Conflitos:** Construção da tabela de parsing e identificação de conflitos `FIRST/FIRST` e `FIRST/FOLLOW`.
- ✅ **Sugestão de Correções:** O sistema analisa a origem do conflito e sugere soluções (ex: Fatoração à esquerda).
- ✅ **Geração de Parsers:** Geração do código fonte (em Python e JavaScript) para Parsers **Recursivos Descendentes**.
- ✅ **Árvores de Derivação:** Análise de frases de input com geração de árvore de derivação em formato Textual, JSON e Gráfico (usando Mermaid.js).
- ⬜ **Geração de Parsers:** Geração do código fonte (em Python ) para Parsers **Recursivos Top-Down**. 
- ⬜ **Geração de Código (Visitor):** Injeção dinâmica de funções de visita em código Python via interface Web para travessia da árvore e geração de resultados/código.
---

- validar gramáticas escritas pelo utilizador;
- calcular `NULLABLE`, `FIRST` e `FOLLOW`;
- construir a tabela LL(1);
- detetar e classificar conflitos;
- sugerir correções para alguns conflitos;
- gerar parser descendente recursivo em Python;
- testar frases de entrada e visualizar a árvore de derivação.

## Estado Atual

Neste momento, o backend já suporta:

- parser formal da meta-gramática;
- análise LL(1) completa;
- deteção de conflitos `FIRST/FIRST`, `FIRST/FOLLOW` e `LEFT-RECURSION`;
- geração de parser descendente recursivo em Python;
- parsing de frases com construção de árvore usando Lark;
- exportação textual, JSON, Mermaid e D3 da árvore;
- API web em Flask.

Neste momento, o projeto não expõe na interface:

- geração de parser table-driven pela UI;
- visitors gerados automaticamente;
- ontologia OWL/RDF.

## Estrutura do Projeto

```text
Projeto-engLinguagem/
├── core/
│   ├── grammar.py
│   ├── ll1_analyzer.py
│   ├── parser_generator.py
│   ├── derivation_tree.py
│   ├── lark_parser.py
│   └── visitor.py
├── web/
│   ├── app.py
│   ├── templates/index.html
│   └── static/js/script.js
├── grammars/
├── tests/
├── run.py
└── pyproject.toml
```

## Arquitetura

O backend está dividido em duas camadas.

- `web/`: camada HTTP e integração com a interface.
- `core/`: lógica de compiladores e processamento das gramáticas.

O fluxo principal é este:

1. O frontend envia uma gramática ou uma frase para um endpoint Flask.
2. O `web/app.py` chama os módulos do `core`.
3. O `core/grammar.py` transforma texto em objetos `Grammar`, `Symbol` e `Production`.
4. O `core/ll1_analyzer.py` calcula propriedades LL(1) e conflitos.
5. Dependendo da funcionalidade, o backend:
	- gera código Python com `core/parser_generator.py`, ou
	- constrói uma árvore de derivação com `core/lark_parser.py`.
6. O resultado é devolvido em JSON para a interface.

## Backend: Funcionalidade por Módulo

### `core/grammar.py`

Este módulo implementa o modelo interno da gramática e o parser da meta-gramática.

Responsabilidades principais:

- definir os tipos de símbolo com `SymbolType`;
- representar símbolos com a classe `Symbol`;
- representar produções com a classe `Production`;
- armazenar a gramática completa com a classe `Grammar`;
- validar coerência estrutural da gramática;
- converter texto introduzido pelo utilizador numa instância de `Grammar`.

Como funciona o parsing da gramática:

- aceita setas `→` e `->`;
- aceita alternativas com `|`;
- aceita epsilon como `ε`, `epsilon` ou `ɛ`;
- identifica não-terminais a partir das cabeças das produções;
- classifica como terminais símbolos em minúsculas, operadores e lexemas especiais;
- define como símbolo inicial a cabeça da primeira produção.

Validações feitas por `Grammar.validate()`:

- existência de símbolo inicial;
- existência de produções;
- garantia de que cada não-terminal tem pelo menos uma produção;
- garantia de que cabeças de produção são não-terminais;
- verificação de que todos os símbolos usados estão definidos.

### `core/ll1_analyzer.py`

Este módulo implementa a análise LL(1).

Estruturas principais:

- `LL1Table`: tabela de parsing indexada por `(não-terminal, terminal)`;
- `Conflict`: descrição estruturada de cada conflito detetado;
- `LL1Analyzer`: motor principal da análise.

Passos executados por `LL1Analyzer.analyze()`:

1. calcula os símbolos anuláveis (`NULLABLE`);
2. calcula os conjuntos `FIRST`;
3. calcula os conjuntos `FOLLOW`;
4. preenche a tabela LL(1);
5. deteta conflitos.

Tipos de conflito atualmente tratados:

- `LEFT-RECURSION`: recursividade à esquerda imediata;
- `FIRST/FIRST`: duas produções competem pelo mesmo lookahead;
- `FIRST/FOLLOW`: uma produção anulável colide com o `FOLLOW` do mesmo não-terminal.

Detalhes importantes do backend:

- conflitos de recursividade à esquerda são reportados com prioridade para não ficarem mascarados por conflitos de tabela;
- o analisador pode devolver sugestões textuais e, em alguns casos, uma gramática corrigida;
- também pode gerar uma frase-exemplo a partir de uma gramática sugerida.

Esta análise é usada por:

- `/analyze`, para mostrar o relatório completo;
- `/generate-parser`, para bloquear geração quando existem conflitos;
- `/parse`, para tentar sugerir uma frase de exemplo quando o parsing falha.

### `core/parser_generator.py`

Este módulo gera código de parser a partir de uma gramática LL(1).

#### `RecursiveDescentGenerator`

O gerador produz um parser em Python:

- estado global com `tokens` e `pos`;
- funções auxiliares `lookahead()`, `match()` e `error()`;
- uma função por não-terminal;
- uma função `parse(input_tokens)` como ponto de entrada;
- árvore sintática representada por tuplos aninhados.

O despacho entre produções é gerado com base em `FIRST` e `FOLLOW`.

#### `TableDrivenGenerator`

# TODO.

### `core/lark_parser.py`

Este módulo é o backend principal da funcionalidade de parsing de frases.

Responsabilidades:

- converter a gramática interna para EBNF compatível com Lark;
- criar um parser Lark a partir da gramática do utilizador;
- fazer parse da frase de input;
- converter a árvore do Lark para uma estrutura própria (`LarkTreeNode`);
- exportar a árvore em vários formatos.

#### `LarkGrammarConverter`

Converte a gramática do utilizador para regras Lark.

Faz, entre outras coisas:

- sanitização de nomes de regras e terminais;
- mapeamento de operadores como `:=`, `+`, `(`, `)` e `;`;
- criação de regex para `id` e `number`;
- inserção de `%ignore WS`.

#### `LarkTreeBuilder`

Executa o parse da frase e tenta criar um parser Lark:

- primeiro com `lalr`;
- em fallback com `earley`, caso a gramática não seja aceite no primeiro modo.

#### `build_derivation_tree_lark()`

É a função de alto nível usada pelo endpoint `/parse`.

Devolve um dicionário com:

- `success`
- `errors`
- `tree`
- `tree_text`
- `tree_mermaid`
- `tree_d3`
- `lark_grammar`
- `derivation_steps`

Nota: `derivation_steps` é devolvido vazio neste caminho, porque o Lark não fornece a derivação passo a passo neste formato.

### `core/derivation_tree.py`

Este módulo completa as árvores de derivação e a implementação LL(1) manual baseada em stack.

Componentes principais:

- `tree_to_mermaid(tree)`: converte árvores em tuplos para Mermaid;
- `tree_to_text(tree)`: converte árvores em tuplos para texto indentado;
- `SimpleTokenizer`: tokenizador simples baseado nos terminais da gramática;
- `DerivationTreeBuilder`: parser LL(1) manual com pilha e construção explícita de árvore;
- `TreeNode`: representação de nós para esse modo manual.
O caminho usado pela rota web de parsing é o baseado em Lark.

### `core/visitor.py`

Este módulo define uma classe base `TreeVisitor` para percorrer árvores de derivação.

Funcionamento:

- tenta resolver dinamicamente um método como `visit_Expr` ou `visit_StmtList_prime`;
- se esse método não existir, usa `generic_visit()`;
- o comportamento por omissão percorre todos os filhos e concatena os resultados;
- em folhas terminais, devolve o valor do token.

Estado atual:

- é uma infraestrutura base para extensões futuras;
- não está integrada de forma explícita em nenhum endpoint Flask.

## Backend HTTP: Endpoints

### `GET /`

Renderiza a página principal `index.html` e injeta exemplos de gramáticas.

### `POST /analyze`

Recebe JSON com:

```json
{ "grammar": "..." }
```

Fluxo interno:

1. faz parse da gramática com `GrammarParser.parse()`;
2. valida a estrutura com `grammar.validate()`;
3. executa `LL1Analyzer`;
4. devolve o relatório completo da análise.

Usado para mostrar:

- terminais e não-terminais;
- produções;
- `NULLABLE`, `FIRST` e `FOLLOW`;
- tabela LL(1);
- conflitos e sugestões.

### `POST /generate-parser`

Recebe JSON com:

```json
{ "grammar": "...", "language": "python" }
```

Fluxo interno:

1. faz parse e valida a gramática;
2. corre a análise LL(1);
3. bloqueia a geração se existirem conflitos;
4. gera código com `RecursiveDescentGenerator`.

Resposta de sucesso:

- `code`: código do parser gerado;
- `type`: atualmente `recursive`;
- `language`: linguagem pedida.

Observação:

- embora o endpoint aceite o campo `language`, o gerador suporta apenas Python neste momento.

### `POST /parse`

Recebe JSON com:

```json
{ "grammar": "...", "input": "..." }
```

Fluxo interno:

1. chama `build_derivation_tree()`;
2. esse wrapper delega para `build_derivation_tree_lark()`;
3. em caso de sucesso, devolve árvore e formatos de visualização;
4. em caso de falha, tenta ainda construir `suggested_example` usando o analisador LL(1).

O `suggested_example` segue esta lógica:

- tenta usar primeiro uma gramática corrigida presente num conflito;
- se isso não existir, tenta gerar um exemplo a partir da gramática original;
- se alguma etapa falhar, devolve string vazia sem bloquear a resposta.

### `GET /examples`

Devolve as gramáticas de exemplo pré-carregadas no backend.

### `POST /api/grammar/validate`

Recebe uma gramática e devolve apenas validação sintática e estrutural, sem relatório LL(1) completo.

## Fluxo de Utilização na Interface

### 1. Analisar gramática

O frontend envia o texto para `/analyze`. O backend devolve um relatório completo que a UI apresenta em:

- conjuntos `FIRST` e `FOLLOW`;
- tabela LL(1);
- conflitos;
- sugestões de correção.

### 2. Construir árvore de derivação

O frontend envia gramática e frase para `/parse`. O backend usa Lark para tentar o parse e devolve:

- árvore em JSON;
- versão textual;
- diagrama Mermaid;
- gramática Lark gerada.

### 3. Gerar parser

O frontend envia a gramática para `/generate-parser`. Se a gramática for LL(1), o backend devolve o código fonte do parser descendente recursivo em Python.

## Testes

O projeto contém testes em `tests/` para comportamentos importantes do backend, incluindo:

- categorização de conflitos;
- segurança das sugestões para `FIRST/FOLLOW`;
- correções de padrões de lista;
- requisitos da UI perante conflitos LL(k);
- validações de fase 1.


## Limitações Atuais

- o parsing de frases usado pela web depende de Lark e não do parser LL(1) manual de `DerivationTreeBuilder`;
- o gerador table-driven existe, mas ainda não está integrado na aplicação web;
- a infraestrutura de `visitor` existe, mas ainda não foi ligada a uma funcionalidade da interface;

## Resumo Técnico

Em termos de backend, o projeto já tem três blocos fortes:

- um parser formal da gramática de entrada;
- um analisador LL(1) com deteção e explicação de conflitos;
- um pipeline de parsing e visualização de árvores apoiado por Lark.
