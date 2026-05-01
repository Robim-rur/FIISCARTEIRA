import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Analista Buy Side - B3", layout="wide")

st.title("📊 Probabilidade de Compra Pós Data-Ex")

# --- FUNÇÕES COM CACHE PARA EVITAR RATE LIMIT ---
@st.cache_data(ttl=3600)  # Guarda os dados por 1 hora (3600 segundos)
def buscar_dados(ticker):
    try:
        asset = yf.Ticker(ticker)
        # Buscamos 5 anos para ter uma base estatística sólida
        df = asset.history(period="5y")
        dividends = asset.dividends
        return df, dividends
    except Exception as e:
        return None, None

def analisar_estatistica(df, dividends, days_window):
    if dividends.empty or df.empty:
        return None
    
    # Filtrar dividendos dentro do período do histórico
    dividends = dividends[dividends.index >= df.index[0]]
    analise_resultados = []

    for ex_date in dividends.index:
        try:
            # Localizar índice da Data-Ex
            idx_ex = df.index.get_indexer([ex_date], method='pad')[0]
            if idx_ex <= 0: continue
            
            # Pegar preço de fechamento da Data-Com (dia anterior)
            price_com = df.iloc[idx_ex - 1]['Close']
            
            # Janela de preços após a Data-Ex
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
    df, dividends = buscar_dados(ticker_selecionado)
    
    if df is None or dividends is None or dividends.empty:
        st.error(f"Erro ao buscar dados ou o Yahoo bloqueou o acesso temporariamente. Tente novamente em alguns minutos ou troque o ativo.")
    else:
        res_serie = analisar_estatistica(df, dividends, janela_dias)
        
        if res_serie is not None and not res_serie.empty:
            st.subheader(f"Resultado para {ticker_selecionado}")
            
            probabilidades = res_serie.value_counts(normalize=True).sort_index() * 100
            
            # Exibição
            cols = st.columns(len(probabilidades))
            for i, (dia, prob) in enumerate(probabilidades.items()):
                cols[i].metric(label=f"Dia {dia}", value=f"{prob:.1f}%")
            
            st.bar_chart(probabilidades)
            st.info("💡 O Dia 0 é a própria Data-Ex. As porcentagens indicam a chance da mínima ocorrer naquele dia específico.")
        else:
            st.warning("Histórico de proventos insuficiente para este ticker.")

st.markdown("---")
st.caption("Estratégia Buy Side: O tempo no mercado vence o timing, mas a estatística ajuda na entrada.")
