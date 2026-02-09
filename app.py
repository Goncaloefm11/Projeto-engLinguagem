from flask import Flask, render_template, request
from core.parser_logic import AnalisadorGramatica

app = Flask(__name__)

def processar_texto_gramatica(texto):
    # Converte o texto da área de transferência num dicionário de produções
    producoes = {}
    for linha in texto.strip().split('\n'):
        if "->" in linha:
            cabeca, corpo = linha.split("->")
            nt = cabeca.strip()
            alternativas = [alt.strip().split() for alt in corpo.split("|")]
            if nt not in producoes: producoes[nt] = []
            producoes[nt].extend(alternativas)
    return producoes

@app.route('/', methods=['GET', 'POST'])
def web():
    res = None
    if request.method == 'POST':
        texto = request.form['gramatica']
        prods = processar_texto_gramatica(texto)
        analisador = AnalisadorGramatica(prods)
        first, follow, tabela, conflitos = analisador.executar_completo()
        
        res = {
            'first': first,
            'follow': follow,
            'tabela': {f"{k[0]},{k[1]}": " ".join(v[0]) for k, v in tabela.items()},
            'conflitos': conflitos,
            'terminais': sorted(list(analisador.terminais)),
            'nao_terminais': analisador.nao_terminais
        }
    return render_template('index.html', res=res)

if __name__ == '__main__':
    app.run(debug=True)