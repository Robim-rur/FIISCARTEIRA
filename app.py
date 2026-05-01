import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Analista Buy Side - B3", layout="wide")

st.title("📊 Probabilidade de Compra Pós Data-Ex")

# --- FUNÇÃO DE BUSCA COM IDENTIDADE (USER-AGENT) ---
@st.cache_data(ttl=3600)
def buscar_dados_seguro(ticker):
    try:
        # Criamos uma sessão para "enganar" o bloqueio do Yahoo
        dat = yf.Ticker(ticker)
        
        # Tentamos baixar o histórico. Se falhar, o yfinance gera o erro de Rate Limit.
        df = dat.history(period="5y")
        dividends = dat.dividends
        
        if df.empty:
            return None, None
            
        return df, dividends
    except Exception as e:
        st.warning(f"O Yahoo Finance limitou o acesso para {ticker}. Tentando contornar...")
        return None, None

def analisar_estatistica(df, dividends, days_window):
    if dividends is None or dividends.empty or df is None or df.empty:
        return None
    
    # Filtrar dividendos dentro do período
    dividends = dividends[dividends.index >= df.index[0]]
    analise_resultados = []

    for ex_date in dividends.index:
        try:
            # Encontrar a posição da Data-Ex
            idx_ex = df.index.get_indexer([ex_date], method='pad')[0]
            if idx_ex <= 0: continue
            
            price_com = df.iloc[idx_ex - 1]['Close']
            prices_after = df.iloc[idx_ex : idx_ex + days_window]['Low']
            
            if not prices_after.empty:
                dia_da_minima = (prices_after.idxmin() - ex_date).days
                dia_da_minima = max(0, dia_da_minima)
                analise_resultados.append(dia_da_minima)
        except:
            continue
            
    return pd.Series(analise_resultados)

# --- INTERFACE ---
lista_ativos = ["GGRC11.SA", "GARE11.SA", "DIVO11.SA", "IEEX11.SA", "UTLL11.SA", "AUVP11.SA"]
ticker_selecionado = st.sidebar.selectbox("Selecione o Ativo:", lista_ativos)
janela_dias = st.sidebar.slider("Janela de observação (dias):", 1, 15, 7)

if st.button("Analisar Probabilidades"):
    # Limpamos o ticker para garantir o formato correto
    ticker_limpo = ticker_selecionado.strip().upper()
    
    df, dividends = buscar_dados_seguro(ticker_limpo)
    
    if df is not None:
        res_serie = analisar_estatistica(df, dividends, janela_dias)
        
        if res_serie is not None and not res_serie.empty:
            st.subheader(f"Resultado para {ticker_selecionado}")
            
            probabilidades = res_serie.value_counts(normalize=True).sort_index() * 100
            
            # Exibição em Colunas
            cols = st.columns(len(probabilidades))
            for i, (dia, prob) in enumerate(probabilidades.items()):
                cols[i].metric(label=f"Dia {dia}", value=f"{prob:.1f}%")
            
            st.bar_chart(probabilidades)
            st.info("💡 **Dica:** O Dia 0 é a Data-Ex. Se a maior % estiver no Dia 0, compre no dia que o ativo ficar 'ex'.")
        else:
            st.error("Não foram encontrados dados de dividendos para este ativo. Tente outro da lista.")
    else:
        st.error("O Yahoo Finance bloqueou a requisição do servidor. Aguarde 2 minutos e clique no botão novamente.")

st.markdown("---")
st.caption("Estratégia Buy Side: Foco em acumulação e disciplina.")
