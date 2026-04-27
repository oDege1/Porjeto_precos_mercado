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

# --- CONFIGURAÇÃO ---
if len(sys.argv) > 1:
    itens_para_pesquisar = sys.argv[1:]
else:
    itens_para_pesquisar = ["ovo", "leite"]

print(f"📋 Lista de busca: {itens_para_pesquisar}")
dados_totais = []

print("--- Iniciando Robô (Modo Scroll Inteligente) ---")
servico = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
navegador = webdriver.Chrome(service=servico, options=options)
wait = WebDriverWait(navegador, 5)

try:
    for produto_pesquisa in itens_para_pesquisar:
        print(f"\n>>> Pesquisando: {produto_pesquisa.upper()}")
        
        navegador.get("https://www.superkoch.com.br")
        
        # --- 1. ETAPA DE BUSCA ---
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

        # --- 2. ETAPA DE SCROLL (Lógica 'Vai e Volta') ---
        print("Carregando produtos (Movimento de leitura)...")
        
        # Aumentei para 15s para dar tempo do movimento de subir e descer acontecer algumas vezes
        tempo_limite = time.time() + 15 
        
        while time.time() < tempo_limite:
            # A) Desce até o fim absoluto da página
            navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) # Espera o site "pensar" e carregar imagens novas
            
            # B) Sobe um pouco (1/4 da altura da janela visível)
            # Isso força o navegador a recalcular a visualização e carregar itens travados
            navegador.execute_script("window.scrollBy(0, -window.innerHeight);")
            time.sleep(1)

        # --- 3. ETAPA DE EXTRAÇÃO (Lógica Regex) ---
        elementos_nomes = navegador.find_elements(By.CSS_SELECTOR, ".line-clamp-3")
        print(f"Encontrei {len(elementos_nomes)} itens. Lendo dados...")
        
        count_sucesso = 0
        
        for elemento_nome in elementos_nomes:
            try:
                nome_produto = elemento_nome.text
                if not nome_produto: continue

                # Sobe na árvore HTML procurando o preço
                elemento_pai = elemento_nome
                preco_encontrado = "Não encontrado"
                
                for _ in range(4):
                    elemento_pai = elemento_pai.find_element(By.XPATH, "./..")
                    texto_completo = elemento_pai.text
                    
                    if "R$" in texto_completo:
                        # Procura padrão monetário (ex: R$ 10,90)
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

        print(f"Sucesso: {count_sucesso} produtos salvos de '{produto_pesquisa}'.")

    # --- 4. SALVAR ARQUIVO ---
    if dados_totais:
        df = pd.DataFrame(dados_totais)
        df = df.drop_duplicates()
        
        # MUDANÇA: Salvar como CSV padronizado
        nome_arquivo = "precos_koch.csv"
        df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"\nARQUIVO GERADO: '{nome_arquivo}' com {len(df)} produtos.")
        print(df.head())
    else:
        print("\nNenhum dado coletado.")

except Exception as e:
    print(f"Erro: {e}")

finally:
    navegador.quit()