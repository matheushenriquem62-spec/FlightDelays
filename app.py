import os

from flask import Flask, render_template, request

import dados

app = Flask(__name__)

PASTA_GRAFICOS = os.path.join(app.root_path, "static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    arquivo = request.files.get("arquivo")

    if arquivo is None or arquivo.filename == "":
        return render_template("analise.html", erro="Nenhum arquivo foi enviado.")

    if not arquivo.filename.lower().endswith(".csv"):
        return render_template("analise.html", erro="O arquivo precisa ter a extensão .csv.")

    try:
        df = dados.ler_csv(arquivo)
        df_limpo, relatorio = dados.limpar(df)
    except ValueError as erro:
        return render_template("analise.html", erro=str(erro))

    resultado = dados.analisar(df_limpo)
    graficos = dados.gerar_graficos(df_limpo, PASTA_GRAFICOS)

    return render_template(
        "analise.html",
        erro=None,
        relatorio=relatorio,
        resultado=resultado,
        graficos=graficos,
    )


if __name__ == "__main__":
    app.run(debug=True)