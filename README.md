# Grammar Playground (Projeto de Engenharia de Linguagens)

Resumo rápido

Este repositório serve como um "playground" para especificar gramáticas e analisar propriedades LL(1). Foi desenvolvido um front-end simples (Flask) onde o utilizador pode colar uma gramática (formato `NT -> prod1 | prod2`), calcular FIRST/FOLLOW, gerar a tabela LL(1), obter sugestões de correção para conflitos e tentar parsear uma frase de entrada (gerar a árvore de derivação).

Estado atual (o que já está feito)

- Interface web (Flask) em `web/app.py` com templates em `web/templates/index.html`:
  - formulário para colar gramática e frase de entrada.
  - exibição da tabela LL(1), relatório de conflitos e árvore de derivação (desenhada com D3).
  - botão "Sugerir Correções" que mostra uma gramática transformada (remoção de recursividade à esquerda e fatorização) e botão "Aplicar" para copiar a sugestão para a gramtica.

- Leitura e representação da gramática: `core/loader.py` lê a gramática textual para a estrutura interna (dicionário com `producoes`, `terminais`, `nao_terminais`, `inicial`).

- Análise LL(1): `core/parser_LL1.py` implementa:
  - `calcular_first(gramatica)` — calcula conjuntos FIRST.
  - `calcular_follow(gramatica, firsts)` — calcula conjuntos FOLLOW.
  - `gerar_tabela_ll1(gramatica, firsts, follows)` — constrói a tabela LL(1) e reporta conflitos (FIRST/FIRST, FIRST/FOLLOW).
  - `gerar_arvore_derivacao(tokens, gramatica, tabela)` — parser orientado pela tabela que constrói a árvore de derivação (retorna `None` se a frase não for aceite).
  - `validar_frase(tokens, gramatica, tabela)` — wrapper que tenta parse e devolve `(aceite, arvore|mensagem)`.

- Sugeridor de correções: `core/refactor.py` contém rotinas básicas para remover recursividade à esquerda e fatorizar prefixos comuns, e uma função `propor_correcoes(gramatica)` que devolve sugestões de gramática textual.

- Geração de parser em código: `core/generator.py` (esqueleto) que gera código de parser recursivo descendente a partir da tabela.

Como executar a aplicação localmente

1. Instalar dependências (o `pyproject.toml` já lista Flask e Lark; se quiseres um venv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # se existir, ou pip install flask lark
```

2. Iniciar a app (a partir da pasta `web`):

```bash
cd web
python3 app.py
```

3. Abrir no browser: http://127.0.0.1:5000

O que testar na UI

- Colar uma gramática simples e clicar "Analisar Tudo".
- Se houver conflitos LL(1), aparecerá a lista de conflitos e o botão "Sugerir Correções".
- Experimentar uma frase de entrada; o sistema tokeniza automaticamente (`1` -> `number`) conforme a gramática conter esses terminais.
- Se a frase for aceite, a árvore de derivação é mostrada (os nós terminais ainda NÃO mostram `tipo : valor`, p.ex. `number : 1`).

Observações técnicas e limitações atuais

- O loader é minimal — assume que cada linha com `->` define produções; espaços e capitalização são significativos.

- Lexer simples:
  - Reconhece inteiros e identificadores básicos. Floats e símbolos complexos podem precisar de regras adicionais.
  - Mapeia `1` → `number` apenas se a gramática declarar `number` como terminal. Caso a gramática não declare `number`, o token será tratado como desconhecido e a UI avisará.

- Parser/árvore:
  - O parser orientado pela tabela assume que a tabela LL(1) está correta; se a gramática ou cálculo FIRST/FOLLOW tiver erros, o parser recusará a frase (com razão) MAS NAO DÁ ERRO ALGO QUE DEVE SER IMPLEMENTADO AINDA.

- Sugeridor de correções (refactor): faz transformações automáticas simples (remoção recursividade à esquerda e fatorização) mas não garante versão final perfeita; casos complexos podem precisar de intervenção manual.

O que falta / próximos passos (mapeado para o PDF / Etapa 1→seguinte)

Abaixo listo funcionalidades/entregáveis que o PDF sugere e o estado atual (feito / parcial / falta):

1) Especificação manual da gramática de exemplo — FEITO.

2) Cálculo FIRST/FOLLOW e tabela LL(1) manual — FEITO (implementado e exibido automaticamente).

3) Deteção de conflitos FIRST/FIRST e FIRST/FOLLOW — FEITO (a função `gerar_tabela_ll1` retorna conflitos que são mostrados na UI).

4) Sugestões automáticas para tornar a gramática LL(1) (remoção recursividade / fatorização) — PARCIAL (implementado em `core/refactor.py`, mas carece de testes extensivos e de um mecanismo de validação pós-transformação mais robusto).

5) Parser que gera árvore de derivação a partir da tabela LL(1) — PARCIAL/FEITO (existe um parser orientado por tabela; verifica a aceitação e constrói a árvore, mas há cenários limites que podem precisar de logging e visualização adicional para debug). Testes com várias gramáticas serão úteis.FALTA O ENVIO DE ERRO DA FRASE DE ENTRADA PARA PRODUZIR A ARVORE

6) Gerador de parser (código em Python) — FEITO?
 (há um `core/generator.py` que produz um parser de exemplo; necessita de polimento e testes).

7) Testes automatizados e cobertura — FALTA (sugerido: criar testes pytest para `calcular_first`, `calcular_follow`, `gerar_tabela_ll1` e casos de parsing). Está listado como dependência dev no `pyproject.toml`.

8) Documentação final e relatório por etapas — PARCIAL (este README + `docs/etapa1.md` cobrem parte; falta um documento que descreva o design global, a API dos módulos e como estender o lexer/gerador).

Sugestões concretas para finalizar o projecto (curto prazo)

  - Gramática sem conflitos (pequena), gramática com recursividade à esquerda, gramática com produções anuláveis.
- Melhorar o lexer:
  - Reconhecer floats, negativos, e mapear automaticamente `number` mesmo quando não declarado (opcional).
  - Reconhecer operadores compostos (`:=`, `<=`, etc.).
- Adicionar uma vista de "debug" (no template) que mostre:
  - tokens gerados pelo lexer,
  - FIRST/FOLLOW conjuntos,
  - para cada passo do parse, a produção escolhida (útil para explicar por que a árvore foi construída assim).
- Polir `core/generator.py` para gerar código executável com docstrings e testes simples.
- Fazer um pass de UI/UX: mensagens de erro mais claras, highlight das produções envolvidas no conflito.

Ficheiros principais e responsabilidades

- web/app.py — controladora Flask e coordenação do fluxo (loader → calcular_first → calcular_follow → gerar_tabela_ll1 → validar_frase → render).
- web/templates/index.html — frontend (formulário, exibição da tabela, árvore D3, botões de sugestão/aplicar).
- core/loader.py — parser simples da gramática textual para estrutura interna.
- core/parser_LL1.py — lógica FIRST/FOLLOW/tabela/parser/árvore.
- core/refactor.py — transformações automáticas (remoção de recursividade à esquerda, fatorização) e proposição de mudanças.
- core/generator.py — gerador de código do parser (esqueleto / funcionalidade inicial).

