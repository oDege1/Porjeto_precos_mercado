import subprocess
import pandas as pd
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- IMPORTAÇÃO DA FUNCIONALIDADE DE ENCARTES ---
try:
    from atualizador_encartes import processar_encartes
except ImportError:
    print("⚠️ Módulo 'atualizador_encartes.py' não encontrado. A integração não funcionará.")
    processar_encartes = None

# --- 1. CONFIGURAÇÃO CENTRAL ---
TERMOS_BUSCA = ["leite", "ovo", "carne", "arroz", "feijão"]

SCRIPTS_CONFIG = [
    {"script": "Scrappers/Angeloni.py", "output": "precos_angeloni.csv", "mercado": "Angeloni"},
    {"script": "Scrappers/Bistek.py",   "output": "precos_bistek.csv",   "mercado": "Bistek"},
    {"script": "Scrappers/Fort.py",     "output": "precos_fort.csv",     "mercado": "Fort Atacadista"},
    {"script": "Scrappers/Giassi.py",   "output": "precos_giassi.csv",   "mercado": "Giassi"},
    {"script": "Scrappers/Koch.py",     "output": "precos_koch.csv",     "mercado": "Super Koch"},
    {"script": "Scrappers/Prado.py",    "output": "precos_prado.csv",    "mercado": "Prado Supermercado"}
]

def limpar_ambiente_inicial():
    print("🧹 Preparando terreno (Limpando CSVs antigos)...")
    for item in SCRIPTS_CONFIG:
        if os.path.exists(item["output"]):
            try:
                os.remove(item["output"])
            except:
                pass

def limpar_residuos_finais():
    print("\n🧹 Sanitizando ambiente (Removendo arquivos temporários)...")
    removidos = 0
    for item in SCRIPTS_CONFIG:
        arquivo = item["output"]
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                pass
    print(f"   ✅ {removidos} arquivos temporários removidos.")

def rodar_script(config_item):
    caminho_script = config_item["script"]
    mercado = config_item["mercado"]
    print(f"🚀 Iniciando {mercado}...")
    
    if not os.path.exists(caminho_script):
        print(f"❌ ERRO CRÍTICO: Script não encontrado: {caminho_script}")
        return False
    try:
        comando = ["python", caminho_script] + TERMOS_BUSCA
        subprocess.run(comando, check=True) 
        print(f"✅ {mercado} finalizado.")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Falha em {mercado}.")
        return False

def converter_preco_br(valor):
    if pd.isna(valor): return 0.0
    valor_str = str(valor).replace("R$", "").replace(" ", "").strip()
    # Verifica se a palavra 'indisponível' ou similar veio no lugar do preço
    if not any(char.isdigit() for char in valor_str):
        return 0.0
        
    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str:
        valor_str = valor_str.replace(",", ".")
    try:
        return float(valor_str)
    except:
        return 0.0

# --- LÓGICA ATUALIZADA DE CÁLCULO ---
def calcular_preco_proporcional(row):
    produto = str(row['Produto']).lower()
    preco = row['Valor_Num']
    
    if preco <= 0:
        return pd.Series(["Padrão", preco])

    # Expressões Regulares aprimoradas
    padrao_peso = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|g)\b', produto)
    padrao_volume = re.search(r'(\d+(?:[\.,]\d+)?)\s*(l|litro|litros|ml)\b', produto)
    # Busca prefixos como c/20, com 12, contém 30
    padrao_un_prefixo = re.search(r'(?:c/|com|contém)\s*(\d+)', produto)
    # Busca sufixos como 30 ovos, 12 unidades
    padrao_un_sufixo = re.search(r'(\d+)\s*(unidades?|un|ovos?)\b', produto)

    fator = 1.0
    medida_base = "1 Un/Kg/L (Padrão)"

    if padrao_peso:
        valor_medida = float(padrao_peso.group(1).replace(',', '.'))
        if padrao_peso.group(2) == 'g':
            fator = valor_medida / 1000.0
            medida_base = "Preço por Kg"
        else: 
            fator = valor_medida
            medida_base = "Preço por Kg"
            
    elif padrao_volume:
        valor_medida = float(padrao_volume.group(1).replace(',', '.'))
        if padrao_volume.group(2) == 'ml':
            fator = valor_medida / 1000.0
            medida_base = "Preço por Litro"
        else:
            fator = valor_medida
            medida_base = "Preço por Litro"
            
    elif padrao_un_prefixo:
        valor_medida = float(padrao_un_prefixo.group(1))
        fator = valor_medida
        medida_base = "Preço por Unidade"
        
    elif padrao_un_sufixo:
        valor_medida = float(padrao_un_sufixo.group(1))
        fator = valor_medida
        medida_base = "Preço por Unidade"

    preco_final = preco / fator if fator > 0 else preco
    return pd.Series([medida_base, round(preco_final, 2)])

