# pandas: lê o CSV e manipula a tabela
import pandas as pd
from scipy.constants import value
# train_test_split: foi usado train_test_split, do scikit-learn, para separar os voos em 80% de treino e 20% de teste.
from sklearn.model_selection import train_test_split
# DecisionTreeClassifier: modelo de árvore de decisão
from sklearn.tree import DecisionTreeClassifier
# RandomForestClassifier: modelo de floresta aleatória (várias árvores votando)
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, f1_score
import os
import joblib

# AAA coluna x vai representar as seguintes informacoes abaixo
COLUNAS_X = ["mes", "dia_semana", "companhia", "horario_previsto", "distancia"]

# AAA coluna Y diz companhia especifica ATRASOU (0 - sem atraso e 1 - Aviao atrasado)
COLUNAS_Y = "atrasou"

# AAA funcao preparar_xy recebe a TABELA DE VOOS X e Y
def preparar_xy(df):

    y = df[COLUNAS_Y]
    X = df[COLUNAS_X]

    X = pd.get_dummies(X, columns=["companhia"]) #<--- esse One hot coloca a sigla da companhia como titulos da tabela em vez de fica um embaixo do outro

    return X, y

def separar_treino_teste(X, y): #ele estuda 80% (treino) dos voos e os 20%(palpite) ele da o palpite
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
            test_size=0.2, # 20% dos voos ficam para o teste
            random_state=42, # fixa o sorteio: toda vez dá a mesma divisão
            stratify=y, # mantém ~20% de atrasados no treino e no teste
    )
    return X_train, X_test, y_train, y_test

def treinar_modelos(X_train, y_train): # A pergunta da árvore“o voo estava marcado até os voos <= 10:56 ou depois?”

    modelos = {
        "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1, class_weight="balanced"), #floresta aleatoria
    }
    for nome, modelo in modelos.items(): #ele vai percorrer nome, modelo em modelos items
        modelo.fit(X_train, y_train)
    return modelos


def avaliar_modelos(modelos, X_test, y_test):

    resultados = {}

    for nome, modelo in modelos.items():
        palpites = modelo.predict(X_test)

        resultados[nome] = {
            "acuracia" : accuracy_score(y_test, palpites), #A porcentagem de acertos, um número só.
            "matriz" : confusion_matrix(y_test, palpites), #tabela 2×2 que mostra onde o modelo acertou e errou
            "relatorio" : classification_report(y_test, palpites, zero_division=0), # Um texto pronto com 3 notas para cada classe (não atrasa e atrasa):
            "f1_atraso": f1_score(y_test, palpites),  # nota do "atrasa", usada para escolher o melhor


        }
    return resultados


# caminho onde o melhor modelo será salvo
CAMINHO_MODELO = "models/modelo.joblib"

def salvar_melhor_modelo(modelos, resultados, colunas):

    melhor = None
    melhor_f1 = -1

    for nome, r in resultados.items():
        if r["f1_atraso"] > melhor_f1:
            melhor = nome
            melhor_f1 = r["f1_atraso"]


    os.makedirs("models", exist_ok=True) # cria a pasta models se ela não existir

    joblib.dump({"nome": melhor, "modelo": modelos[melhor], "colunas": colunas}, CAMINHO_MODELO)

    return melhor

# função que o formulário do site vai chamar. Ela recebe os 5 dados digitados e devolve se o voo provavelmente atrasa.
def prever(mes, dia_semana, companhia,  horario_previsto, distancia):
    dados = joblib.load(CAMINHO_MODELO)
    modelo = dados["modelo"]
    colunas = dados["colunas"]

    if f"companhia_{companhia}" not in colunas:
        raise ValueError("Companhia desconhecida: " + str (companhia))

    # monta uma tabela de 1 linha com o voo digitado
    voo = pd.DataFrame([{
        "mes": mes,
        "dia_semana": dia_semana,
        "companhia": companhia,
        "horario_previsto": horario_previsto,
        "distancia": distancia,
    }])

   #coloca a companhia como titulos na tabela dnv
    voo = pd.get_dummies(voo, columns=["companhia"])

    # deixa as colunas na mesma ordem do treino; as que faltam viram 0
    voo = voo.reindex(columns=colunas, fill_value=0)

    palpite = int(modelo.predict(voo)[0])
    chance = float(modelo.predict_proba(voo)[0][1])

    return {"atrasa": palpite == 1, "chance": round(chance * 100, 1), "modelo": dados["nome"]}







