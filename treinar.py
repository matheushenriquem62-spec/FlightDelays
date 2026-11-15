import pandas as pd
from modelo import (preparar_xy, separar_treino_teste, treinar_modelos,
                    avaliar_modelos, salvar_melhor_modelo)

# 1) ler os voos
df = pd.read_csv("data/voos.csv")

# 2) separar X e y, e depois treino e teste
X, y = preparar_xy(df)
X_train, X_test, y_train, y_test = separar_treino_teste(X, y)

# 3) treinar os 2 modelos e avaliar no teste
modelos = treinar_modelos(X_train, y_train)
resultados = avaliar_modelos(modelos, X_test, y_test)

for nome, r in resultados.items():
    print(nome, "| acurácia:", round(r["acuracia"], 3), "| f1 atraso:", round(r["f1_atraso"], 3))

# 4) salvar o melhor
melhor = salvar_melhor_modelo(modelos, resultados, list(X.columns))
print("Melhor modelo:", melhor)