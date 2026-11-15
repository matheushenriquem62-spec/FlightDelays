## Parte do Mariano: dados, análise e gráficos

Eu fiquei com a parte dos dados. Os arquivos são `preparar_dados.py`, `dados.py` e a rota `/upload` do `app.py`.

**preparar_dados.py**
Baixei um mês de voos do site do BTS (dados reais dos EUA). Esse script pega o arquivo bruto, tira os voos cancelados e os sem informação de atraso, cria a coluna `atrasou` (1 se o voo chegou com 15 minutos ou mais de atraso) e sorteia 30 mil voos. O resultado é o `data/voos.csv`.
Como usar: `python preparar_dados.py data/bts_bruto.csv`

**dados.py**
- `ler_csv`: lê o arquivo enviado e confere se ele serve. Se estiver vazio, com separador errado ou faltando coluna, mostra uma mensagem clara em vez de quebrar.
- `limpar`: remove linhas com valor ausente ou impossível e guarda um relatório com o tamanho antes e depois. Linhas repetidas só são contadas, não removidas, porque sem o número do voo não dá para saber se são repetidas de verdade.
- `analisar`: calcula 3 achados (atraso por companhia, por dia da semana e por faixa de horário).
- `gerar_graficos`: faz 3 gráficos: distribuição da distância, atraso por companhia e atraso por hora do dia.

**app.py (rota /upload)**
Recebe o CSV pelo formulário, chama as funções acima e manda o resultado para a página de análise. Se o arquivo for inválido, mostra a mensagem de erro na página.

**Limitação:** os dados são só de janeiro, então os padrões podem refletir o inverno nos EUA.

**Uso de IA:** usei o Claude (Anthropic) para tirar dúvidas, entender conceitos, revisar e comentar o código da minha parte.



## Parte do Pedro: páginas de upload e de resultados

Eu fiquei com a página de upload e a página de resultados. Os arquivos são `templates/index.html` e `templates/analise.html`, e 2 linhas na rota `/upload` do `app.py`.

**index.html**
Página inicial. Tem o formulário que envia o CSV para a rota `/upload` (método POST, com `enctype="multipart/form-data"`, que é obrigatório para enviar arquivo). O campo se chama `arquivo`, o mesmo nome que o `app.py` usa em `request.files.get("arquivo")`. A página também mostra o formato esperado do CSV (as 6 colunas).

**analise.html**
Página de resultados, montada com Jinja a partir das variáveis que a rota `/upload` envia:
- `erro`: se o arquivo for inválido, mostra a mensagem e um link para voltar.
- `colunas` e `amostra`: nomes das colunas e as 10 primeiras linhas do arquivo enviado.
- `relatorio`: tamanho da base antes e depois da limpeza e o que foi feito (função `limpar`).
- `resultado`: total de voos, taxa geral de atraso e os 3 achados (função `analisar`).
- `graficos`: os 3 gráficos (função `gerar_graficos`), cada um com um texto de interpretação.

**app.py (rota /upload)**
Adicionei `amostra` e `colunas` no `render_template`, para mostrar a amostra e as colunas do arquivo enviado.

**Uso de IA:** usei o Claude (Anthropic) para tirar dúvidas, entender conceitos e revisar o código da minha parte.


## Parte do Matheus: formulário de previsão e CSS do site

Eu fiquei com o formulário de previsão, a exibição do resultado e o visual do site. Os arquivos são `templates/previsao.html`, `static/style.css` e a rota `/previsao` do `app.py`. Também coloquei o `<link>` do CSS no `index.html` e no `analise.html`, e um menu para navegar entre as páginas.

**previsao.html**
Tem um campo para cada variável do X: companhia, mês, dia da semana, horário previsto e distância. As companhias da lista vêm do próprio modelo salvo, então sempre batem com o que ele aprendeu. O horário é digitado como 14:35 e o `app.py` transforma em 1435 (o formato do CSV). Se der erro, a mensagem aparece em cima e o que a pessoa digitou não é apagado. O resultado aparece numa caixa vermelha (provável atraso) ou verde (provavelmente no horário), com a chance em % e o nome do modelo usado.

**app.py (rota /previsao)**
- `pegar_companhias`: abre o modelo salvo e pega as siglas das companhias que ele conhece.
- `previsao`: no GET mostra o formulário. No POST converte os campos, confere se os valores fazem sentido (mês de 1 a 12, dia de 1 a 7, distância de 1 a 5000 milhas, companhia da lista) e chama a função `prever` do `modelo.py`. Se algo estiver errado, mostra uma mensagem em vez de quebrar. Se o modelo ainda não foi treinado, avisa para rodar `python treinar.py`.

