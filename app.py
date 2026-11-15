"""app.py - servidor Flask.
Parte do Mariano: a rota /upload (recebe o CSV e chama as funções do dados.py).
"""

# os: montar o caminho da pasta static
import os

# Flask: cria o site; render_template: monta a página HTML; request: o que o usuário enviou
from flask import Flask, render_template, request

# nosso arquivo dados.py (por isso se escreve dados.ler_csv(...))
import dados

# joblib: abre o modelo salvo (usado para pegar a lista de companhias)
import joblib

# prever: função do modelo.py que faz a previsão; CAMINHO_MODELO: onde o modelo está salvo
from modelo import prever, CAMINHO_MODELO

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
      # amostra e colunas do arquivo enviado (slide 5); to_html transforma a tabela em HTML
      amostra=df.head(10).to_html(index=False),
      colunas=list(df.columns),
    )


# ============================================================
# Parte do Matheus: formulário de previsão (rota /previsao)
# ============================================================

# pega as companhias que o modelo conhece, para montar a lista do formulário
def pegar_companhias():
    dados_modelo = joblib.load(CAMINHO_MODELO)
    # no treino, cada companhia virou uma coluna chamada "companhia_AA", "companhia_DL"...
    # aqui a gente tira o "companhia_" e fica só com a sigla
    siglas = []
    for coluna in dados_modelo["colunas"]:
        if coluna.startswith("companhia_"):
            siglas.append(coluna.replace("companhia_", ""))
    return sorted(siglas)


# GET: mostra o formulário vazio | POST: valida os campos, chama o modelo e mostra o resultado
@app.route("/previsao", methods=["GET", "POST"])
def previsao():
    erro = None
    resultado = None
    valores = {}  # o que a pessoa digitou, para devolver pro formulário se der erro

    # se o modelo ainda não foi treinado, avisa em vez de quebrar o site
    try:
        companhias = pegar_companhias()
    except Exception:
        return render_template(
            "previsao.html",
            companhias=[],
            valores={},
            resultado=None,
            erro="Modelo não encontrado. Rode 'python treinar.py' primeiro.",
        )

    if request.method == "POST":
        valores = request.form.to_dict()

        # tenta converter os campos; se vier vazio ou com texto estranho, cai no except
        try:
            companhia = request.form["companhia"]
            mes = int(request.form["mes"])
            dia_semana = int(request.form["dia_semana"])
            distancia = float(request.form["distancia"])

            # o navegador manda o horário como "14:35"; o modelo usa 1435 (HHMM)
            hora, minuto = request.form["horario"].split(":")
            horario_previsto = int(hora) * 100 + int(minuto)
        except (KeyError, ValueError):
            erro = "Preencha todos os campos com valores válidos."
        else:
            # os campos existem, agora confere se os valores fazem sentido
            if companhia not in companhias:
                erro = "Escolha uma companhia da lista."
            elif not 1 <= mes <= 12:
                erro = "O mês precisa estar entre 1 e 12."
            elif not 1 <= dia_semana <= 7:
                erro = "O dia da semana precisa estar entre 1 (segunda) e 7 (domingo)."
            elif not 1 <= distancia <= 5000:
                erro = "A distância precisa estar entre 1 e 5000 milhas."
            else:
                # tudo certo: chama o modelo (ele devolve um dicionário com atrasa, chance e modelo)
                try:
                    resultado = prever(mes, dia_semana, companhia, horario_previsto, distancia)
                except ValueError as problema:
                    erro = str(problema)

    return render_template(
        "previsao.html",
        companhias=companhias,
        valores=valores,
        resultado=resultado,
        erro=erro,
    )


# roda o servidor com "python app.py" (debug=True recarrega ao salvar)
if __name__ == "__main__":
    app.run(debug=True)
