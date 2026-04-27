import json
import pandas as pd
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def configurar_driver():
    options = Options()
    # options.add_argument("--headless") # Se quiser rodar escondido
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # User-agent real para passar por "humano"
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extrair_preco_do_json(produto):
    """Lógica para achar o preço dentro da resposta da API."""
    try:
        # 1. Tenta pegar do primeiro SKU (variação)
        if 'skus' in produto and len(produto['skus']) > 0:
            sku = produto['skus'][0]
            # Preço promocional (sellingPrice) ou normal (bestPrice)
            if 'offers' in sku and len(sku['offers']) > 0:
                return sku['offers'][0].get('salesPrice', 0.0)
            if 'bestPrice' in sku:
                val = sku['bestPrice']
                return val / 100 if val > 1000 else val # Ajuste caso venha em centavos

        # 2. Tenta pegar da raiz
        if 'price' in produto:
            return produto['price']
    except:
        pass
    return 0.0

def extrair_fort():
    driver = configurar_driver()
    
    # --- TRUQUE DE MESTRE: Configurar o Header 'Referer' ---
    # Isso engana a API dizendo que a requisição veio do próprio site do Fort
    # Evita o erro 403 (Senha/Bloqueio)
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
        'headers': {
            'Referer': 'https://www.deliveryfort.com.br/',
            'Origin': 'https://www.deliveryfort.com.br'
        }
    })
    
    # Termos de busca
    if len(sys.argv) > 1:
        termos = sys.argv[1:]
    else:
        termos = ["arroz"]
    
    print(f"📋 Lista de busca: {termos}")
    
    dados_totais = []

    try:
        for termo in termos:
            print(f"\n--- Processando: {termo} ---")
            
            # Navega nas páginas 1, 2 e 3
            for pagina in range(1, 4):
                print(f"📡 Acessando API - Página {pagina}...")
                
                # URL da API da Linx (que você descobriu no href)
                # Adicionamos os parâmetros para garantir a resposta JSON
                url_api = (
                    f"https://api.linximpulse.com/engage/search/v3/search?"
                    f"apikey=deliveryfort&terms={termo}&resultsPerPage=32"
                    f"&salesChannel=2&page={pagina}&sortBy=relevance"
                    f"&showOnlyAvailable=true&format=json"
                )
                
                driver.get(url_api)
                
                # Pega o texto do corpo da página (que será o JSON puro)
                conteudo = driver.find_element(By.TAG_NAME, "body").text
                
                # Verifica se deu erro de acesso
                if "Access Denied" in conteudo or "Forbidden" in conteudo:
                    print("   ⛔ Acesso negado pela API (Check de segurança).")
                    break
                
                try:
                    dados = json.loads(conteudo)
                except json.JSONDecodeError:
                    print("   ⚠️ Resposta não é um JSON válido. Pulei esta página.")
                    break
                
                # Extrai a lista de produtos
                lista_produtos = dados.get('products', [])
                if not lista_produtos:
                    print("   ⏹️ Fim dos resultados para este termo.")
                    break
                
                contador = 0
                for prod in lista_produtos:
                    nome = prod.get('name', '')
                    if not nome: continue
                    
                    preco_num = extrair_preco_do_json(prod)
                    
                    if preco_num > 0:
                        dados_totais.append({
                            "Termo": termo,
                            "Produto": nome,
                            "Preço": f"R$ {preco_num:,.2f}".replace(".", ",")
                        })
                        contador += 1
                        
                print(f"   ✅ {contador} itens extraídos.")
                time.sleep(1) # Pausa leve

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

        if dados_totais:
            df = pd.DataFrame(dados_totais)
            df = df.drop_duplicates(subset=['Produto', 'Preço'])
            nome_arquivo = "precos_fort.csv"
            df.to_csv(nome_arquivo, index=False, sep=';', encoding='utf-8-sig')
            print(f"\n💾 SUCESSO! '{nome_arquivo}' salvo com {len(df)} produtos.")
        else:
            print("\n❌ Nenhum dado coletado.")

if __name__ == "__main__":
    extrair_fort()