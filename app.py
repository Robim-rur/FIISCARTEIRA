import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configurações iniciais
st.set_page_config(page_title="Analista Buy Side - Probabilidade Data-Ex", layout="wide")

# Estilização básica
st.title("📊 Probabilidade Estatística de Compra")
st.markdown("""
Este app analisa o comportamento dos seus ativos após a **Data-Ex**. 
O objetivo é identificar em qual dia (após o desconto do dividendo) o mercado costuma oferecer o melhor preço de entrada.
""")

# Barra Lateral - Configurações
st.sidebar.header("Configurações de Análise")
lista_ativos = ["GGRC11.SA", "GARE11.SA", "DIVO11.SA", "IEEX11.SA", "UTLL11.SA", "AUVP11.SA"]
ticker_selecionado = st.sidebar.selectbox("Selecione o Ativo:", lista_ativos)
janela_dias = st.sidebar.slider("Dias de observação após Data-Ex:", 1, 15, 7)
periodo = st.sidebar.selectbox("Histórico de análise:", ["1y", "2y", "5y"], index=1)

def analisar_probabilidade(ticker, days_window, period):
    # Download de dados do ativo
    asset = yf.Ticker(ticker)
    df = asset.history(period=period)
    dividends = asset.dividends
    
    if dividends.empty:
        return None, None

    # Filtrar apenas dividendos que ocorreram dentro do período do dataframe
    dividends = dividends[dividends.index >= df.index[0]]
    
    analise_resultados = []

    for ex_date in dividends.index:
        try:
            # Localizar a posição da data-ex no dataframe de preços
            # A Data-Com é o dia útil anterior à Data-Ex
            idx_ex = df.index.get_indexer([ex_date], method='ffill')[0]
            
            if idx_ex <= 0: continue
            
            price_com = df.iloc[idx_ex - 1]['Close']
            
            # Pegar os preços 'Low' (mínimas) nos dias seguintes à Data-Ex
            prices_after = df.iloc[idx_ex : idx_ex + days_window]['Low']
            
            if not prices_after.empty:
                # Qual foi o dia da mínima (0 = próprio dia da Data-Ex)
                dia_da_minima = (prices_after.idxmin() - ex_date).days
                # Se o cálculo de dias der negativo ou maior que a janela por erro de feriado, ajustamos
                dia_da_minima = max(0, min(dia_da_minima, days_window))
                
                queda_percentual = ((prices_after.min() / price_com) - 1) * 100
                
                analise_resultados.append({
                    'dia_minima': dia_da_minima,
                    'queda': queda_percentual
                })
        except Exception:
            continue

    return pd.DataFrame(analise_resultados), len(dividends)

# Execução do App
if st.button("Calcular Probabilidades"):
    with st.spinner(f"Analisando histórico de {ticker_selecionado}..."):
        res_df, total_eventos = analisar_probabilidade(ticker_selecionado, janela_dias, periodo)
        
        if res_df is not None and not res_df.empty:
            st.subheader(f"Análise baseada em {total_eventos} eventos de dividendos")
            
            # Cálculo das Probabilidades
            probabilidades = res_df['dia_minima'].value_counts(normalize=True).sort_index() * 100
            queda_media = res_df.groupby('dia_minima')['queda'].mean()

            # Layout de Métricas
            cols = st.columns(len(probabilidades))
            for i, (dia, prob) in enumerate(probabilidades.items()):
                with cols[i]:
                    st.metric(label=f"Dia {dia}", value=f"{prob:.1f}%")
                    st.caption(f"Queda média: {queda_media[dia]:.2f}%")

            st.write("---")
            st.info(f"**Interpretação:** O dia com a maior porcentagem (%) é o dia em que o ativo teve a maior probabilidade de atingir o preço mais baixo após a Data-Ex.")
            
            # Gráfico Simples
            st.bar_chart(probabilidades)
            
        else:
            st.error("Não foram encontrados dados de proventos suficientes para este ativo no Yahoo Finance.")

# Rodapé
st.markdown("---")
st.caption("Estratégia Buy Side: Foque no acúmulo de ativos e no tempo de mercado.")
