"""dados.py - leitura, validação, limpeza, análise e gráficos do CSV de voos.

Formato esperado do CSV (uma linha por voo):
    mes               número de 1 a 12
    dia_semana        número de 1 (segunda) a 7 (domingo)
    companhia         código da companhia aérea (ex.: AA, DL, UA)
    horario_previsto  horário previsto de saída no formato HHMM (ex.: 1435 = 14:35)
    distancia         distância do voo em milhas (maior que 0)
    atrasou           1 se chegou com 15 min ou mais de atraso, 0 caso contrário
"""

import os

import pandas as pd
import matplotlib

# "Agg" gera as imagens direto em arquivo, sem abrir janela.
# É obrigatório dentro do Flask (o servidor não tem tela).
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLUNAS_OBRIGATORIAS = [
    "mes",
    "dia_semana",
    "companhia",
    "horario_previsto",
    "distancia",
    "atrasou",
]
COLUNAS_NUMERICAS = ["mes", "dia_semana", "horario_previsto", "distancia", "atrasou"]

# companhias com menos voos que isso ficam de fora da comparação (taxa instável)
MIN_VOOS_COMPANHIA = 30

NOMES_DIAS = {
    1: "segunda",
    2: "terça",
    3: "quarta",
    4: "quinta",
    5: "sexta",
    6: "sábado",
    7: "domingo",
}


def ler_csv(arquivo):
    """Lê o CSV enviado e confere se ele serve. Devolve um DataFrame.
    Se algo estiver errado, levanta ValueError com uma mensagem clara."""
    try:
        df = pd.read_csv(arquivo)
    except pd.errors.EmptyDataError:
        raise ValueError("O arquivo está vazio.")
    except Exception:
        raise ValueError("Não foi possível ler o arquivo. Envie um CSV válido.")

    if df.empty:
        raise ValueError("O arquivo tem o cabeçalho, mas nenhuma linha de dados.")

    # separador errado: o arquivo inteiro vira uma coluna só (ex.: "mes;dia;...")
    if len(df.columns) == 1 and (";" in df.columns[0] or "\t" in df.columns[0]):
        raise ValueError("Separador incorreto. O CSV deve usar vírgula (,) para separar as colunas.")

    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(
            "Colunas obrigatórias ausentes: " + ", ".join(faltando)
            + ". Colunas esperadas: " + ", ".join(COLUNAS_OBRIGATORIAS) + "."
        )

    return df


def limpar(df):
    """Limpa os dados SEM alterar o DataFrame recebido (trabalha numa cópia).
    Devolve (df_limpo, relatorio). O relatório registra cada transformação."""
    df = df[COLUNAS_OBRIGATORIAS].copy()
    linhas_antes = len(df)
    transformacoes = []

    # 1) conversões: texto nas colunas numéricas vira NaN (valor ausente)
    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    df["companhia"] = df["companhia"].astype(str).str.strip().str.upper()
    transformacoes.append("Colunas numéricas convertidas para número; código da companhia padronizado (maiúsculas, sem espaços).")

    # 2) valores ausentes: sem o valor não dá pra analisar nem treinar, então a linha sai
    ausentes = int(df.isna().any(axis=1).sum())
    df = df.dropna()
    transformacoes.append(f"{ausentes} linha(s) removida(s) por valor ausente ou não numérico.")

    # 3) valores impossíveis (fora do intervalo que faz sentido)
    validos = (
        df["mes"].between(1, 12)
        & df["dia_semana"].between(1, 7)
        & df["horario_previsto"].between(0, 2359)
        & (df["horario_previsto"] % 100 < 60)
        & (df["distancia"] > 0)
        & df["atrasou"].isin([0, 1])
    )
    impossiveis = int((~validos).sum())
    df = df[validos]
    transformacoes.append(f"{impossiveis} linha(s) removida(s) por valor impossível (mês, dia, horário, distância ou alvo fora do intervalo).")

    # 4) duplicatas: só contamos, NÃO removemos. Sem um identificador do voo (número, data),
    # voos diferentes podem ter exatamente as mesmas 6 colunas, e apagar seria perder dado real.
    duplicadas = int(df.duplicated().sum())
    transformacoes.append(f"{duplicadas} linha(s) repetida(s) mantida(s): sem identificador do voo, não dá pra afirmar que são duplicatas reais.")

    # 5) tipos finais (inteiros onde faz sentido)
    for coluna in ["mes", "dia_semana", "horario_previsto", "atrasou"]:
        df[coluna] = df[coluna].astype(int)

    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError("Depois da limpeza não sobrou nenhum registro válido.")

    relatorio = {
        "linhas_antes": linhas_antes,
        "linhas_depois": len(df),
        "removidas_ausentes": ausentes,
        "removidas_impossiveis": impossiveis,
        "duplicadas_mantidas": duplicadas,
        "transformacoes": transformacoes,
    }
    return df, relatorio


def _faixa_horario(df):
    """Transforma o horário HHMM em faixa do dia (série de texto)."""
    hora = df["horario_previsto"] // 100
    return pd.cut(
        hora,
        bins=[-1, 5, 11, 17, 23],
        labels=["madrugada (0h-5h)", "manhã (6h-11h)", "tarde (12h-17h)", "noite (18h-23h)"],
    )


