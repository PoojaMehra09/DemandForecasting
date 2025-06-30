import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Retail Inventory & Demand Dashboard", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_excel("retail_store_inventory.xlsx")
    # Standardize column names for ease of use
    df.columns = [col.strip() for col in df.columns]
    # Convert date column if exists
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col])
            date_col = col
            break
    else:
        date_col = None
    return df, date_col

df, date_col = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔎 Filters")
stores = df['Store'].unique() if 'Store' in df.columns else []
categories = df['Category'].unique() if 'Category' in df.columns else []
products = df['Product'].unique() if 'Product' in df.columns else []

selected_stores = st.sidebar.multiselect("Select Store(s):", stores, default=list(stores)[:5] if len(stores) > 5 else stores)
selected_categories = st.sidebar.multiselect("Select Category(ies):", categories, default=list(categories)[:5] if len(categories) > 5 else categories)
selected_products = st.sidebar.multiselect("Select Product(s):", products, default=list(products)[:5] if len(products) > 5 else products)

if date_col:
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    selected_dates = st.sidebar.date_input("Select Date Range:", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    selected_dates = None

# --- APPLY FILTERS ---
mask = (
    (df['Store'].isin(selected_stores) if stores.any() else True) &
    (df['Category'].isin(selected_categories) if categories.any() else True) &
    (df['Product'].isin(selected_products) if products.any() else True)
)
if selected_dates and date_col:
    mask &= (df[date_col] >= pd.to_datetime(selected_dates[0])) & (df[date_col] <= pd.to_datetime(selected_dates[1]))

filtered_df = df[mask]

# --- HEADER ---
st.title("🏪 Retail Store Inventory & Demand Insights Dashboard")
st.markdown("""
This dashboard delivers detailed micro and macro analysis on retail inventory, demand, and supply chain health.
Use the left-side filters to drill down by store, category, product, and date.
""")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "KPIs & Overview", "Demand & Inventory Trends", "Product Insights",
    "Store Insights", "Category Insights", "Advanced Analysis"
])

# --- TAB 1: KPIs & OVERVIEW ---
with tab1:
    st.header("📊 Key Performance Indicators")
    st.markdown("High-level KPIs summarizing demand, inventory, sales, and stock health for your selected filters.")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Demand Forecast", int(filtered_df['Demand Forecast'].sum()))
    if 'Stock' in filtered_df.columns:
        col2.metric("Total Stock", int(filtered_df['Stock'].sum()))
    if 'Sales' in filtered_df.columns:
        col3.metric("Total Sales", int(filtered_df['Sales'].sum()))
    if 'Stockout' in filtered_df.columns:
        col4.metric("Stockout Days", int(filtered_df['Stockout'].sum()))
    if date_col:
        days = (filtered_df[date_col].max() - filtered_df[date_col].min()).days + 1
        col5.metric("Date Range (days)", days)
    st.markdown("These KPIs update instantly with your chosen filters.")

    st.markdown("**Data Preview** – First 100 Rows")
    st.dataframe(filtered_df.head(100), use_container_width=True)

# --- TAB 2: DEMAND & INVENTORY TRENDS ---
with tab2:
    st.header("📈 Demand vs Inventory Over Time")
    st.markdown("Visualize daily trends in forecasted demand, stock, and sales. Spot seasonality, gaps, and spikes.")
    if date_col:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=filtered_df[date_col], y=filtered_df['Demand Forecast'], name='Demand Forecast', mode='lines+markers'))
        if 'Stock' in filtered_df.columns:
            fig.add_trace(go.Scatter(x=filtered_df[date_col], y=filtered_df['Stock'], name='Stock', mode='lines+markers'))
        if 'Sales' in filtered_df.columns:
            fig.add_trace(go.Scatter(x=filtered_df[date_col], y=filtered_df['Sales'], name='Sales', mode='lines+markers'))
        fig.update_layout(xaxis_title='Date', yaxis_title='Value')
        st.plotly_chart(fig, use_container_width=True)

        # 7-day rolling average
        st.markdown("**7-Day Rolling Avg: Demand Forecast**")
        if len(filtered_df) > 7:
            roll = filtered_df[[date_col, 'Demand Forecast']].set_index(date_col).sort_index().rolling('7D').mean().dropna()
            st.line_chart(roll, use_container_width=True)
    else:
        st.info("No date column detected for time series trends.")

    st.markdown("**Top 10 Highest Demand Days**")
    if date_col:
        top_demand = filtered_df.groupby(date_col)['Demand Forecast'].sum().nlargest(10)
        fig2 = px.bar(top_demand, x=top_demand.index, y=top_demand.values, labels={"x": "Date", "y": "Total Demand"})
        st.plotly_chart(fig2, use_container_width=True)

