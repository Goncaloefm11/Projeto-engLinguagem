# Grammar Playground (GP)
### Engenharia de Linguagens — 2026

> Ambiente gráfico e computacional web para especificação, análise, otimização e transformação de Gramáticas Independentes de Contexto (GICs) baseadas no modelo preditivo **LL(1)**.

O sistema valida restrições gramaticais, gera autómatos (parsers) e árvores de derivação sintática abstrata (AST), e estende a semântica gramatical para a Web Semântica através da exportação de grafos de conhecimento e execução de queries ontológicas estruturadas.

---

## Índice

1. [Estrutura do Repositório](#estrutura-do-repositório)
2. [Funcionalidades Implementadas](#funcionalidades-implementadas)
3. [Instalação e Execução](#instalação-e-execução)
4. [Guia de Utilização](#guia-de-utilização)

---

## Estrutura do Repositório

```
grammar-playground/
│
├── app.py                       # Servidor Flask — gestão de sessões e rotas da API
│
├── core/                        # Motores de compilação, refatorização e mapeamento semântico
│   ├── loader.py                # Analisador de gramáticas textuais (formato standard + alternativas '|')
│   ├── parser_LL1.py            # Cálculo de FIRST/FOLLOW, tabelas de parsing e serialização de árvores
│   ├── lexer.py                 # Analisador léxico parametrizável baseado em RegEx
│   ├── refactor.py              # Fatorização à esquerda e remoção de recursividade à esquerda
│   ├── error_recovery.py        # Diagnóstico de erros sintáticos com heurísticas de Panic Mode
│   └── ontology.py              # Mapeador para triplos RDF/OWL (Turtle) com suporte a rdflib
│
├── gerado/                      # Artefactos gerados dinamicamente pela gramática ativa na UI
│   ├── grammar.ttl              # Grafo de conhecimento RDF/Turtle para interrogação SPARQL
│   ├── parser_generated.py      # Parser recursivo descendente autónomo exportado em Python
│   ├── visitor_auto.py          # Template estrutural de Visitor mapeado à gramática ativa
│   └── visitor_filesystem.py    # Visitor especializado para compilar árvores Filesystem em Bash
│
└── templates/
    └── index.html               # Interface web interativa (D3.js + Mermaid + Highlight.js)
```

---

## Funcionalidades Implementadas

### 1. Núcleo de Análise Sintática LL(1) — `core/`

| Componente | Descrição |
|---|---|
| **Cálculo de Símbolos Diretores** | Computação automática de FIRST e FOLLOW, com suporte nativo a cadeias anuláveis e derivações em vazio (ε) |
| **Deteção de Conflitos** | Identificação em tempo real de ambiguidades na tabela preditiva — conflitos FIRST/FIRST e FIRST/FOLLOW |
| **Refatorização Automática** | Remoção de recursividade à esquerda (direta) e fatorização de prefixos comuns |
| **Recuperação de Erros** | Modo Panic Mode com mensagens humanizadas, inspeção de stack vs. lookahead e rotina de autocorreção |

### 2. Geração de Código e Compilação Dinâmica — `gerado/`

- **Dual-Parsing Infrastructure** — valida e constrói a árvore sintática com tabela genérica em memória *ou* exporta um ficheiro Python puro com recursão descendente (`parser_generated.py`)
- **Visitors Adaptativos** — gera o padrão Visitor mapeando cada não-terminal a uma função dedicada, facilitando tradução ou interpretação da árvore de derivação

### 3. Integração com a Web Semântica — `core/ontology.py`

- **Mapeamento OWL/RDF** — traduz metadados da linguagem analisada para triplos semânticos, tipificando instâncias de `Grammar`, `Production`, `Terminal` e `NonTerminal`, incluindo propriedades como `firstSet` e `followSet`
- **Consola SPARQL Embutida** — permite interrogar a gramática semanticamente via queries em tempo real diretamente no painel web

---

## Instalação e Execução

**Pré-requisito:** Python 3.10+

```bash
# 1. Instalar dependências
pip install Flask rdflib

# 2. Iniciar o servidor
python app.py
```

A aplicação fica disponível em `http://localhost:5000`.

---

## Guia de Utilização

### Passo 1 — Definir a Gramática
Na caixa de texto principal, escreva a gramática ou carregue um dos exemplos disponíveis no menu dropdown:

| Exemplo | Descrição |
|---|---|
| `Pascal_sub` | Subconjunto da linguagem Pascal |
| `JSON` | Gramática JSON completa |
| `SQL` | Subconjunto de SQL |
| `Filesystem` | Estrutura de sistema de ficheiros |

Clique em **Analisar** para processar.

### Passo 2 — Estudar o Lookahead
A app preenche automaticamente as tabelas de FIRST, FOLLOW e a matriz de parsing LL(1), com destaque visual para conflitos. Se existirem conflitos, clique em **"Ver Sugestões de Correção"** para aplicar refatorização automática.

### Passo 3 — Analisar Expressões
Introduza uma frase na caixa de input sintático:

- **Frase válida** — o sistema gera o parse e desenha a árvore em três formatos síncronos:
  - Grafo visual e interativo (D3.js)
  - Representação textual indentada
  - Notação Mermaid

- **Frase com erros** — o parser interrompe e apresenta um diagnóstico detalhado (tokens esperados vs. recebidos). O botão **"Corrigir Frase"** permite retificar o input autonomamente.

### Passo 4 — Ontologia e SPARQL
No separador **Ontologia**, visualize o ficheiro `grammar.ttl` gerado. Use o seletor de queries predefinidas para interrogar a gramática semanticamente — por exemplo, pesquisar produções com elementos anuláveis ou listar todos os não-terminais. Os resultados aparecem formatados em tabela.


## Autores 
### Desenvolvimento e Implementação: 
Gonçalo Magalhães PG61524
Eduarda Pereira PG61516
Tomas Pinto A104448
### Unidade Curricular: 
Engenharia de Linguagens (Projeto 2026)   
### Especificação do Projeto e Equipa Docente: 
José Carlos Ramalho