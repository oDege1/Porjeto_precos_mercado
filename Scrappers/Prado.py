from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
import sys

if len(sys.argv) > 1:
    itens_para_pesquisar = sys.argv[1:]
else:
    itens_para_pesquisar = ["ovo", "leite"]

print(f"📋 Lista de busca (Prado): {itens_para_pesquisar}")
dados_totais = []

print("--- Iniciando Robô Prado (Modo Visível com Pausa) ---")
servico = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# NOTA: O Prado NÃO tem o --headless, então ele abrirá normalmente.

navegador = webdriver.Chrome(service=servico, options=options)
wait = WebDriverWait(navegador, 15)

try:
    for produto_pesquisa in itens_para_pesquisar:
        print(f"\n>>> Pesquisando: {produto_pesquisa.upper()}")
        
        navegador.get("https://loja.pradosupermercados.com.br/")
        
        print("⏳ Aguardando 10 segundos para verificações de segurança do navegador...")
        time.sleep(10) # PAUSA DE 10 SEGUNDOS ADICIONADA AQUI
        
        try:
            print("Acessando barra de pesquisa...")
            try:
                botao_busca = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Buscar produtos')]")))
                botao_busca.click()
            except:
                navegador.find_element(By.CSS_SELECTOR, ".icomoon-search").click()
            
            campo_input = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "input")))
            campo_input.clear()
            campo_input.send_keys(produto_pesquisa)
            time.sleep(1)
            campo_input.send_keys(Keys.ENTER)
            
        except Exception as e:
            print(f"Erro na busca: {e}")
            continue

        print("Carregando produtos (Movimento de leitura)...")
        tempo_limite = time.time() + 15 
        
        while time.time() < tempo_limite:
            navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            navegador.execute_script("window.scrollBy(0, -window.innerHeight);")
            time.sleep(1)

        elementos_nomes = navegador.find_elements(By.CSS_SELECTOR, ".line-clamp-3")
        count_sucesso = 0
        
        for elemento_nome in elementos_nomes:
            try:
                nome_produto = elemento_nome.text
                if not nome_produto: continue

                elemento_pai = elemento_nome
                preco_encontrado = "Não encontrado"
                
                for _ in range(4):
                    elemento_pai = elemento_pai.find_element(By.XPATH, "./..")
                    texto_completo = elemento_pai.text
                    
                    if "R$" in texto_completo:
                        match = re.search(r'R\$\s?[\d\.,]+', texto_completo)
                        if match:
                            preco_encontrado = match.group()
                            break
                
                if preco_encontrado != "Não encontrado":
                    dados_totais.append({
                        "Termo": produto_pesquisa,
                        "Produto": nome_produto,
                        "Preço": preco_encontrado
                    })
                    count_sucesso += 1

            except:
                continue 

    if dados_totais:
        df = pd.DataFrame(dados_totais)
        df = df.drop_duplicates()
        nome_arquivo = "precos_prado.csv"
        df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8-sig')

except Exception as e:
    print(f"Erro Geral: {e}")

finally:
    navegador.quit()