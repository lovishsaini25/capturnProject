import streamlit as st
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

def calculate_ud_ratio(data):
    data['Change'] = data['Close']-data['Open']
    up_days = (data['Change'] > 0).sum()
    down_days = (data['Change'] < 0).sum()
    up_volumes = data[data['Change'] > 0]['Volume'].sum()
    down_volumes = data[data['Change'] < 0]['Volume'].sum()
    ud_ratio = up_days / down_days if down_days != 0 else None
    ud_volume_ratio = up_volumes / down_volumes
    return ud_ratio, np.float64(ud_volume_ratio)

st.title("Stock UD Ratio Calculator")

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
            
            if not stock_data.empty:
                ud_ratio, up_volume_ratio = calculate_ud_ratio(stock_data)
                st.write(f"UD Ratio for {ticker} over {timeframe}: {ud_ratio:.2f} and UD Volume ratio is {up_volume_ratio:.2f}"
                         if ud_ratio else "Insufficient data to calculate UD Ratio.")
            else:
                st.write("No data available for the selected ticker and timeframe.")
                
        except Exception as e:
            st.write(f"Error: {e}")
    else:
        st.write("Please enter a valid stock ticker symbol.")
