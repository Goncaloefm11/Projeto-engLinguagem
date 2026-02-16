# Grammar Playground - Quick Start Guide

## 🚀 Início Rápido (5 minutos)

### Passo 1: Instalar Dependências
```bash
pip install -r requirements.txt
```

### Passo 2: Iniciar a Aplicação
```bash
python app.py
```

### Passo 3: Abrir no Navegador
Abra `http://localhost:5000` no seu navegador

---

## 📝 Exemplo: Analisar a Gramática Pascal

1. **Cole a gramática no painel esquerdo:**

```
Program → StmtList;
StmtList → Stmt StmtList' | ε;
StmtList' → ; Stmt StmtList' | ε;
Stmt → id := Expr;
Expr → Term Expr';
Expr' → + Term Expr' | ε;
Term → id | number;
```

2. **Clique em "Analisar Gramática"**

3. **Veja os resultados:**
   - ✓ Gramática LL(1) válida
   - Conjuntos FIRST e FOLLOW calculados
   - Tabela de parsing gerada
   - Sem conflitos detectados

---

## 🔍 Exemplo: Analisar uma Frase

1. **Insira uma frase:**
```
id := number
```

2. **Clique em "Construir Árvore de Derivação"**

3. **Veja a árvore gerada:**
```
Program
  StmtList
    Stmt
      id
      :=
      Expr
        Term
          id | number
```

---

## 📊 Compreender os Resultados

### FIRST Sets
Mostra quais símbolos podem iniciar uma derivação:
- `FIRST(Expr) = { id, number }`
- `FIRST(Expr') = { +, ε }`

### FOLLOW Sets
Mostra quais símbolos podem vir após cada não-terminal:
- `FOLLOW(Stmt) = { ;, $ }`
- `FOLLOW(Expr') = { ;, $ }`

### LL(1) Table
Tabela de decisão para parsing dirigido por tabela:
- Linha: Não-terminal
- Coluna: Terminal
- Célula: Qual produção usar

### Conflitos
Se detectados, mostram ambiguidades na gramática que impedem análise LL(1)

---

## 🛠️ Testando com Test Script

```bash
python test_grammar_playground.py
```

Isso executará testes automáticos e verificará se tudo está funcionando.

---

## 📚 Exemplos Pré-configurados

### Pascal Subset
Gramática para um subconjunto de Pascal com:
- Atribuições: `id := Expr`
- Expressões: `Term + Term`
- Múltiplas declarações separadas por `;`

### Expressões Matemáticas
Gramática para expressões com:
- Operadores: `+` e `*`
- Precedência correta
- Parênteses

### Listas Simples
Gramática para listas separadas por vírgulas

---

## 💡 Dicas Importantes

### Formato de Gramática
✓ Use `→` (seta para a direita)  
✓ Use `|` para alternativas  
✓ Use `ε` para produções vazias  
✓ Termine com `;`

Exemplos:
```
Correto:   A → B C | ε;
Errado:    A -> B C | eps.
Errado:    A => B C | e
```

### Nomes de Símbolos
✓ **Não-terminais**: Letra maiúscula (ex: `A`, `Expr`, `Term`)  
✓ **Terminais**: Letra minúscula (ex: `id`, `number`, `+`)

### Símbolos Especiais
- `;` (ponto-e-vírgula): Termina uma produção
- `|` (barra vertical): Separa alternativas
- `ε` (epsilon): Produção vazia
- `→` (seta): Separa cabeça de corpo

---

## ⚙️ Estrutura de Arquivos Criados/Modificados

```
Projeto-engLinguagem/
├── app.py                        ✨ NOVO - Flask app principal
├── requirements.txt              ✨ NOVO - Dependências
├── test_grammar_playground.py    ✨ NOVO - Test suite
├── GRAMMAR_PLAYGROUND_README.md  ✨ NOVO - Documentação completa
├── QUICKSTART.md                 ✨ NOVO - Este arquivo
│
├── deteta_vuln/
│   ├── grammar_analyzer.py       ✨ NOVO - Analisador LL(1)
│   ├── parse_tree_builder.py     ✨ NOVO - Construtor de árvores
│   ├── grammar_language.lark     ✨ NOVO - Gramática Lark
│   └── ... (arquivos existentes)
│
├── templates/
│   └── index.html                ✏️ ATUALIZADO - Interface moderna
│
└── static/
    └── (vazio - para CSS/JS futuros)
```

---

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask lark
```

### Erro: "Address already in use"
Mude a porta:
```python
# No final do app.py:
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Use 5001 em vez de 5000
```

### Apresentação: "Grammar parsing failed"
Verifique o formato:
- Cada produção termina com `;`?
- Usa `→` e não `->`?
- Não-terminais começam com maiúscula?
- Terminais começam com minúscula?

---

## 📖 Próximas Etapas

Depois de compreender os básicos:

1. **Criar sua própria gramática**
   - Pense em uma linguagem simples
   - Defina suas produções
   - Analise com o Grammar Playground

2. **Testar com sentenças complexas**
   - Veja como o parser constrói a árvore
   - Entenda a derivação

3. **Entender conflitos**
   - Modifique a gramática para criar conflitos
   - Veja como aparecem na análise
   - Aprenda a corrigi-los

4. **Aprofundar em LL(1)**
   - Leia sobre análise descendente
   - Aprenda sobre conjuntos FIRST/FOLLOW
   - Estude eliminação de recursão à esquerda

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique a [Documentação Completa](GRAMMAR_PLAYGROUND_README.md)
2. Execute o [Test Script](test_grammar_playground.py)
3. Verifique o [Código Fonte](deteta_vuln/)

---

**Bom aproveito! 🎉**