def centralizar_dados():
    limpar_ambiente_inicial()
    print(f"\n--- INICIANDO BUSCA POR: {TERMOS_BUSCA} ---")
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(rodar_script, item) for item in SCRIPTS_CONFIG]
        for future in futures:
            future.result()

    print("\n--- CONSOLIDANDO DADOS ---")
    dfs_consolidados = []
    data_coleta = datetime.now().strftime("%d/%m/%Y")

    for config in SCRIPTS_CONFIG:
        arquivo = config["output"]
        mercado = config["mercado"]
        
        if not os.path.exists(arquivo):
            continue
            
        try:
            df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig")
            colunas_map = {
                "Termo Buscado": "Termo", "Busca": "Termo",
                "Produto": "Produto", "Nome": "Produto", "Nome do Produto": "Produto",
                "Preco": "Preço", "Preço": "Preço", "Valor": "Preço"
            }
            df = df.rename(columns=colunas_map)
            
            cols_finais = ["Termo", "Produto", "Preço"]
            if all(col in df.columns for col in cols_finais):
                df_final = df[cols_finais].copy()
                df_final["Mercado"] = mercado
                df_final["Data"] = data_coleta
                dfs_consolidados.append(df_final)
        except Exception as e:
            print(f"❌ Erro ao ler arquivo do {mercado}: {e}")

    if dfs_consolidados:
        df_total = pd.concat(dfs_consolidados, ignore_index=True)
        
        # 1. Transforma tudo o que for preço em número (textos viram 0.0)
        df_total["Valor_Num"] = df_total["Preço"].apply(converter_preco_br)
        
        # 2. FILTRO BLINDADO: Remove qualquer linha que tenha valor zerado ou nulo
        df_total = df_total[df_total["Valor_Num"] > 0].copy()
        
        # 3. Calcula as proporções apenas para os produtos válidos restantes
        if not df_total.empty:
            df_total[['Tipo_Medida', 'Preço_Proporcional']] = df_total.apply(calcular_preco_proporcional, axis=1)
            
            df_total = df_total.drop_duplicates()

            nome_final = "COMPARATIVO_FINAL.csv"
            df_total = df_total[["Termo", "Produto", "Preço", "Valor_Num", "Tipo_Medida", "Preço_Proporcional", "Mercado", "Data"]]
            df_total.to_csv(nome_final, index=False, sep=";", encoding="utf-8-sig")
            
            print("\n" + "="*40)
            print(f"✅ RELATÓRIO FINAL GERADO: {nome_final}")
            print(f"📊 Total de produtos válidos encontrados: {len(df_total)}")
            print("="*40)
        else:
            print("\n❌ Após os filtros, nenhum dado válido com preço sobrou para salvar.")

        limpar_residuos_finais()

        if processar_encartes:
            processar_encartes()
    else:
        print("\n❌ Nenhum dado coletado.")

if __name__ == "__main__":
    centralizar_dados()