**style.css**
Um CSS só para as 3 páginas. Eu estilizei as tags direto (body, table, form, img...), então as páginas do Pedro ficaram com o visual novo só com a linha do `<link>`. As cores ficam todas no começo do arquivo. Funciona no celular também.

**Limitação:** o modelo foi treinado só com voos de janeiro, então escolher outro mês no formulário não muda o resultado de verdade. Deixei um aviso na página sobre isso.



## Parte do Matheus Henrique: modelos, avaliação e função de previsão

Eu fiquei com a parte do machine learning. Os arquivos são `modelo.py`, `treinar.py` e o modelo salvo em `models/modelo.joblib`.

**modelo.py**
- `preparar_xy`: separa a tabela em X (mês, dia da semana, companhia, horário previsto e distância) e y (`atrasou`). Só entram no X informações que existem antes do voo, para não haver vazamento de dados. A companhia é texto, então uso o one-hot encoding (`pd.get_dummies`), que cria uma coluna de 0 e 1 para cada companhia. O X fica com 17 colunas.
- `separar_treino_teste`: usa o `train_test_split` do scikit-learn para guardar 80% dos voos para treino (24 mil) e 20% para teste (6 mil). Uso `random_state=42` para a divisão ser sempre a mesma e `stratify=y` para manter a proporção de voos atrasados (cerca de 20%) nos dois grupos. Os dois modelos usam a mesma divisão, então a comparação é justa.
- `treinar_modelos`: cria e treina com o `fit` dois modelos, a Decision Tree (árvore de decisão, `max_depth=5`) e a Random Forest (100 árvores que votam, `max_depth=10`). Os dois estudam só os dados de treino.
- `avaliar_modelos`: cada modelo dá o palpite (`predict`) nos voos de teste, que ele nunca viu, e comparo com o `y_test`. Guardo a acurácia, a matriz de confusão, o relatório (precisão, recall e f1) e o `f1_atraso`, a nota só dos voos atrasados.
- `salvar_melhor_modelo`: escolhe o modelo com maior `f1_atraso` e salva com o `joblib` em `models/modelo.joblib`, junto com a lista de colunas. Assim o site só carrega o modelo pronto, sem treinar de novo.
- `prever`: recebe os dados de um voo, monta a tabela com as mesmas 17 colunas do treino e devolve se o voo provavelmente atrasa, a chance em % e o nome do modelo. É a função que o formulário do site chama.

**treinar.py**
Script que junta tudo na ordem: lê `data/voos.csv`, separa X e y, divide em treino e teste, treina, avalia, mostra os resultados e salva o melhor modelo.
Como usar: `python treinar.py`

**Resultados (6 mil voos de teste)**

| Modelo | Acurácia | Atrasos encontrados (recall) | Precisão do "atrasa" | f1 do "atrasa" |
|---|---|---|---|---|
| Decision Tree | 0,62 | 0,49 | 0,26 | 0,34 |
| Random Forest | 0,618 | 0,54 | 0,28 | 0,37 |

A Random Forest foi salva por ter o maior f1 de atraso.

**O que aprendi sobre a acurácia:** na primeira versão a acurácia deu 0,795, mas isso enganava. Só cerca de 20% dos voos atrasam, então um modelo que sempre responde "não atrasa" também acerta uns 80%. A matriz de confusão mostrou que os modelos não achavam nenhum voo atrasado (recall 0,00). Por isso usei `class_weight="balanced"`, que dá mais peso aos voos atrasados. A acurácia caiu para 0,62, mas os modelos passaram a identificar mais da metade dos atrasos, com mais alarmes falsos. Escolhi essa troca porque o objetivo do sistema é avisar sobre atrasos.

**Limitação:** mês, dia, companhia, horário e distância explicam pouco do atraso, então os modelos erram bastante (quando dizem "atrasa", acertam menos de 3 em cada 10 vezes). O modelo foi treinado só com voos de janeiro e deve ser lido como uma estimativa, não como uma garantia.

**Uso de IA:** usei o Claude (Anthropic) para tirar dúvidas, entender os conceitos (treino e teste, one-hot, métricas), revisar e comentar o código da minha parte. Eu rodei e testei o código e consigo explicar cada parte.
