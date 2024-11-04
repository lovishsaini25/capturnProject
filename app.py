import streamlit as st
import yfinance as yf
import numpy as np
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from shares import share_list

# Navigation
st.set_page_config(page_title="Capturn Stock Tool", layout="wide")
st.title("Capturn Stock Analysis Tool")

# Sidebar for Navigation
page = st.sidebar.selectbox("Navigate", ["Search Stock", "Compute UD Ratio for Top Companies"])

def calculate_ud_ratio(data):
    data['Change'] = data['Close'] - data['Open']
    up_days = (data['Change'] > 0).sum()
    down_days = (data['Change'] < 0).sum()
    up_volumes = data[data['Change'] > 0]['Volume'].sum()
    down_volumes = data[data['Change'] < 0]['Volume'].sum()
    ud_ratio = up_days / down_days if down_days != 0 else None
    ud_volume_ratio = up_volumes / down_volumes if down_volumes != 0 else None
    return ud_ratio, np.float64(ud_volume_ratio) if ud_volume_ratio else None

def add_technical_indicators(data):
    data.ta.macd(append=True)
    data.ta.rsi(append=True)
    data.ta.bbands(append=True)
    data.ta.sma(length=20, append=True)
    data.ta.ema(length=50, append=True)
    return data

if page == "Search Stock":
    # Ticker Input
    ticker = st.text_input("Enter stock ticker symbol:", value="RELIANCE", help="Example: RELIANCE")

    # Timeframe Selection
    timeframe = st.radio("Select a timeframe:", ["1M", "3M", "6M", "1Y", "3Y", "5Y", "All"], horizontal=True)

    end_date = datetime.now()
    start_date = None if timeframe == "All" else end_date - {
        "1M": timedelta(days=30),
        "3M": timedelta(days=90),
        "6M": timedelta(days=180),
        "1Y": timedelta(days=365),
        "3Y": timedelta(days=3 * 365),
        "5Y": timedelta(days=5 * 365),
    }[timeframe]

    if st.button("Search"):
        if ticker:
            try:
                stock_data = yf.download(f'{ticker}.NS', start=start_date, end=end_date)
                stock_data.columns = stock_data.columns.map(lambda x: x[0])
                if not stock_data.empty:
                    # Calculate UD Ratio
                    ud_ratio, up_volume_ratio = calculate_ud_ratio(stock_data)
                    st.subheader(f"UD Ratio for {ticker} over {timeframe}")
                    st.write(f"UD Ratio: {ud_ratio:.2f}, UD Volume Ratio: {up_volume_ratio:.2f}"
                             if ud_ratio else "Insufficient data to calculate UD Ratio.")

                    # Add technical indicators
                    stock_data = add_technical_indicators(stock_data)
                    last_day_summary = stock_data.iloc[-1][[
                        'MACD_12_26_9', 'RSI_14', 'BBL_5_2.0', 'BBM_5_2.0', 'BBU_5_2.0', 'SMA_20', 'EMA_50'
                    ]]
                    
                    with st.container():
                        st.subheader("Summary of Technical Indicators for the Last Day:")
                        st.dataframe(last_day_summary)

                        # Interactive Plot with Plotly
                        st.subheader("Technical Indicator Charts:")
                        fig = go.Figure()

                        fig.add_trace(go.Candlestick(
                            x=stock_data.index,
                            open=stock_data['Open'],
                            high=stock_data['High'],
                            low=stock_data['Low'],
                            close=stock_data['Close'],
                            name='Candlestick'
                        ))

                        fig.add_trace(go.Scatter(
                            x=stock_data.index,
                            y=stock_data['SMA_20'],
                            mode="lines",
                            name="SMA 20",
                            line=dict(width=2, color="blue")
                        ))

                        fig.add_trace(go.Scatter(
                            x=stock_data.index,
                            y=stock_data['EMA_50'],
                            mode="lines",
                            name="EMA 50",
                            line=dict(width=2, color="orange")
                        ))

                        fig.add_trace(go.Scatter(
                            x=stock_data.index,
                            y=stock_data['BBL_5_2.0'],
                            line=dict(color="lightblue", width=1, dash="dot"),
                            showlegend=False
                        ))

                        fig.add_trace(go.Scatter(
                            x=stock_data.index,
                            y=stock_data['BBU_5_2.0'],
                            fill="tonexty",
                            mode="lines",
                            line=dict(color="lightblue", width=1, dash="dot"),
                            name="Bollinger Bands",
                            fillcolor="rgba(173, 216, 230, 0.3)"
                        ))

                        fig.update_layout(
                            title=f"{ticker} Price with Technical Indicators",
                            yaxis_title="Price",
                            xaxis_title="Date",
                            xaxis_rangeslider_visible=False,
                            template="plotly_dark"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning("No data available for the selected ticker and timeframe.")

            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter a valid stock ticker symbol.")

elif page == "Compute UD Ratio for Top Companies":
    if st.button("Compute UD Ratio for Top 50 Companies"):
        results = []
        progress_bar = st.progress(0)
        progress_text = st.empty()
        end_date = datetime.now()
        total_companies = len(share_list)
        start_date = end_date - timedelta(days=30)
        result_industry_sector = {}
        
        for i, symbol in enumerate(share_list):
            try:
                stock_data = yf.download(f'{symbol}.NS', start=start_date, end=end_date)
                stock_data.columns = stock_data.columns.map(lambda x: x[0])
                if not stock_data.empty:
                    ud_ratio, ud_volume_ratio = calculate_ud_ratio(stock_data)
                    if ud_ratio and ud_volume_ratio:
                        results.append((symbol, ud_ratio, ud_volume_ratio))
                        stock_data_industry = yf.Ticker(f'{symbol}.NS').info
                        result_industry_sector[stock_data_industry.get('industry')] = result_industry_sector.get(stock_data_industry.get('industry'), 0) + ud_ratio
            except Exception as e:
                st.write(f"Error fetching data for {symbol}: {e}")

            progress_bar.progress((i + 1) / total_companies)
            progress_text.text(f"{i + 1} out of {total_companies} companies done.")
        
        results = sorted(results, key=lambda x: x[1], reverse=True)[:50]
        result_industry_sector = sorted(result_industry_sector.items(), key=lambda x: x[1], reverse=True)
        
        top_50_df = pd.DataFrame(results, columns=["Ticker", "UD Ratio", "UD Volume Ratio"])
        st.subheader("Top 50 Companies by UD Ratio:")
        st.dataframe(top_50_df)
        
        result_industry_sector_df = pd.DataFrame(result_industry_sector, columns=["Industry/Sector", "UD Ratio"])
        st.subheader("Top Industries by UD Ratio:")
        st.dataframe(result_industry_sector_df)
        
        progress_text.empty()
        progress_bar.empty()
