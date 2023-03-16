import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import plotly.express as px

# To import data from BigQuery
credentials = service_account.Credentials.from_service_account_file('config.json')

# Initialize query
sql_query = """
select * from dbt_prod.revenue
"""

# Import data from big query
df = pd.read_gbq(sql_query, project_id=credentials.project_id, credentials=credentials)

# Get the name of the restaurants
restaurants = df['restaurant'].unique()
# Replacing real restaurant names by fictive oens
df.loc[df['restaurant'] == restaurants[0], 'restaurant'] = 'Grande Prairie'
df.loc[df['restaurant'] == restaurants[1], 'restaurant'] = 'Fils et Mignon'
df.loc[df['restaurant'] == restaurants[2], 'restaurant'] = 'R Cuisine'

# Define our new restaurant dropdown values
restaurants = df['restaurant'].unique().tolist()

# Give columns a proper name
df = df.rename(columns={
    'turnover': 'Turnover',
    'nb_orders': 'Number of orders',
    'nb_menus': 'Number of menus',
    'nb_dishes': 'Number of dishes'
})
# Define metric drop down values
metrics = [i for i in df.columns if i not in ["day", "restaurant"]]


# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1 , maximum-scale=1.9, minimum-scale=.5'}])

######################################################
####################### Layout #######################
######################################################

app.layout = dbc.Container([

    ########### Header ###########
    html.H1("Zelty API Retrieval", style={"font-weight": "bold"}),

    ########### Block ###########
    html.Div([

        html.H3("Revenue overview"),

        dbc.Row([
            # Restaurant dropdown
            dbc.Col([
                html.H6("Restaurant"),
                dcc.Dropdown(
                    sorted(restaurants + ["All"]), # To display All restaurants
                    restaurants[0],
                    id="restaurant-dropdown"
                    )
                ]),
            # Metric dropdown
            dbc.Col([
                html.H6("Metric"),
                dcc.Dropdown(
                    metrics,
                    metrics[0],
                    id="metric-dropdown"
                    )
                ]),
        ], className="center-right"),

        # Graph
        dbc.Card([
            dcc.Graph(
                id="my-graph",
                figure={},       
            )
        ], className="card")
    ], className="centered")
])


######################################################
###################### Callbacks #####################
######################################################

@app.callback(
    Output("my-graph", "figure"),
    [Input("restaurant-dropdown", "value"),
    Input("metric-dropdown", "value")]

)

def update_graph(restaurant, metric):

    # Filter by restaurant
    if restaurant != "All":
        dff = df[df["restaurant"] == restaurant]

    # No restaurant filter
    else:
        dff = df.groupby('day')[metric].sum().reset_index()

    # Change color depending of the restaurant
    if restaurant == restaurants[0]:
        color = 'lightblue'
    elif restaurant == restaurants[1]:
        color = '#da6565' # light red
    elif restaurant == restaurants[2]:
        color = 'lightyellow'
    else:
        color = 'lightgrey'
    
    # Change titles
    # Title
    title = f"<b>{restaurant}</b>: {metric}"
    title = title +  " sold" if metric != "Turnover" else title # Add word `sold`to titles with count metrics`
    # Y axis
    yaxis_title = "Amount" if metric == "Turnover" else "Count"

    fig = px.area(
        dff,
        x="day",
        y=metric,
        color_discrete_sequence=[color],
        hover_data={
        "day": False # Does not display day value on hover
        }
    )

    fig.update_layout(
        # Modify chart layout
        template="plotly_dark",
        paper_bgcolor='rgba(0, 0, 0, 0)', # Transparent background

        # Title
        title=title,
        xaxis_title="Date range",
        yaxis_title=yaxis_title,

        # Format hovermode
        hovermode="x",
        hoverlabel=dict(
            bgcolor="black",
            font_size=12,
            font_family="Rockwell"
        ),
        # Date range
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    return fig


######################################################
####################### Run app ######################
######################################################

if __name__ == '__main__':
    app.run_server(debug=True)
