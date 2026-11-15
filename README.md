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