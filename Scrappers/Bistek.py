import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sys

# Configuração dos produtos e limites
PRODUTOS_PARA_BUSCAR = ['ovo', 'leite']
MAX_PAGINAS = 5

def configurar_driver():
    """Configura o navegador Chrome controlado pelo Selenium."""
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Descomente se não quiser ver o navegador abrindo
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extrair_dados(driver, termo):
    resultados = []
    
    for pagina in range(1, MAX_PAGINAS + 1):
        # Montagem da URL conforme solicitado
        url = f"https://www.bistek.com.br/{termo}?map=ft&p={termo}&page={pagina}"
        print(f"--- Processando: {termo} | Página: {pagina} ---")
        
        driver.get(url)
        
        # Espera o site carregar (Sites VTEX são pesados, 5 segundos é uma margem segura)
        time.sleep(5)
        
        # Rolar a página para baixo para garantir que as imagens e preços carreguem (Lazy Load)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Passa o HTML atual para o BeautifulSoup (mais rápido para analisar que o Selenium puro)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Encontrar o container de cada produto
        # Nota: Baseado na estrutura do Bistek/VTEX
        produtos_html = soup.find_all('section', class_='vtex-product-summary-2-x-container')
        
        if not produtos_html:
            print(f"Nenhum produto encontrado na página {pagina}. Encerrando busca por '{termo}'.")
            break
            
        for prod in produtos_html:
            try:
                # 1. Extração do NOME
                # Classe fornecida: vtex-product-summary-2-x-productBrand
                tag_nome = prod.find('span', class_='vtex-product-summary-2-x-productBrand')
                nome = tag_nome.get_text(strip=True) if tag_nome else "Nome não encontrado"
                
                # 2. Extração do PREÇO
                # O preço no VTEX é dividido em: R$ (Símbolo) + Inteiro + , (Vírgula) + Fração
                # Buscamos as partes separadamente para garantir precisão
                
                # Símbolo (R$)
                tag_simbolo = prod.find('span', class_='vtex-product-price-1-x-currencyCode')
                
                # Inteiro (Não fornecido no prompt, mas necessário para compor o preço)
                tag_inteiro = prod.find('span', class_='vtex-product-price-1-x-currencyInteger')
                
                # Fração (49, 90, etc)
                tag_fracao = prod.find('span', class_='vtex-product-price-1-x-currencyFraction')
                
                if tag_inteiro and tag_fracao:
                    # Monta: R$ 10,90
                    simbolo = tag_simbolo.get_text(strip=True) if tag_simbolo else "R$"
                    preco_formatado = f"{simbolo} {tag_inteiro.get_text(strip=True)},{tag_fracao.get_text(strip=True)}"
                else:
                    preco_formatado = "Indisponível / Sem Preço"

                # Só adiciona se tiver nome válido
                if nome:
                    resultados.append({
                        'Termo Buscado': termo,
                        'Produto': nome,
                        'Preco': preco_formatado,
                        'Pagina': pagina
                    })
                    
            except Exception as e:
                print(f"Erro ao processar um item: {e}")
                continue

    return resultados

def salvar_csv(dados):
    if not dados:
        print("Nenhum dado capturado para salvar.")
        return

    # ALTERADO: Nome padronizado
    nome_arquivo = 'precos_bistek.csv'
    
    # 'utf-8-sig' é importante para o Excel abrir acentos corretamente
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8-sig') as file:
        # ALTERADO: Adicionado delimiter=';' para padronizar com os outros scripts
        writer = csv.DictWriter(file, fieldnames=['Termo Buscado', 'Produto', 'Preco', 'Pagina'], delimiter=';')
        writer.writeheader()
        writer.writerows(dados)   
    print(f"\nSucesso! Arquivo '{nome_arquivo}' criado com {len(dados)} produtos.")

def main():
    driver = configurar_driver()
    todos_dados = []
    
    # --- ALTERADO: Lógica de argumentos ---
    if len(sys.argv) > 1:
        produtos_busca = sys.argv[1:]
    else:
        produtos_busca = PRODUTOS_PARA_BUSCAR # Usa a constante do topo se rodar sozinho

    print(f"📋 Lista de busca: {produtos_busca}")

    try:
        for produto in produtos_busca:
            dados_produto = extrair_dados(driver, produto)
            todos_dados.extend(dados_produto)
            
    finally:
        driver.quit()
        
    salvar_csv(todos_dados)

if __name__ == "__main__":
    main()