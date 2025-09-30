import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="TTD Stock Variance Dashboard", layout="wide")

# --- Load Data Function ---
@st.cache_data
def load_data():
    df = pd.read_excel("TTD Stock Comparison On 29-Sep-2025 2.Xlsx")  # Replace with your Excel file path
    df.columns = df.columns.str.strip()

    # Ensure Diff Stock column
    if 'Diff Stock' not in df.columns:
        df['Diff Stock'] = df['Phys Stock'] - df['Book Stock']

    cost_col = "Cost Price"  # Adjust if your Excel has a different name
    df['Book Value'] = df['Book Stock'] * df[cost_col]
    df['Phys Value'] = df['Phys Stock'] * df[cost_col]
    df['Diff Value'] = df['Diff Stock'] * df[cost_col]

    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
categories = df['Category'].unique().tolist()
selected_category = st.sidebar.selectbox("Select Category", ["All"] + categories)

# --- Filtered Data ---
filtered_df = df.copy()
if selected_category != "All":
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# --- Summary Metrics ---
total_book_stock = filtered_df['Book Stock'].sum()
total_phys_stock = filtered_df['Phys Stock'].sum()
total_diff_stock = filtered_df['Diff Stock'].sum()

total_book_value = filtered_df['Book Value'].sum()
total_phys_value = filtered_df['Phys Value'].sum()
total_diff_value = filtered_df['Diff Value'].sum()

stock_variance_pct = (
    (total_diff_stock / total_book_stock) * 100 if total_book_stock != 0 else 0
)

# --- Dashboard Title ---
st.title("📊 TTD Stock Variance Dashboard")

# --- Summary Section ---
st.markdown("### 📊 Stock Summary")
col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    st.markdown(
        f"<h5>System Stock</h5>"
        f"<p style='font-size:28px; font-weight:bold;'>{total_book_stock:,.0f}</p>"
        f"<p style='font-size:14px; color:gray;'>AED {total_book_value:,.0f}</p>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"<h5>Physical Stock</h5>"
        f"<p style='font-size:28px; font-weight:bold;'>{total_phys_stock:,.0f}</p>"
        f"<p style='font-size:14px; color:gray;'>AED {total_phys_value:,.0f}</p>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"<h5>Stock Difference</h5>"
        f"<p style='font-size:28px; font-weight:bold;'>{total_diff_stock:,.0f}</p>"
        f"<p style='font-size:14px; color:gray;'>AED {total_diff_value:,.0f}</p>",
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"<h5>Stock Variance %</h5>"
        f"<p style='font-size:28px; font-weight:bold;'>{stock_variance_pct:.2f} %</p>",
        unsafe_allow_html=True
    )

st.markdown("---")  # Space after summary

# --- Priority: Shortages First, then Excess ---
shortage_items = filtered_df[filtered_df['Diff Stock'] > 0].sort_values('Diff Stock', ascending=False)
excess_items = filtered_df[filtered_df['Diff Stock'] < 0].sort_values('Diff Stock')  # Negative values
priority_items = pd.concat([shortage_items, excess_items])

# --- Top 30 Priority Items ---
top_30_priority = priority_items.head(30)

st.subheader("Top 30 Items: Priority by Stock Difference")
fig_priority = go.Figure()

# Color: red for shortage, green for excess
colors = ['red' if x > 0 else 'green' for x in top_30_priority['Diff Stock']]

fig_priority.add_trace(go.Bar(
    y=top_30_priority['Item Name'],
    x=top_30_priority['Diff Stock'],
    name='Stock Difference (Qty)',
    orientation='h',
    marker_color=colors,
    hovertemplate=(
        "<b>%{y}</b><br>" +
        "Category: %{customdata[0]}<br>" +
        "Item No: %{customdata[1]}<br>" +
        "Barcode: %{customdata[2]}<br>" +
        "Book Stock: %{customdata[3]}<br>" +
        "Phys Stock: %{customdata[4]}<br>" +
        "Stock Diff: %{x}<br>" +
        "Stock Diff Value: AED %{customdata[5]:,.0f}<extra></extra>"
    ),
    customdata=top_30_priority[['Category','Item No','Barcode','Book Stock','Phys Stock','Diff Value']]
))

fig_priority.add_trace(go.Bar(
    y=top_30_priority['Item Name'],
    x=top_30_priority['Diff Value'],
    name='Stock Difference Value (AED)',
    orientation='h',
    marker_color='orange',
    hovertemplate=(
        "<b>%{y}</b><br>" +
        "Category: %{customdata[0]}<br>" +
        "Item No: %{customdata[1]}<br>" +
        "Barcode: %{customdata[2]}<br>" +
        "Book Stock: %{customdata[3]}<br>" +
        "Phys Stock: %{customdata[4]}<br>" +
        "Stock Diff: %{customdata[5]}<br>" +
        "Stock Diff Value: AED %{x:,.0f}<extra></extra>"
    ),
    customdata=top_30_priority[['Category','Item No','Barcode','Book Stock','Phys Stock','Diff Stock']]
))

fig_priority.update_layout(
    barmode='group', 
    yaxis=dict(autorange='reversed'), 
    xaxis_title="Quantity / Value",
    height=800, 
    legend_title="Metrics", 
    margin=dict(t=20, b=20)
)
st.plotly_chart(fig_priority, use_container_width=True)

# --- Top 30 Table ---
st.subheader("📄 Top 30 Items Details (Stock Difference Priority)")
key_columns = ['Category', 'Item Name', 'Item No', 'Barcode', 'Book Stock', 'Phys Stock', 'Diff Stock', 'Book Value', 'Phys Value', 'Diff Value']
available_columns = [col for col in key_columns if col in top_30_priority.columns]
st.dataframe(top_30_priority[available_columns])

# --- Remaining Items ---
st.subheader("📄 Remaining Items")
remaining_df = filtered_df.drop(top_30_priority.index)
st.dataframe(remaining_df[available_columns].sort_values(['Category','Diff Stock'], ascending=[True, False]))
