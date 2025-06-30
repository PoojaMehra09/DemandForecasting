import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------- LOAD DATA -----------
@st.cache_data
def load_data():
    df = pd.read_excel("retail_store_inventory.xlsx")
    # Add date conversion if needed
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# ----------- SIDEBAR FILTERS -----------
st.sidebar.title("🔎 Filter Data")
stores = df['Store'].unique() if 'Store' in df.columns else []
categories = df['Category'].unique() if 'Category' in df.columns else []
products = df['Product'].unique() if 'Product' in df.columns else []

selected_stores = st.sidebar.multiselect("Select Store(s):", stores, default=stores)
selected_categories = st.sidebar.multiselect("Select Category(ies):", categories, default=categories)
selected_products = st.sidebar.multiselect("Select Product(s):", products, default=products)

if 'Date' in df.columns:
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    selected_dates = st.sidebar.date_input("Select Date Range:", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    selected_dates = None

# Apply filters
mask = (
    (df['Store'].isin(selected_stores) if stores.any() else True) &
    (df['Category'].isin(selected_categories) if categories.any() else True) &
    (df['Product'].isin(selected_products) if products.any() else True)
)
if selected_dates and 'Date' in df.columns:
    mask &= (df['Date'] >= pd.to_datetime(selected_dates[0])) & (df['Date'] <= pd.to_datetime(selected_dates[1]))

filtered_df = df[mask]

# ----------- DASHBOARD LAYOUT -----------
st.title("🏪 Retail Store Inventory & Demand Insights Dashboard")
st.markdown(
    "This dashboard provides micro and macro analysis of retail store inventory and demand, "
    "enabling Supply Chain leaders and stakeholders to drive data-backed decisions."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview KPIs", "Demand & Inventory Trends", "Product/Category Analysis",
    "Store Analysis", "Advanced & Custom"
])

# ----------- TAB 1: OVERVIEW KPIs -----------
with tab1:
    st.header("🔗 High-Level KPIs & Trends")
    st.markdown("These KPIs provide a snapshot of inventory, demand, and stock health across selected stores, products, and dates.")

    kpi1 = filtered_df['Demand Forecast'].sum()
    kpi2 = filtered_df['Stock'].sum() if 'Stock' in filtered_df.columns else 0
    kpi3 = filtered_df['Sales'].sum() if 'Sales' in filtered_df.columns else 0
    kpi4 = (filtered_df['Stockout'].sum() if 'Stockout' in filtered_df.columns else 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Demand Forecast", int(kpi1))
    col2.metric("Total Stock Available", int(kpi2))
    col3.metric("Total Sales", int(kpi3))
    col4.metric("Stockout Days", int(kpi4))

    st.markdown("**Tip:** Adjust the filters on the left to update these KPIs for specific segments.")

# ----------- TAB 2: DEMAND & INVENTORY TRENDS -----------
with tab2:
    st.header("📈 Demand vs Inventory Trends")
    st.markdown("Visualize trends for demand forecast, stock, and sales to spot gaps and patterns over time.")

    if 'Date' in filtered_df.columns:
        st.markdown("**Line Chart:** Daily Demand Forecast, Stock, and Sales")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Demand Forecast'], name='Demand Forecast', mode='lines+markers'))
        if 'Stock' in filtered_df.columns:
            fig1.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Stock'], name='Stock', mode='lines+markers'))
        if 'Sales' in filtered_df.columns:
            fig1.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Sales'], name='Sales', mode='lines+markers'))
        st.plotly_chart(fig1, use_container_width=True)

    # Rolling average demand
    st.markdown("**Bar Chart:** Top 10 Days by Demand Forecast")
    if 'Date' in filtered_df.columns:
        top_demand = filtered_df.groupby('Date')['Demand Forecast'].sum().nlargest(10)
        fig2 = px.bar(top_demand, y=top_demand.values, x=top_demand.index, labels={"x": "Date", "y": "Total Demand"})
        st.plotly_chart(fig2, use_container_width=True)

# ----------- TAB 3: PRODUCT / CATEGORY ANALYSIS -----------
with tab3:
    st.header("🛒 Product & Category Insights")
    st.markdown("Identify which products and categories drive most demand and inventory movement.")

    if 'Product' in filtered_df.columns and 'Demand Forecast' in filtered_df.columns:
        st.markdown("**Bar Chart:** Top 10 Products by Forecasted Demand")
        prod_demand = filtered_df.groupby('Product')['Demand Forecast'].sum().nlargest(10)
        fig3 = px.bar(prod_demand, y=prod_demand.values, x=prod_demand.index, labels={"x": "Product", "y": "Total Demand"})
        st.plotly_chart(fig3, use_container_width=True)

    if 'Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
        st.markdown("**Pie Chart:** Sales Share by Category")
        cat_sales = filtered_df.groupby('Category')['Sales'].sum()
        fig4 = px.pie(cat_sales, values=cat_sales.values, names=cat_sales.index)
        st.plotly_chart(fig4, use_container_width=True)

# ----------- TAB 4: STORE ANALYSIS -----------
with tab4:
    st.header("🏬 Store-Level Analysis")
    st.markdown("Evaluate demand and inventory dynamics across stores to spot overstocked or understocked locations.")

    if 'Store' in filtered_df.columns:
        st.markdown("**Bar Chart:** Demand Forecast by Store")
        store_demand = filtered_df.groupby('Store')['Demand Forecast'].sum().sort_values(ascending=False)
        fig5 = px.bar(store_demand, y=store_demand.values, x=store_demand.index, labels={"x": "Store", "y": "Total Demand"})
        st.plotly_chart(fig5, use_container_width=True)

        if 'Stock' in filtered_df.columns:
            st.markdown("**Scatter Plot:** Stock vs Demand by Store")
            store_stock = filtered_df.groupby('Store').agg({'Demand Forecast':'sum','Stock':'sum'})
            fig6 = px.scatter(store_stock, x='Demand Forecast', y='Stock', text=store_stock.index)
            st.plotly_chart(fig6, use_container_width=True)

# ----------- TAB 5: ADVANCED / CUSTOM ANALYSIS -----------
with tab5:
    st.header("🔬 Advanced and Custom Insights")
    st.markdown("Drill deeper into inventory management with ABC analysis, heatmaps, pivot tables, or custom queries.")

    # Example: ABC Analysis (80/20 rule for Products by Demand)
    st.markdown("**ABC Analysis:** Products by Cumulative Demand")
    if 'Product' in filtered_df.columns and 'Demand Forecast' in filtered_df.columns:
        abc = filtered_df.groupby('Product')['Demand Forecast'].sum().sort_values(ascending=False)
        total = abc.sum()
        cumsum = abc.cumsum() / total
        fig7 = px.bar(x=abc.index, y=abc.values, labels={'x':'Product','y':'Total Demand'})
        st.plotly_chart(fig7, use_container_width=True)
        st.dataframe(pd.DataFrame({'Product': abc.index, 'Demand': abc.values, 'Cumulative%': cumsum.values}).head(20))

    # Custom Table: Full filtered data
    st.markdown("**Data Table:** Filtered Dataset")
    st.dataframe(filtered_df.head(100))

# ----------- EXTRAS: EXPORT DATA, MORE CHARTS, ETC -----------
# (Add more as needed to reach 20+ visuals: heatmaps, histograms, boxplots, timeseries decomposition, outlier detection, low-stock alerts, etc.)

