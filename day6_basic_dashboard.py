# Step 1: Basic imports and page setup
import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set up the page configuration
st.set_page_config(
    page_title="Trading Journal - Day 6",
    page_icon="📈",
    layout="wide"
)

# Add a title
st.title("📈 Trading Journal Dashboard")
st.write("Day 6: Basic Dashboard with Metrics, Table, and P&L Chart")
st.markdown("---")

# Step 2: Create SIMPLE sample trade data
st.header("Step 2: Creating Sample Trade Data")

# Simple sample data
def create_simple_sample_data():
    data = {
        'id': [1, 2, 3, 4, 5],
        'date': ['2024-01-01 10:00', '2024-01-01 14:30', '2024-01-02 09:15',
                '2024-01-02 16:45', '2024-01-03 11:20'],
        'symbol': ['BTCUSDT', 'ETHUSDT', 'BTCUSDT', 'SOLUSDT', 'ETHUSDT'],
        'type': ['LONG', 'SHORT', 'LONG', 'LONG', 'SHORT'],
        'entry_price': [45000.50, 2400.75, 45500.25, 95.60, 2420.30],
        'exit_price': [45200.75, 2380.25, 45300.50, 97.25, 2395.40],
        'pnl': [200.25, -20.50, -199.75, 1.65, -24.90],
        'status': ['WIN', 'LOSS', 'LOSS', 'WIN', 'LOSS']
    }
    return pd.DataFrame(data)

# Create the data
st.write("Creating sample trade data...")
trades_df = create_simple_sample_data()

# Display basic info
st.write(f"**✅ Total Trades:** {len(trades_df)}")
st.write(f"**📅 Date Range:** {trades_df['date'].min()} to {trades_df['date'].max()}")

# Show the data
st.subheader("Trade Data Preview")
st.dataframe(trades_df)

st.success("Step 2 Complete! Sample data created successfully.")

# Step 3: Simple Metrics Display
st.markdown("---")
st.header("📊 Step 3: Key Trading Metrics")

# Create columns for metrics
col1, col2, col3, col4 = st.columns(4)

# Calculate metrics
total_pnl = trades_df['pnl'].sum()
winning_trades = trades_df[trades_df['status'] == 'WIN']
losing_trades = trades_df[trades_df['status'] == 'LOSS']
win_rate = len(winning_trades) / len(trades_df) * 100
avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0

# Display metrics in columns
with col1:
    st.metric(
        label="Total P&L",
        value=f"${total_pnl:.2f}",
        delta=f"${total_pnl:.2f}",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Win Rate",
        value=f"{win_rate:.1f}%",
        delta=f"{len(winning_trades)}/{len(trades_df)} trades"
    )

with col3:
    st.metric(
        label="Avg Win",
        value=f"${avg_win:.2f}" if avg_win != 0 else "$0.00"
    )

with col4:
    st.metric(
        label="Avg Loss",
        value=f"${avg_loss:.2f}" if avg_loss != 0 else "$0.00"
    )

# Additional metrics
st.subheader("Additional Statistics")

col5, col6, col7 = st.columns(3)

with col5:
    total_trades = len(trades_df)
    st.info(f"**Total Trades:** {total_trades}")

with col6:
    unique_symbols = trades_df['symbol'].nunique()
    st.info(f"**Symbols Traded:** {unique_symbols}")

with col7:
    profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if losing_trades['pnl'].sum() != 0 else "∞"
    st.info(f"**Profit Factor:** {profit_factor}")

st.success("Step 3 Complete! Metrics displayed successfully.")

# Step 4: Trade Table with Filtering
st.markdown("---")
st.header("🔍 Step 4: Trade Table with Filtering")

# Create filters in sidebar
st.sidebar.header("Filter Trades")

# Filter by symbol
all_symbols = ['All'] + list(trades_df['symbol'].unique())
selected_symbol = st.sidebar.selectbox(
    "Select Symbol:",
    all_symbols
)

# Filter by trade type
all_types = ['All'] + list(trades_df['type'].unique())
selected_type = st.sidebar.selectbox(
    "Select Trade Type:",
    all_types
)

# Filter by status
all_statuses = ['All'] + list(trades_df['status'].unique())
selected_status = st.sidebar.selectbox(
    "Select Status:",
    all_statuses
)

# Filter by P&L range
min_pnl = float(trades_df['pnl'].min())
max_pnl = float(trades_df['pnl'].max())
pnl_range = st.sidebar.slider(
    "Select P&L Range:",
    min_value=min_pnl,
    max_value=max_pnl,
    value=(min_pnl, max_pnl)
)

# Apply filters
filtered_df = trades_df.copy()

if selected_symbol != 'All':
    filtered_df = filtered_df[filtered_df['symbol'] == selected_symbol]

if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['type'] == selected_type]

if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

# Filter by P&L range
filtered_df = filtered_df[
    (filtered_df['pnl'] >= pnl_range[0]) &
    (filtered_df['pnl'] <= pnl_range[1])
    ]

