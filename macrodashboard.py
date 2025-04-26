import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

#tip = yf.download("TIP")
#print(tip)


# Set page config
st.set_page_config(page_title="Macro Dashboard", layout="wide")

# Title
st.title("🌎 Fast Macro Dashboard (Free Version)")

# Sidebar - Country Selection
countries = {
    "United States": {
        "TIP": "Inflation Protection ETF",
        "^TNX": "US 10Y Yield",
        "^GSPC": "S&P500 Index",
        "XLI": "Industrials ETF"
    },
    "Germany": {
        "EWG": "Germany ETF"
    },
    "Japan": {
        "EWJ": "Japan ETF"
    },
    "Brazil": {
        "EWZ": "Brazil ETF"
    }
}

selected_country = st.sidebar.selectbox("Select Country", list(countries.keys()))
symbol_dict = countries[selected_country]

# Sidebar - Date Range
start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date.today())

# Sidebar - Auto Refresh
refresh = st.sidebar.checkbox("Auto-refresh every 5 minutes", value=False)

# Load Data
all_data = pd.DataFrame()

# Display Data
st.subheader(f"Indicators for {selected_country}")

for symbol, label in symbol_dict.items():
    df = yf.download(symbol, start=start_date, end=end_date)

    all_data = df

    # Drop rows where all are NaN
    all_data.dropna(how='all', inplace=True)
    st.line_chart(all_data["Close"], y=symbol)

# Optional: Refresh every 5 mins
if refresh:
    st.rerun(scope="app")
