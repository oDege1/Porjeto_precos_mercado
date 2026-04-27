import pandas as pd
import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher

ARQUIVO_ALVO = "COMPARATIVO_FINAL.csv"
ARQUIVO_INPUT_JSON = "encartes_gemini.json"
SIMILARIDADE_MINIMA = 0.85 

def calcular_similaridade(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

def calcular_preco_proporcional(produto, preco):
    produto = str(produto).lower()
    if preco <= 0:
        return "Padrão", preco

    # Mesmas Expressões Regulares aprimoradas do main.py
    padrao_peso = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|g)\b', produto)
    padrao_volume = re.search(r'(\d+(?:[\.,]\d+)?)\s*(l|litro|litros|ml)\b', produto)
    padrao_un_prefixo = re.search(r'(?:c/|com|contém)\s*(\d+)', produto)
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
    return medida_base, round(preco_final, 2)

def processar_encartes():
    print(f"\n🔎 Verificando dados de encartes em '{ARQUIVO_INPUT_JSON}'...")

    if not os.path.exists(ARQUIVO_INPUT_JSON):
        print("⚠️ Arquivo JSON não encontrado. Pulei a etapa de encartes.")
        return

    try:
        with open(ARQUIVO_INPUT_JSON, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                return
            dados_novos = json.loads(conteudo)
    except json.JSONDecodeError:
        print("❌ ERRO: O conteúdo de 'encartes_gemini.json' não é um JSON válido.")
        return

    if os.path.exists(ARQUIVO_ALVO):
        df = pd.read_csv(ARQUIVO_ALVO, sep=";", encoding="utf-8-sig")
    else:
        df = pd.DataFrame(columns=["Termo", "Produto", "Preço", "Mercado", "Data", "Valor_Num", "Tipo_Medida", "Preço_Proporcional"])

    print(f"📊 Processando {len(dados_novos)} itens do Encarte...")
    
    atualizados = 0
    adicionados = 0
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    for item in dados_novos:
        novo_produto = str(item.get('produto', '')).strip()
        novo_mercado = str(item.get('mercado', '')).strip()
        try:
            preco_raw = str(item.get('preco', 0)).replace(',', '.')
            novo_preco = float(preco_raw)
        except:
            continue

        if not novo_produto or novo_preco <= 0:
            continue
        
        mask_mercado = df['Mercado'].str.lower() == novo_mercado.lower()
        df_mercado = df[mask_mercado]
        
        melhor_match_idx = -1
        maior_score = 0
        
        for idx in df_mercado.index:
            produto_existente = str(df.at[idx, 'Produto'])
            score = calcular_similaridade(novo_produto, produto_existente)
            
            if score > maior_score:
                maior_score = score
                melhor_match_idx = idx
        
        if maior_score >= SIMILARIDADE_MINIMA:
            produto_nome_final = str(df.at[melhor_match_idx, 'Produto'])
            medida, preco_prop = calcular_preco_proporcional(produto_nome_final, novo_preco)
            
            df.at[melhor_match_idx, 'Preço'] = f"R$ {novo_preco:,.2f}".replace(".", ",")
            df.at[melhor_match_idx, 'Valor_Num'] = novo_preco
            df.at[melhor_match_idx, 'Data'] = f"{data_hoje} (Encarte)"
            df.at[melhor_match_idx, 'Tipo_Medida'] = medida
            df.at[melhor_match_idx, 'Preço_Proporcional'] = preco_prop
            atualizados += 1
        else:
            medida, preco_prop = calcular_preco_proporcional(novo_produto, novo_preco)
            nova_linha = {
                "Termo": "Encarte",
                "Produto": novo_produto,
                "Preço": f"R$ {novo_preco:,.2f}".replace(".", ","),
                "Mercado": novo_mercado,
                "Data": f"{data_hoje} (Encarte)",
                "Valor_Num": novo_preco,
                "Tipo_Medida": medida,
                "Preço_Proporcional": preco_prop
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
            adicionados += 1

    colunas_ordem = ["Termo", "Produto", "Preço", "Valor_Num", "Tipo_Medida", "Preço_Proporcional", "Mercado", "Data"]
    df = df[[col for col in colunas_ordem if col in df.columns]]
    df.to_csv(ARQUIVO_ALVO, index=False, sep=";", encoding="utf-8-sig")
    
    print("-" * 40)
    print(f"✅ ENCARTES INTEGRADOS COM SUCESSO!")
    print(f"   📝 Preços Atualizados: {atualizados}")
    print(f"   ✨ Produtos Novos: {adicionados}")
    print("-" * 40)

if __name__ == "__main__":
    processar_encartes()