import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys

def extrair_angeloni_url_direta():
    # Configuração do Navegador
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") # Retire o comentário se quiser rodar sem ver a janela
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30) 

    # --- Recebe lista do main.py ou usa padrão ---
    if len(sys.argv) > 1:
        termos = sys.argv[1:]
    else:
        termos = ["leite", "ovo"]
    
    print(f"📋 Lista de busca: {termos}")
    
    dados_totais = []

    try:
        for termo in termos:
            print(f"\n--- Processando: {termo} ---")
            
            # URL de busca
            url = f"https://www.angeloni.com.br/super/{termo}?_q={termo}&map=ft"
            print(f"Acessando URL: {url}")
            driver.get(url)

            # Fecha Modais/Pop-ups com ESC
            try:
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass

            # Aguarda produtos
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "vtex-product-summary-2-x-container")))
            except:
                print(f"Não foram encontrados produtos para {termo} ou a página demorou.")
                continue

            # Scroll
            print("Realizando scroll para carregar imagens e preços...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4) 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(4)

            # Coleta
            produtos = driver.find_elements(By.CSS_SELECTOR, ".vtex-product-summary-2-x-container")
            print(f"Encontrados {len(produtos)} itens na página.")

            for produto in produtos:
                try:
                    # -- Captura do NOME --
                    nome_el = produto.find_element(By.CSS_SELECTOR, ".vtex-product-summary-2-x-productBrand")
                    nome = nome_el.text

                    # -- Captura do PREÇO (COM CORREÇÃO PARA PROMOÇÃO) --
                    try:
                        # ESTRATÉGIA: Busca primeiro o container "sellingPrice" (Preço de Venda).
                        # Isso isola o preço real e ignora o bloco "Economize" que tem classes iguais.
                        try:
                            container_preco = produto.find_element(By.CSS_SELECTOR, ".vtex-product-price-1-x-sellingPrice")
                        except:
                            # Fallback: Se não achar o container específico, tenta no produto todo
                            container_preco = produto

                        # Busca os componentes DENTRO do container isolado
                        simbolo = container_preco.find_element(By.CSS_SELECTOR, ".vtex-product-price-1-x-currencyCode").text
                        inteiro = container_preco.find_element(By.CSS_SELECTOR, ".vtex-product-price-1-x-currencyInteger").text
                        fracao = container_preco.find_element(By.CSS_SELECTOR, ".vtex-product-price-1-x-currencyFraction").text
                        
                        preco_formatado = f"{simbolo} {inteiro},{fracao}"
                        valor_excel = f"{inteiro},{fracao}"
                    except:
                        preco_formatado = "Indisponível"
                        valor_excel = "0,00"

                    if nome:
                        dados_totais.append({
                            "Termo": termo,
                            "Produto": nome,
                            "Preço": preco_formatado
                        })

                except Exception as e:
                    continue

    finally:
        driver.quit()

        # Salvar CSV
        if dados_totais:
            df = pd.DataFrame(dados_totais)
            nome_arquivo = "precos_angeloni.csv"
            
            df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8-sig')
            
            print(f"\nSucesso! Arquivo '{nome_arquivo}' criado com {len(dados_totais)} linhas.")
            print(df.head())
        else:
            print("\nNenhum dado coletado.")

if __name__ == "__main__":
    extrair_angeloni_url_direta()