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
