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

def extrair_giassi_url_direta():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    if len(sys.argv) > 1:
        termos = sys.argv[1:]
    else:
        termos = ["leite", "ovo"]
        
    print(f"📋 Lista de busca (Giassi): {termos}")
    dados_totais = []

    try:
        for termo in termos:
            try:
                print(f"\n--- Processando: {termo} ---")
                url = f"https://www.giassi.com.br/{termo}?_q={termo}&map=ft"
                driver.get(url)

                try:
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                except:
                    pass

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "vtex-product-summary-2-x-container")))

                print("Realizando scroll para carregar imagens e preços...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3) 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(2)

                produtos = driver.find_elements(By.CSS_SELECTOR, ".vtex-product-summary-2-x-container")
                print(f"Encontrados {len(produtos)} itens na página para {termo}.")

                for produto in produtos:
                    try:
                        nome_el = produto.find_element(By.CSS_SELECTOR, ".vtex-product-summary-2-x-productBrand")
                        nome = nome_el.text

                        # Tenta extrair o preço. Se der erro, cai no except e pula o produto.
                        preco_el = produto.find_element(By.CSS_SELECTOR, ".giassi-apps-custom-0-x-priceUnit")
                        preco_texto = preco_el.text 
                        preco_formatado = preco_texto
                        valor_excel = preco_texto.replace("R$", "").replace(" ", "").replace("\xa0", "").strip()

                        # Só adiciona se o nome existir e o valor não for zero/vazio
                        if nome and valor_excel and valor_excel != "0,00":
                            dados_totais.append({
                                "Busca": termo,
                                "Produto": nome,
                                "Preço": preco_formatado,
                                "Valor Numérico": valor_excel
                            })

                    except Exception:
                        # Se não encontrar o preço, ignora silenciosamente e vai para o próximo produto
                        continue
                        
            except Exception as e:
                print(f"⚠️ Erro ao buscar '{termo}' ou site demorou muito. Pulando para a próxima palavra.")
                continue 

    finally:
        driver.quit()

        if dados_totais:
            df = pd.DataFrame(dados_totais)
            nome_arquivo = "precos_giassi.csv"
            df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8-sig')
            print(f"\nSucesso! Arquivo '{nome_arquivo}' criado do Giassi com {len(dados_totais)} produtos válidos.")
        else:
            print("\nNenhum dado coletado no Giassi.")

if __name__ == "__main__":
    extrair_giassi_url_direta()