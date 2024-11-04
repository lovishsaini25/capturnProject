import streamlit as st
import yfinance as yf
import numpy as np
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from shares import share_list

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

st.title("Capturn Stock Tool")

ticker = st.text_input("Enter stock ticker symbol:", value="RELIANCE")

st.write("Select a timeframe:")
timeframe = st.radio("Timeframe", ["1M", "3M", "6M", "1Y", "3Y", "5Y", "All"], horizontal=True)

end_date = datetime.now()
if timeframe == "All":
    start_date = None
else:
    timeframe_mapping = {
        "1M": timedelta(days=30),
        "3M": timedelta(days=90),
        "6M": timedelta(days=180),
        "1Y": timedelta(days=365),
        "3Y": timedelta(days=3 * 365),
        "5Y": timedelta(days=5 * 365),
    }
    start_date = end_date - timeframe_mapping[timeframe]

if st.button("Search"):
    if ticker:
        try:
            stock_data = yf.download(f'{ticker}.NS', start=start_date, end=end_date)
            stock_data.columns = stock_data.columns.map(lambda x: x[0])
            if not stock_data.empty:
                # Calculate UD Ratio
                ud_ratio, up_volume_ratio = calculate_ud_ratio(stock_data)
                st.write(f"UD Ratio for {ticker} over {timeframe}: {ud_ratio:.2f} and UD Volume ratio is {up_volume_ratio:.2f}"
                         if ud_ratio else "Insufficient data to calculate UD Ratio.")
                
                # Add technical indicators
                stock_data = add_technical_indicators(stock_data)
                
                # Display technical indicators for the last day
                last_day_summary = stock_data.iloc[-1][[
                    'MACD_12_26_9', 'RSI_14', 'BBL_5_2.0', 'BBM_5_2.0', 'BBU_5_2.0', 'SMA_20', 'EMA_50'
                ]]
                st.write("Summary of Technical Indicators for the Last Day:")
                st.dataframe(last_day_summary)
                
                # Interactive Plot with Plotly
                st.write("Technical Indicator Charts:")
                fig = go.Figure()

                # Add candlestick chart for stock price
                fig.add_trace(go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['Open'],
                    high=stock_data['High'],
                    low=stock_data['Low'],
                    close=stock_data['Close'],
                    name='Candlestick'
                ))

                # Add SMA and EMA lines
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

                # Add Bollinger Bands with improved appearance
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
                    fillcolor="rgba(173, 216, 230, 0.3)"  # Light blue with transparency
                ))

                fig.update_layout(
                    title=f"{ticker} Price with Technical Indicators",
                    yaxis_title="Price",
                    xaxis_title="Date",
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark"
                )

                st.plotly_chart(fig)

            else:
                st.write("No data available for the selected ticker and timeframe.")
                
        except Exception as e:
            st.write(f"Error: {e}")
    else:
        st.write("Please enter a valid stock ticker symbol.")

if st.button("Compute UD Ratio for Top 50 Companies"):
    results = []
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
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
        
        # Update progress bar and message
        progress_bar.progress((i + 1) / total_companies)
        progress_text.text(f"{i + 1} out of {total_companies} companies done.")
    
    # Sort by UD ratio and select top 50 companies
    results = sorted(results, key=lambda x: x[1], reverse=True)[:50]
    result_industry_sector = sorted(result_industry_sector.items(), key=lambda x: x[1], reverse=True)
    top_50_df = pd.DataFrame(results, columns=["Ticker", "UD Ratio", "UD Volume Ratio"])
    st.write("Top 50 Companies by UD Ratio:")
    st.dataframe(top_50_df)
    result_industry_sector= pd.DataFrame(result_industry_sector, columns=["Industry/Sector", "UD Ratio"])
    st.write("Top Industries by UD Ratio:")
    st.dataframe(result_industry_sector)
    
    # Clear the progress display
    progress_text.empty()
    progress_bar.empty()