# Display filter results
st.write(f"**Showing {len(filtered_df)} of {len(trades_df)} trades**")


# Style the dataframe with color coding
def color_pnl(val):
    if val > 0:
        return 'color: green; font-weight: bold;'
    elif val < 0:
        return 'color: red; font-weight: bold;'
    else:
        return 'color: gray;'


def color_status(val):
    if val == 'WIN':
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    else:
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'


# Apply styling
styled_df = filtered_df.style.applymap(color_pnl, subset=['pnl'])
styled_df = styled_df.applymap(color_status, subset=['status'])

# Display the styled dataframe
st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

# Summary of filtered results
if len(filtered_df) > 0:
    filtered_pnl = filtered_df['pnl'].sum()
    filtered_win_rate = len(filtered_df[filtered_df['status'] == 'WIN']) / len(filtered_df) * 100

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Filtered P&L:** ${filtered_pnl:.2f}")
    with col2:
        st.info(f"**Filtered Win Rate:** {filtered_win_rate:.1f}%")

st.success("Step 4 Complete! Filterable trade table implemented.")

# Step 5: Start of P&L Chart
st.markdown("---")
st.header("📈 Step 5: P&L Chart")

# First, let's fix the display issue from Step 4
# (Just a note - we'll see the chart now)

# Create a simple cumulative P&L chart
st.subheader("Cumulative P&L Over Time")

# Prepare data for chart
# Convert date string to datetime for sorting
chart_df = trades_df.copy()
chart_df['date_dt'] = pd.to_datetime(chart_df['date'])
chart_df = chart_df.sort_values('date_dt')

# Calculate cumulative P&L
chart_df['cumulative_pnl'] = chart_df['pnl'].cumsum()

# Create two columns for charts
col1, col2 = st.columns(2)

with col1:
    # Bar chart: P&L per trade
    st.write("**P&L per Trade**")

    # Create a color list for the bars
    colors = ['green' if pnl > 0 else 'red' for pnl in chart_df['pnl']]

    # Simple bar chart using Streamlit
    st.bar_chart(
        chart_df.set_index('date')['pnl'],
        color="#FF4B4B"  # Streamlit will use this for all bars
    )

    st.caption("Bar chart showing profit/loss for each trade")

with col2:
    # Line chart: Cumulative P&L
    st.write("**Cumulative P&L**")

    # Line chart
    st.line_chart(
        chart_df.set_index('date')['cumulative_pnl'],
        color="#00FF00"  # Green line
    )

    st.caption("Line chart showing running total of P&L")

# Add a more detailed chart using Plotly
st.subheader("Detailed P&L Analysis")

# Create tabs for different chart views
tab1, tab2, tab3 = st.tabs(["Cumulative P&L", "Trade Distribution", "Symbol Performance"])

with tab1:
    st.write("**Interactive Cumulative P&L Chart**")

    # Simple HTML table for now (we'll upgrade to Plotly next)
    st.write("Cumulative P&L progression:")

    # Show cumulative P&L table
    cum_table = chart_df[['date', 'pnl', 'cumulative_pnl']].copy()
    cum_table['pnl'] = cum_table['pnl'].apply(lambda x: f"${x:.2f}")
    cum_table['cumulative_pnl'] = cum_table['cumulative_pnl'].apply(lambda x: f"${x:.2f}")

    st.table(cum_table)

with tab2:
    st.write("**Trade Distribution**")

    # Count wins vs losses
    win_loss_counts = trades_df['status'].value_counts()

    # Display as metrics
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        st.metric("Winning Trades", value=len(winning_trades))
    with w_col2:
        st.metric("Losing Trades", value=len(losing_trades))

    # Simple pie chart data
    st.write("Win/Loss Ratio:")
    st.write(
        f"**{len(winning_trades)} Wins ({win_rate:.1f}%)** | **{len(losing_trades)} Losses ({100 - win_rate:.1f}%)**")

with tab3:
    st.write("**Performance by Symbol**")

    # Calculate P&L by symbol
    symbol_performance = trades_df.groupby('symbol').agg({
        'pnl': 'sum',
        'id': 'count'
    }).rename(columns={'id': 'trade_count', 'pnl': 'total_pnl'})

    # Sort by P&L
    symbol_performance = symbol_performance.sort_values('total_pnl', ascending=False)

    # Display
    for symbol, row in symbol_performance.iterrows():
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(f"**{symbol}**")
        with col2:
            st.write(f"{row['trade_count']} trades")
        with col3:
            pnl_color = "green" if row['total_pnl'] > 0 else "red"
            st.markdown(f"<span style='color: {pnl_color}; font-weight: bold;'>${row['total_pnl']:.2f}</span>",
                        unsafe_allow_html=True)

st.success("🎉 Day 6 Complete! Basic dashboard with metrics, filtering, and P&L chart is ready!")
st.balloons()

# Add this at the BOTTOM
if __name__ == "__main__":
    pass