# --- TAB 3: PRODUCT INSIGHTS ---
with tab3:
    st.header("🛒 Product-level Analysis")
    st.markdown("Uncover top- and bottom-performing products by demand, sales, and stock.")
    if 'Product' in filtered_df.columns:
        # Top 10 products by demand
        prod_demand = filtered_df.groupby('Product')['Demand Forecast'].sum().nlargest(10)
        st.markdown("**Top 10 Products by Demand Forecast**")
        fig3 = px.bar(prod_demand, x=prod_demand.index, y=prod_demand.values, labels={"x": "Product", "y": "Total Demand"})
        st.plotly_chart(fig3, use_container_width=True)

        if 'Sales' in filtered_df.columns:
            prod_sales = filtered_df.groupby('Product')['Sales'].sum().nlargest(10)
            st.markdown("**Top 10 Products by Sales**")
            fig4 = px.bar(prod_sales, x=prod_sales.index, y=prod_sales.values, labels={"x": "Product", "y": "Total Sales"})
            st.plotly_chart(fig4, use_container_width=True)
        
        if 'Stock' in filtered_df.columns:
            low_stock = filtered_df.groupby('Product')['Stock'].sum().nsmallest(10)
            st.markdown("**10 Lowest Stock Products**")
            fig5 = px.bar(low_stock, x=low_stock.index, y=low_stock.values, labels={"x": "Product", "y": "Total Stock"})
            st.plotly_chart(fig5, use_container_width=True)

        # ABC analysis (Pareto 80/20)
        st.markdown("**ABC Analysis: Cumulative Demand by Product**")
        abc = prod_demand.sort_values(ascending=False)
        cum_pct = abc.cumsum() / abc.sum()
        abc_df = pd.DataFrame({'Product': abc.index, 'Demand': abc.values, 'Cumulative%': cum_pct.values})
        st.dataframe(abc_df.head(20), use_container_width=True)
        fig6 = px.line(abc_df, x='Product', y='Cumulative%', markers=True)
        st.plotly_chart(fig6, use_container_width=True)

# --- TAB 4: STORE INSIGHTS ---
with tab4:
    st.header("🏬 Store-level Analysis")
    st.markdown("Compare demand, sales, and stock across stores. Identify high- or low-performing locations.")
    if 'Store' in filtered_df.columns:
        store_demand = filtered_df.groupby('Store')['Demand Forecast'].sum().sort_values(ascending=False)
        st.markdown("**Demand Forecast by Store**")
        fig7 = px.bar(store_demand, x=store_demand.index, y=store_demand.values, labels={"x": "Store", "y": "Total Demand"})
        st.plotly_chart(fig7, use_container_width=True)
        
        if 'Stock' in filtered_df.columns:
            store_stock = filtered_df.groupby('Store')['Stock'].sum()
            st.markdown("**Stock by Store**")
            fig8 = px.bar(store_stock, x=store_stock.index, y=store_stock.values, labels={"x": "Store", "y": "Total Stock"})
            st.plotly_chart(fig8, use_container_width=True)
            
            # Stock vs demand scatter
            store_compare = pd.DataFrame({'Demand': store_demand, 'Stock': store_stock}).dropna()
            st.markdown("**Stock vs Demand Scatter by Store**")
            fig9 = px.scatter(store_compare, x='Demand', y='Stock', text=store_compare.index)
            st.plotly_chart(fig9, use_container_width=True)

        if 'Sales' in filtered_df.columns:
            store_sales = filtered_df.groupby('Store')['Sales'].sum()
            st.markdown("**Sales by Store**")
            fig10 = px.bar(store_sales, x=store_sales.index, y=store_sales.values, labels={"x": "Store", "y": "Total Sales"})
            st.plotly_chart(fig10, use_container_width=True)