def analisar(df):
    """Calcula os 3 achados do trabalho. Devolve um dicionário."""
    taxa_geral = round(df["atrasou"].mean() * 100, 1)

    # achado 1: atraso por companhia (só companhias com voos suficientes)
    por_cia = df.groupby("companhia")["atrasou"].agg(["mean", "count"])
    por_cia_ok = por_cia[por_cia["count"] >= MIN_VOOS_COMPANHIA]
    if por_cia_ok.empty:
        por_cia_ok = por_cia
    por_cia_ok = por_cia_ok.sort_values("mean", ascending=False)
    pior_cia, melhor_cia = por_cia_ok.index[0], por_cia_ok.index[-1]

    # achado 2: atraso por dia da semana
    por_dia = df.groupby("dia_semana")["atrasou"].mean()
    pior_dia, melhor_dia = por_dia.idxmax(), por_dia.idxmin()

    # achado 3: atraso por faixa do dia
    por_faixa = df.groupby(_faixa_horario(df), observed=True)["atrasou"].mean()
    pior_faixa, melhor_faixa = por_faixa.idxmax(), por_faixa.idxmin()

    achados = [
        f"Companhias: {pior_cia} tem a maior taxa de atraso ({por_cia_ok.loc[pior_cia, 'mean'] * 100:.1f}%) "
        f"e {melhor_cia} a menor ({por_cia_ok.loc[melhor_cia, 'mean'] * 100:.1f}%). A média geral é {taxa_geral}%.",
        f"Dia da semana: {NOMES_DIAS[pior_dia]} é o dia com mais atrasos ({por_dia[pior_dia] * 100:.1f}%) "
        f"e {NOMES_DIAS[melhor_dia]} o com menos ({por_dia[melhor_dia] * 100:.1f}%).",
        f"Horário: a faixa '{pior_faixa}' tem a maior taxa de atraso ({por_faixa[pior_faixa] * 100:.1f}%) "
        f"e '{melhor_faixa}' a menor ({por_faixa[melhor_faixa] * 100:.1f}%).",
    ]

    return {
        "total_voos": len(df),
        "taxa_geral": taxa_geral,
        "distancia_media": round(df["distancia"].mean(), 1),
        "distancia_max": int(df["distancia"].max()),
        "achados": achados,
    }


def gerar_graficos(df, pasta):
    """Gera os 3 gráficos como PNG dentro de 'pasta'. Devolve a lista de nomes dos arquivos."""
    os.makedirs(pasta, exist_ok=True)
    taxa_geral = df["atrasou"].mean() * 100
    arquivos = []

    # 1) DISTRIBUIÇÃO: histograma da distância
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["distancia"], bins=30, color="#2a7f8f", edgecolor="white")
    ax.set_title("Distribuição da distância dos voos")
    ax.set_xlabel("Distância (milhas)")
    ax.set_ylabel("Quantidade de voos")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_distancia.png"), dpi=110)
    plt.close(fig)
    arquivos.append("grafico_distancia.png")

    # 2) COMPARAÇÃO: taxa de atraso por companhia
    por_cia = df.groupby("companhia")["atrasou"].agg(["mean", "count"])
    por_cia_ok = por_cia[por_cia["count"] >= MIN_VOOS_COMPANHIA]
    if por_cia_ok.empty:
        por_cia_ok = por_cia
    por_cia_ok = (por_cia_ok["mean"] * 100).sort_values()
    fig, ax = plt.subplots(figsize=(8, max(4.5, 0.35 * len(por_cia_ok))))
    ax.barh(por_cia_ok.index, por_cia_ok.values, color="#2a7f8f")
    ax.axvline(taxa_geral, color="#c0392b", linestyle="--", label=f"Média geral ({taxa_geral:.1f}%)")
    ax.set_title("Taxa de atraso na chegada por companhia")
    ax.set_xlabel("Voos atrasados (%)")
    ax.set_ylabel("Companhia")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_companhias.png"), dpi=110)
    plt.close(fig)
    arquivos.append("grafico_companhias.png")

    # 3) RELAÇÃO: taxa de atraso conforme a hora prevista de saída
    por_hora = (df.groupby(df["horario_previsto"] // 100)["atrasou"].mean() * 100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(por_hora.index, por_hora.values, marker="o", color="#2a7f8f")
    ax.axhline(taxa_geral, color="#c0392b", linestyle="--", label=f"Média geral ({taxa_geral:.1f}%)")
    ax.set_title("Taxa de atraso por hora prevista de saída")
    ax.set_xlabel("Hora prevista de saída (0 a 23)")
    ax.set_ylabel("Voos atrasados (%)")
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_horario.png"), dpi=110)
    plt.close(fig)
    arquivos.append("grafico_horario.png")

    return arquivos


if __name__ == "__main__":
    # teste rápido fora do Flask:  python dados.py
    df_lido = ler_csv("data/voos.csv")
    df_limpo, rel = limpar(df_lido)
    print("Linhas antes:", rel["linhas_antes"], "| depois:", rel["linhas_depois"])
    for t in rel["transformacoes"]:
        print(" -", t)
    resultado = analisar(df_limpo)
    for a in resultado["achados"]:
        print(" *", a)
    print("Gráficos:", gerar_graficos(df_limpo, "static"))
