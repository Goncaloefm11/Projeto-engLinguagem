# Grammar Playground (GP) - Engenharia de Linguagens 2026

[cite_start]Este projeto consiste no desenvolvimento de um ambiente gráfico para analisar e trabalhar com gramáticas independentes de contexto do tipo **LL(1)**[cite: 7]. [cite_start]O objetivo é fornecer uma ferramenta completa para a especificação de gramáticas, deteção de conflitos e geração de parsers[cite: 8, 9, 10].

## Estado Atual do Projeto (Fase 1)

Até ao momento, implementámos o motor central do sistema, permitindo a transição do modelo teórico para uma interface funcional. O sistema já cumpre os seguintes requisitos:

### 1. Modelação da Gramática
- [cite_start]**Estrutura Base:** Identificação automática de símbolos terminais, não-terminais e produções[cite: 22].
- [cite_start]**Símbolos Específicos:** Suporte total para o símbolo vazio (epsilon `e`)[cite: 32].
- [cite_start]**Exemplo Real:** O sistema já processa com sucesso o subconjunto da linguagem Pascal fornecido no enunciado [cite: 25, 26, 27-40].

### 2. Análise LL(1) Automática
- [cite_start]**Conjuntos FIRST:** Cálculo dos terminais que iniciam as derivações[cite: 23].
- [cite_start]**Conjuntos FOLLOW:** Cálculo dos símbolos que podem aparecer à direita de um não-terminal[cite: 23].
- [cite_start]**Tabela de Parsing:** Construção da matriz de análise sintática LL(1) baseada nos conjuntos anteriores[cite: 23].

### 3. Deteção de Conflitos e Validação
- [cite_start]**Identificação de Erros:** O sistema deteta conflitos **FIRST/FIRST** e **FIRST/FOLLOW** para produções anuláveis[cite: 24].
- [cite_start]**Interface Web:** Integração de toda a lógica numa interface gráfica Web que permite o input de gramáticas e visualização imediata[cite: 19].

---

## Como Utilizar

### Pré-requisitos
- **Python 3.x** instalado.
- **Flask** (instalar via `pip install flask`).

### Execução
1. Clona o repositório ou descarrega os ficheiros.
2. No terminal, dentro da pasta do projeto, executa:
   ```bash
   python app.py
