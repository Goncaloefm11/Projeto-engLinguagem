# Grammar Playground (GP) - Engenharia de Linguagens 2026

Ambiente gráfico desenvolvido para analisar gramáticas independentes de contexto do tipo **LL(1)**.

## Funcionalidades Implementadas

### 1. Modelação da Gramática
- **Identificação Automática:** Separação entre Terminais e Não-Terminais.
- **Suporte a Epsilon:** Tratamento de produções vazias (`e`).
- **Exemplo Pascal:** Processamento completo do subconjunto da linguagem Pascal.

### 2. Motor de Análise LL(1)
- **Cálculo de Conjuntos:** Geração automática de FIRST e FOLLOW.
- **Tabela de Parsing:** Construção da matriz de decisão para análise sintática.
- **Deteção de Conflitos:** Identificação de conflitos FIRST/FIRST e FIRST/FOLLOW.

### 3. Interface e Ferramentas
- **Ambiente Web:** Interface interativa para inserção de gramáticas e visualização de tabelas.
- **Analisador de Frases:** Validação de cadeias de entrada (tokens) baseada na tabela gerada.

## Instalação e Uso

1. Instalar Flask: `pip install flask`
2. Executar: `python app.py`
3. Aceder: `http://127.0.0.1:5000`

## 📂 Estrutura
- `core/`: Lógica algorítmica e matemática.
- `templates/`: Interface gráfica.
- `app.py`: Servidor e rotas do projeto.