# --- TAB 5: CATEGORY INSIGHTS ---
with tab5:
    st.header("📦 Category-level Insights")
    st.markdown("Analyze demand and sales trends at the category level for strategic supply planning.")
    if 'Category' in filtered_df.columns:
        cat_demand = filtered_df.groupby('Category')['Demand Forecast'].sum().sort_values(ascending=False)
        st.markdown("**Demand Forecast by Category**")
        fig11 = px.bar(cat_demand, x=cat_demand.index, y=cat_demand.values, labels={"x": "Category", "y": "Total Demand"})
        st.plotly_chart(fig11, use_container_width=True)
        
        if 'Sales' in filtered_df.columns:
            cat_sales = filtered_df.groupby('Category')['Sales'].sum()
            st.markdown("**Sales by Category (Pie Chart)**")
            fig12 = px.pie(cat_sales, values=cat_sales.values, names=cat_sales.index)
            st.plotly_chart(fig12, use_container_width=True)

        if 'Stock' in filtered_df.columns:
            cat_stock = filtered_df.groupby('Category')['Stock'].sum()
            st.markdown("**Stock by Category**")
            fig13 = px.bar(cat_stock, x=cat_stock.index, y=cat_stock.values, labels={"x": "Category", "y": "Total Stock"})
            st.plotly_chart(fig13, use_container_width=True)

# --- TAB 6: ADVANCED ANALYSIS ---
with tab6:
    st.header("🔬 Advanced Insights")
    st.markdown("Explore anomalies, outliers, and custom pivots for advanced supply chain decisions.")

    # Outlier detection on Demand Forecast
    st.markdown("**Demand Forecast Outlier Detection (Boxplot)**")
    fig14 = px.box(filtered_df, y='Demand Forecast')
    st.plotly_chart(fig14, use_container_width=True)

    # Heatmap: Product vs Store by Demand
    if 'Product' in filtered_df.columns and 'Store' in filtered_df.columns:
        st.markdown("**Heatmap: Demand Forecast by Store and Product**")
        pivot = filtered_df.pivot_table(index='Product', columns='Store', values='Demand Forecast', aggfunc='sum', fill_value=0)
        fig15 = px.imshow(pivot, aspect='auto')
        st.plotly_chart(fig15, use_container_width=True)
    
    # Stockout alert table
    if 'Stockout' in filtered_df.columns:
        st.markdown("**Stockout Events Table**")
        st.dataframe(filtered_df[filtered_df['Stockout'] > 0], use_container_width=True)
    
    # Download filtered data
    st.markdown("**Download Filtered Data**")
    csv = filtered_df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "filtered_inventory.csv", "text/csv")

    st.markdown("**Custom Pivot Table (Demo)**")
    if 'Store' in filtered_df.columns and 'Category' in filtered_df.columns:
        pivot2 = pd.pivot_table(filtered_df, values='Demand Forecast', index='Store', columns='Category', aggfunc=np.sum, fill_value=0)
        st.dataframe(pivot2)

    st.markdown("**Histogram: Demand Forecast Distribution**")
    fig16 = px.histogram(filtered_df, x='Demand Forecast', nbins=30)
    st.plotly_chart(fig16, use_container_width=True)

    # More: add your own pivots, time trends, histograms, boxplots, custom queries as needed!

# --- END OF APP ---
