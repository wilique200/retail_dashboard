import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import zipfile

# -------------------------------
# Load and clean dataset
# -------------------------------
with zipfile.ZipFile("cleaned_retail_data.zip", "r") as z:
    z.extractall()  # extracts cleaned_retail_data.csv into current directory

df = pd.read_csv("cleaned_retail_data.csv")

# Data cleaning
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
df['Totalsale'] = pd.to_numeric(df['Totalsale'], errors='coerce')
df = df.dropna(subset=['CustomerID'])
df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0) & (df['Totalsale'] > 0)]

# -------------------------------
# KPI calculations
# -------------------------------
total_revenue = df['Totalsale'].sum()
avg_order_value = df.groupby('InvoiceNo')['Totalsale'].sum().mean()
num_customers = df['CustomerID'].nunique()

# -------------------------------
# Initialize Dash app
# -------------------------------
app = dash.Dash(__name__)
app.title = "Retail Sales Dashboard"

# -------------------------------
# Layout
# -------------------------------
app.layout = html.Div([
    html.H1("Retail Sales Dashboard", style={'textAlign': 'center', 'color': '#2E86C1'}),

    # KPI cards
    html.Div([
        html.Div([
            html.H3("Total Revenue", style={'color': '#1B4F72'}),
            html.P(f"${total_revenue:,.2f}", style={'fontSize': '24px', 'fontWeight': 'bold'})
        ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),

        html.Div([
            html.H3("Average Order Value", style={'color': '#1B4F72'}),
            html.P(f"${avg_order_value:,.2f}", style={'fontSize': '24px', 'fontWeight': 'bold'})
        ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),

        html.Div([
            html.H3("Number of Customers", style={'color': '#1B4F72'}),
            html.P(f"{num_customers:,}", style={'fontSize': '24px', 'fontWeight': 'bold'})
        ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'center'}),
    ], style={'marginBottom': '40px'}),

    # Filters
    html.Div([
        html.Label("Select Country"),
        dcc.Dropdown(
            options=[{'label': c, 'value': c} for c in sorted(df['Country'].unique())],
            value='United Kingdom',
            id='country-filter'
        ),
        html.Label("Select Date Range"),
        dcc.DatePickerRange(
            id='date-filter',
            start_date=df['InvoiceDate'].min(),
            end_date=df['InvoiceDate'].max()
        )
    ], style={'width': '50%', 'margin': 'auto'}),

    # Charts
    dcc.Graph(id='monthly-sales'),
    dcc.Graph(id='top-products'),
])

# -------------------------------
# Callbacks
# -------------------------------
@app.callback(
    [Output('monthly-sales', 'figure'),
     Output('top-products', 'figure')],
    [Input('country-filter', 'value'),
     Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date')]
)
def update_dashboard(selected_country, start_date, end_date):
    filtered = df[(df['Country'] == selected_country) &
                  (df['InvoiceDate'] >= start_date) &
                  (df['InvoiceDate'] <= end_date)]

    monthly_sales = filtered.groupby(filtered['InvoiceDate'].dt.to_period('M'))['Totalsale'].sum().reset_index()
    monthly_sales['InvoiceDate'] = monthly_sales['InvoiceDate'].dt.to_timestamp()

    top_products = filtered.groupby('Description')['Totalsale'].sum().sort_values(ascending=False).head(10)

    fig_monthly = px.line(monthly_sales, x="InvoiceDate", y="Totalsale",
                          title="Monthly Sales Trend", markers=True,
                          color_discrete_sequence=['#2E86C1'])
    fig_top = px.bar(top_products, x=top_products.index, y=top_products.values,
                     title="Top 10 Products by Revenue",
                     color=top_products.values, color_continuous_scale='Blues')

    return fig_monthly, fig_top

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)