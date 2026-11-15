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

**Uso de IA:** usei o Claude (Anthropic) para tirar dúvidas, entender conceitos, revisar e comentar o código da minha parte.
