"""preparar_dados.py - transforma o CSV bruto do BTS no formato usado pelo projeto.

Como usar (dentro da pasta do projeto):
    python preparar_dados.py data/bts_bruto.csv

Lê o arquivo baixado do BTS (Reporting Carrier On-Time Performance), remove voos
cancelados e sem informação de atraso, renomeia as colunas, sorteia uma amostra
e salva em data/voos.csv, que é o arquivo que a aplicação espera.

O alvo ("atrasou") é 1 quando o voo chegou com 15 minutos ou mais de atraso.
Se o arquivo tiver a coluna ARR_DEL15, ela é usada. Se não tiver, o alvo é calculado
a partir do atraso de chegada em minutos (ARR_DELAY ou ARR_DELAY_NEW): >= 15 vira 1.
"""

# sys: pega o que foi digitado no terminal (o caminho do CSV)
import sys

# pandas: lê e transforma o CSV
import pandas as pd

# arquivo de entrada: o 1º argumento do terminal (ou o padrão)
ENTRADA = sys.argv[1] if len(sys.argv) > 1 else "data/bts_bruto.csv"
# arquivo pronto que o projeto usa
SAIDA = "data/voos.csv"
TAMANHO_AMOSTRA = 30000
SEMENTE = 42  # random_state: garante que todo mundo gera a mesma amostra
LIMITE_ATRASO_MIN = 15  # definição do trabalho: atraso de 15 min ou mais

# nome no projeto -> nomes possíveis no arquivo do BTS.
# A comparação ignora maiúsculas/minúsculas e underscores (DAY_OF_WEEK = DayOfWeek),
# porque o BTS já usou os dois estilos de nome.
CANDIDATOS = {
    "mes": ["Month"],
    "dia_semana": ["DayOfWeek"],
    "companhia": ["Reporting_Airline", "IATA_CODE_Reporting_Airline", "OP_UNIQUE_CARRIER", "UniqueCarrier", "OP_CARRIER"],
    "horario_previsto": ["CRSDepTime"],
    "distancia": ["Distance"],
}
COLUNA_CANCELADO = ["Cancelled"]
COLUNA_ATRASOU = ["ArrDel15"]  # já vem 0/1
COLUNA_ATRASO_MIN = ["ArrDelay", "ArrDelayNew", "ArrDelayMinutes"]  # atraso em minutos


# compara nomes de coluna ignorando maiúsculas e "_" (DAY_OF_WEEK = DayOfWeek)
def normalizar(nome):
    return nome.replace("_", "").lower()


def achar(colunas_arquivo, candidatos):
    """Devolve o nome real da coluna no arquivo, ou None se nenhum candidato existir."""
    reais = {normalizar(c): c for c in colunas_arquivo}
    for c in candidatos:
        if normalizar(c) in reais:
            return reais[normalizar(c)]
    return None


def exigir(colunas_arquivo, candidatos, nome):
    """Igual a achar(), mas para o programa com mensagem clara se não encontrar."""
    coluna = achar(colunas_arquivo, candidatos)
    if coluna is None:
        raise SystemExit(
            f"Não encontrei a coluna '{nome}' no arquivo. Procurei por: {candidatos}.\n"
            f"Colunas do arquivo: {list(colunas_arquivo)}\n"
            "Baixe de novo no BTS marcando essa coluna (ou ajuste CANDIDATOS no topo deste script)."
        )
    return coluna


# passo a passo: ler -> filtrar -> criar o alvo -> amostrar -> salvar
def main():
    bruto = pd.read_csv(ENTRADA, low_memory=False)
    print(f"Arquivo bruto: {len(bruto)} voos, {len(bruto.columns)} colunas")

    # descobre o nome real de cada coluna no arquivo baixado
    mapa = {nome: exigir(bruto.columns, cands, nome) for nome, cands in CANDIDATOS.items()}
    col_cancelado = exigir(bruto.columns, COLUNA_CANCELADO, "Cancelled")

    # alvo: ARR_DEL15 (0/1) se existir; senão, calcula a partir do atraso em minutos
    col_atrasou = achar(bruto.columns, COLUNA_ATRASOU)
    col_minutos = None if col_atrasou else achar(bruto.columns, COLUNA_ATRASO_MIN)
    if col_atrasou is None and col_minutos is None:
        raise SystemExit(
            "Não encontrei a coluna do atraso de chegada. Procurei por: "
            f"{COLUNA_ATRASOU + COLUNA_ATRASO_MIN}.\n"
            f"Colunas do arquivo: {list(bruto.columns)}\n"
            "Baixe de novo no BTS marcando ARR_DEL15 (ou ARR_DELAY / ARR_DELAY_NEW)."
        )
    col_alvo = col_atrasou or col_minutos
    if col_minutos:
        print(f"Coluna ARR_DEL15 ausente: o alvo será calculado de '{col_minutos}' (>= {LIMITE_ATRASO_MIN} min = atrasou)")

    # 1) o PDF pede para excluir voos cancelados
    df = bruto[bruto[col_cancelado] == 0]
    print(f"Sem cancelados: {len(df)} voos")

    # 2) sem informação de atraso não sabemos se atrasou (acontece em voos desviados)
    df = df.dropna(subset=[col_alvo])
    print(f"Com informação de atraso: {len(df)} voos")

    # (o alvo "atrasou" é criado logo abaixo: 1 = chegou com 15 min ou mais de atraso)
    # 3) só as colunas do projeto, com os nomes do projeto
    saida = df[[mapa[n] for n in CANDIDATOS]].copy()
    saida.columns = list(CANDIDATOS)
    if col_minutos:
        saida["atrasou"] = (df[col_minutos] >= LIMITE_ATRASO_MIN).astype(int)
    else:
        saida["atrasou"] = df[col_atrasou].astype(int)
    saida["horario_previsto"] = saida["horario_previsto"].astype(int)
    saida["mes"] = saida["mes"].astype(int)
    saida["dia_semana"] = saida["dia_semana"].astype(int)
    saida["distancia"] = saida["distancia"].round().astype(int)

    # 4) amostra (o arquivo de um mês tem centenas de milhares de linhas)
    if len(saida) > TAMANHO_AMOSTRA:
        saida = saida.sample(TAMANHO_AMOSTRA, random_state=SEMENTE)
    saida = saida.reset_index(drop=True)

    # index=False: não grava a coluna de números de linha do pandas
    saida.to_csv(SAIDA, index=False)
    print(f"Salvo em {SAIDA}: {len(saida)} voos | {saida['atrasou'].mean() * 100:.1f}% atrasaram {LIMITE_ATRASO_MIN} min ou mais")


# só roda com "python preparar_dados.py ..." (não quando é importado)
if __name__ == "__main__":
    main()
