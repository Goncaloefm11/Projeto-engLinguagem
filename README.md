Grammar Playground (GP) - Engenharia de Linguagens 2026
Este projeto consiste num ambiente gráfico desenvolvido para analisar e trabalhar com gramáticas independentes de contexto do tipo LL(1), conforme os requisitos da UC de Engenharia de Linguagens (2º semestre de 2026).


🚀 Estado Atual do Projeto (Fase 1)
Até ao momento, implementámos o "motor" central do sistema, permitindo a transição do modelo teórico para uma interface funcional. O sistema já é capaz de:

1. Modelação da Gramática

Extração de Símbolos: Identificação automática de símbolos terminais e não-terminais.

Gestão de Produções: Estruturação de regras de derivação, incluindo o suporte para o símbolo vazio (ϵ).

Compatibilidade: O sistema processa com sucesso a gramática de exemplo da linguagem Pascal fornecida.


2. Análise LL(1) Automática

Conjuntos FIRST: Cálculo dos terminais que podem iniciar as derivações de cada não-terminal.

Conjuntos FOLLOW: Cálculo dos símbolos que podem aparecer imediatamente à direita de um não-terminal.

Tabela de Parsing: Construção da tabela de análise sintática LL(1) baseada nos conjuntos calculados.

3. Deteção de Conflitos e Validação

Identificação de Erros: O sistema deteta automaticamente conflitos FIRST/FIRST e FIRST/FOLLOW para produções anuláveis.


Interface Web: Integração de toda a lógica numa interface gráfica que permite o input de gramáticas e visualização imediata de resultados e conflitos.

🛠️ Como Utilizar
Pré-requisitos

Python 3.x instalado.

Flask (instalar via pip install flask).

Execução

Clona o repositório ou descarrega os ficheiros.

No terminal, dentro da pasta do projeto, executa:

Bash
python app.py
Abre o browser em: http://127.0.0.1:5000

📂 Organização do Código
app.py: Servidor Flask que gere a interface Web e a comunicação com o backend.

core/parser_logic.py: O núcleo algorítmico onde residem os cálculos de FIRST, FOLLOW e a construção da Tabela.

core/utils.py: Funções auxiliares para leitura e processamento de gramáticas a partir de texto ou ficheiros.

templates/: Contém a estrutura HTML/Tailwind para a visualização gráfica dos dados.

📝 Próximos Objetivos (Roadmap)
[ ] Análise de Frases: Construção da árvore de derivação em formato textual e gráfico.

[ ] Geração de Parser: Criar o parser recursivo descendente correspondente à gramática inserida.

[ ] Fase 2: Início da representação em ontologias OWL/RDF.

Equipa: Gonçalo & Colega

Docente: José Carlos Ramalho Data de Início: 2026-02-02
