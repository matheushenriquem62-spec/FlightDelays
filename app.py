"""app.py - servidor Flask.
Parte do Mariano: a rota /upload (recebe o CSV e chama as funções do dados.py).
"""

# os: montar o caminho da pasta static
import os

# Flask: cria o site; render_template: monta a página HTML; request: o que o usuário enviou
from flask import Flask, render_template, request

# nosso arquivo dados.py (por isso se escreve dados.ler_csv(...))
import dados

app = Flask(__name__)

# pasta onde os PNGs dos gráficos são salvos (o Flask serve a pasta static)
PASTA_GRAFICOS = os.path.join(app.root_path, "static")


# página inicial (formulário de upload, feito pelo Pedro)
@app.route("/")
def index():
    return render_template("index.html")


# recebe o CSV enviado pelo formulário (POST) e mostra a análise
@app.route("/upload", methods=["POST"])
def upload():
    # "arquivo" é o name do campo no formulário; .get devolve None se não veio nada
    arquivo = request.files.get("arquivo")

    # ninguém escolheu arquivo
    if arquivo is None or arquivo.filename == "":
        return render_template("analise.html", erro="Nenhum arquivo foi enviado.")

    # só aceita .csv
    if not arquivo.filename.lower().endswith(".csv"):
        return render_template("analise.html", erro="O arquivo precisa ter a extensão .csv.")

    # ler e limpar: se o arquivo for inválido, o dados.py levanta ValueError
    # e a gente mostra a mensagem na página, sem o site quebrar
    try:
        df = dados.ler_csv(arquivo)
        df_limpo, relatorio = dados.limpar(df)
    except ValueError as erro:
        return render_template("analise.html", erro=str(erro))

    # arquivo válido: calcula os achados e gera os gráficos
    resultado = dados.analisar(df_limpo)
    graficos = dados.gerar_graficos(df_limpo, PASTA_GRAFICOS)

    # entrega tudo para a página analise.html (feita pelo Pedro)
    return render_template(
        "analise.html",
        erro=None,
        relatorio=relatorio,
        resultado=resultado,
        graficos=graficos,
    )


# roda o servidor com "python app.py" (debug=True recarrega ao salvar)
if __name__ == "__main__":
    app.run(debug=True)