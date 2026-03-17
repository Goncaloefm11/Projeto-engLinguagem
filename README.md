# Grammar Playground (GP)
**Projeto de Engenharia de Linguagens - 2º Semestre 2026**  
Um ambiente gráfico para analisar e trabalhar com gramáticas independentes de contexto do tipo LL(1).

## Fase 1

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

### Fase 2 
- ⬜ Gerar uma ontologia OWL/RDF para a gramática introduzida
- ⬜ Verificar a existência de conflitos nesta representação
- ⬜ Sugerir a estrutura de uma função visita para geração de código


## Execução
### Iniciar o Servidor Web
```bash
python run.py
```
Ou:
```bash
cd web
python app.py
```

Disponível em **http://localhost:5000**

## 🏗️ Arquitetura do Sistema
O projeto adota uma arquitetura modular que separa a lógica do compilador (Core) da interface gráfica (Web).

### Estrutura de Diretórios
```text
grammar_playground/
├── core/                       # Núcleo da lógica do compilador
│   ├── grammar.py              # Parser da Meta-Gramática e Modelos Base
│   ├── ll1_analyzer.py         # Algoritmos FIRST/FOLLOW e Tabela LL(1)
│   ├── parser_generator.py     # Gerador de Código (Recursivo Descendente)
│   ├── derivation_tree.py      # Construção da Árvore (Wrapper Lark)
│   └── lark_parser.py          # Conversor para EBNF do Lark
├── web/                        # Interface Web Frontend/Backend
│   ├── app.py                  # Servidor Flask (Rotas da API)
│   ├── static/
│   │   ├── css/style.css       # Estilos (UI/UX)
│   │   └── js/script.js        # Lógica de interface (Fetch API)
│   └── templates/
│       └── index.html          # View principal (Pills + Tabs)
└── test_phase1.py     # Testes de integração rigorosos (Asserts)
```


# Como funciona
1. **Meta-Gramática**: Quando se introduz uma gramática na caixa de texto, o core/grammar.py não usa apenas Expressões Regulares. Implementa também um analisador descendente rigoroso, validando regras como cabeças únicas, setas (→ ou ->) e separadores lógicos (|).

2. **Análise LL(1)**: O analisador constrói os conjuntos e preenche a tabela no ficheiro ll1_analyzer.py. Se múltiplas produções caírem na mesma célula da tabela, a classe Conflict é instanciada para descrever o problema e sugerir a resolução.

3. **Árvores de Derivação**: O sistema compila, em background, a gramática do utilizador para EBNF compatível com a biblioteca Lark do Python, que trata de fazer o parse da frase. O resultado é percorrido e transformado em nós nativos, gerando texto e os diagramas Mermaid.

## Execução de Testes
Para provar que todos os requisitos funcionam, desenvolvemos um guião rigoroso de testes:
```Bash
python test_phase1.py
```
## Como usar interface Web
O menu lateral está dividido em 3 secções para guiar o fluxo de trabalho:

1. **Gramática**: Digite uma gramática (ou escolha o subconjunto de Pascal nos exemplos) e clique em Analisar Gramática. Isto vai gerar os conjuntos FIRST/FOLLOW e a Tabela LL(1) no painel da direita.

2. **Frase**: Introduza uma frase válida para a gramática selecionada (ex: id := id + number) e clique em Construir Árvore de Derivação. O gráfico aparecerá na direita.

3. **Parsers**: Escolha a linguagem-alvo (Python/JS). O código-fonte do parser Recursivo Descendente será gerado.
