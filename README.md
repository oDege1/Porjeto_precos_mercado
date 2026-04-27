# 🛒 Comparador de Preços de Supermercados (Web Scraping)

Este é um aplicativo de extração de dados (Web Scraping) e processamento em lote criado para monitorar, comparar e normalizar os preços de produtos essenciais em diversas redes de supermercados de Florianópolis, SC (como Angeloni, Bistek, Fort Atacadista, Giassi, etc.).

Além de buscar dados diretamente dos sites dos mercados, o sistema possui uma integração inteligente que lê encartes promocionais e cruza essas informações com a base de dados principal, calculando os preços proporcionais (por Kg, Litro ou Unidade) para garantir uma comparação justa.

## 🚀 Funcionalidades

* **Scraping Concorrente:** Utiliza `ThreadPoolExecutor` para rodar múltiplos scripts de scraping simultaneamente, economizando tempo.
* **Integração de Encartes:** Processa arquivos JSON com produtos de promoções relâmpago/encartes (`encartes_gemini.json`) e faz o *match* de similaridade (Fuzzy Matching) com os produtos já extraídos via site.
* **Cálculo de Preço Proporcional:** Usa Expressões Regulares (Regex) para identificar pesos e volumes nos nomes dos produtos e converte tudo para uma medida base (ex: Preço por Litro, Preço por Kg), permitindo saber qual produto é realmente mais barato.
* **Filtro Blindado de Dados:** Limpa automaticamente valores zerados, nulos ou dados inválidos gerados durante a raspagem.
* **Geração de Relatório Consolidado:** Exporta o resultado final limpo e organizado em um arquivo CSV (`COMPARATIVO_FINAL.csv`).

## 📂 Estrutura do Projeto

* `main.py`: O orquestrador principal do projeto. Dispara os scrapers da pasta `Scrappers/`, consolida os DataFrames, aplica o filtro de preços válidos, calcula proporções e chama a atualização de encartes.
* `atualizador_encartes.py`: Módulo responsável por ler `encartes_gemini.json`, comparar com o banco de dados existente e inserir/atualizar preços baseados nas ofertas físicas usando a biblioteca `difflib`.
* `mercados.json`: Arquivo de configuração e mapeamento geográfico contendo as redes de supermercados, suas filiais e endereços na região de Florianópolis/SC.
* `encartes_gemini.json`: Arquivo de input contendo os dados extraídos de encartes promocionais.
* `Scrappers/` *(Pasta implícita)*: Diretório onde ficam os scripts individuais de extração para cada mercado (ex: `Angeloni.py`, `Bistek.py`, `Fort.py`).
* `COMPARATIVO_FINAL.csv`: Arquivo de saída gerado pelo script, pronto para ser importado no Excel, Power BI ou banco de dados.

## 🛠️ Tecnologias Utilizadas

* **Python 3.x**
* **Pandas:** Para manipulação, limpeza e consolidação dos dados tubulares.
* **Concurrent.Futures:** Para execução assíncrona (multithreading) dos scripts de scraping.
* **Regex (re):** Para extração de gramaturas e volumes dos títulos dos produtos.
* **Difflib (SequenceMatcher):** Para calcular o índice de similaridade entre nomes de produtos.

## ⚙️ Pré-requisitos e Instalação

1. Certifique-se de ter o Python instalado em sua máquina.
2. Instale a biblioteca `pandas` (as demais são nativas do Python):
   ```bash
   pip install pandas
Certifique-se de que os scripts de scraping individuais estão criados dentro de uma pasta chamada Scrappers/ no mesmo diretório do main.py.

▶️ Como Executar
Para iniciar o processo de coleta e geração do relatório, basta rodar o arquivo principal:

Bash
python main.py
O que vai acontecer?

O script vai acionar os arquivos na pasta Scrappers/ de forma paralela.

Vai unir todos os .csv gerados temporariamente.

Se houver promoções no encartes_gemini.json, o atualizador_encartes.py fará a mesclagem.

O console exibirá o progresso e, no final, indicará o total de produtos válidos encontrados.

O arquivo COMPARATIVO_FINAL.csv será gerado/atualizado na raiz do projeto.

📊 Estrutura dos Dados de Saída (COMPARATIVO_FINAL.csv)
O arquivo gerado contém as seguintes colunas (separadas por ponto e vírgula ;):

Termo: A categoria base da busca (ex: leite, arroz, carne).

Produto: O nome completo do produto extraído.

Preço: O texto original do preço (ex: R$ 5,99).

Valor_Num: O preço convertido em formato numérico flutuante (ex: 5.99).

Tipo_Medida: A métrica base encontrada (ex: Preço por Kg, Preço por Litro).

Preço_Proporcional: O valor calculado com base na gramatura do produto.

Mercado: A rede de supermercados de onde o dado veio.

Data: A data em que o dado foi extraído (adicionado de "(Encarte)" quando for promoção de panfleto).
