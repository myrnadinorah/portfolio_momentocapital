import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

mysql_connection_string = os.getenv("MYSQL_CONNECTION_STRING")

if not mysql_connection_string:
    st.error("MySQL connection string is missing. Check your .env file.")
    st.stop()
    

engine = create_engine(mysql_connection_string)

query_equity = "SELECT * FROM Equity;"
query_metrics = "SELECT * FROM Metrics;"
query_trades = "SELECT * FROM Trades_Metrics;"

st.title("Portfolio Dashboard with Trades Metrics")

try:
    df_equity = pd.read_sql(query_equity, con=engine)
    df_metrics = pd.read_sql(query_metrics, con=engine)
    df_trades = pd.read_sql(query_trades, con=engine)
    st.success("Data successfully fetched from MySQL!")
except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")
    st.stop()

portfolio_ids = df_equity['portfolio_id'].unique()
if portfolio_ids.size == 0:
    st.warning("No portfolios available in the database.")
    st.stop()

portfolio_groups = {}
for portfolio_id in portfolio_ids:
    prefix = portfolio_id.split('-')[0]
    if prefix not in portfolio_groups:
        portfolio_groups[prefix] = []
    portfolio_groups[prefix].append(portfolio_id)

st.sidebar.title("Portfolio Groups")
selected_group = st.sidebar.selectbox("Select a Group", options=list(portfolio_groups.keys()))

selected_portfolio_id = st.sidebar.radio(
    f"Portfolios in {selected_group}", portfolio_groups[selected_group]
)

filtered_equity = df_equity[df_equity['portfolio_id'] == selected_portfolio_id].copy()
filtered_metrics = df_metrics[df_metrics['portfolio_id'] == selected_portfolio_id].copy()
filtered_trades = df_trades[df_trades['portfolio_id'] == selected_portfolio_id].copy()

if filtered_equity.empty and filtered_metrics.empty and filtered_trades.empty:
    st.warning(f"No data available for Portfolio ID {selected_portfolio_id}.")
    st.stop()

if not filtered_equity.empty:
    filtered_equity['Date'] = pd.to_datetime(filtered_equity['Date'])

if not filtered_equity.empty:
    st.subheader(f"Equity: Date vs Value for Portfolio ID {selected_portfolio_id}")
    equity_fig = px.line(
        filtered_equity, 
        x='Date', 
        y='Value', 
        title=f'Equity: Date vs Value for Portfolio ID {selected_portfolio_id}',
        labels={'Value': 'Equity Value', 'Date': 'Date'}
    )
    equity_fig.update_layout(template="plotly_white")
    st.plotly_chart(equity_fig)

if not filtered_metrics.empty:
    st.subheader("Metrics")

    transposed_metrics = filtered_metrics.set_index('portfolio_id').transpose()

    st.table(transposed_metrics)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
filtered_trades['Fecha_inicio'] = pd.to_datetime(filtered_trades['Fecha_inicio'])
trades_last_month = filtered_trades[
    (filtered_trades['Fecha_inicio'] >= start_date) & (filtered_trades['Fecha_inicio'] <= end_date)
]

if not trades_last_month.empty:
    st.subheader(f"Trades Metrics for Portfolio ID {selected_portfolio_id} (Last Month)")
    st.table(
        trades_last_month[
            ['Fecha_inicio', 'Fecha_salida', 'Plazo_dias', 'Asset', 'TWRR', 'MAE', 'MFE', 'TPR', 'Return_to_TPR']
        ]
    )
else:
    st.warning(f"No trades data available for the last month for Portfolio ID {selected_portfolio_id}.")
