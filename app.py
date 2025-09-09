import dash
from dash import Dash, html, dcc, Output, Input, callback, dash_table
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
from datetime import datetime as dt
from datetime import timedelta as td
import pytz   # if Python 3.9+, you can use zoneinfo instead
import socket
import logging
import os
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s"
)

logger = logging.getLogger(__name__)

# set url prefix
url_prefix = "/app/des_export/"

app = dash.Dash(__name__, 
                url_base_pathname=url_prefix,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True # this is used for multipage apps where callbacks are registered dynamically for pages that might be conditionally loaded
                ) 

# choose your app’s default timezone
tz = pytz.timezone("America/Toronto")

# Load variables from .env into environment
load_dotenv()

# set up the sql connection string
DB_HOST = os.getenv('QP_SERVER')
DB_USER = os.getenv('QP_VIEWER_USER')
DB_PASS = os.getenv('QP_VIEWER_PASSWORD')

# logger.info('Credentials loaded locally')
logger.debug(f"{'QP_SERVER'}: {DB_HOST}")
logger.debug(f"{'QP_VIEWER_USER'}: {DB_USER}")


# create the dcp engine
dcp_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(DB_USER,DB_PASS,DB_HOST,'dcp')
dcp_engine=create_engine(dcp_engine_string,pool_pre_ping=True)

# create the borden engine
borden_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(DB_USER,DB_PASS,DB_HOST,'borden')
borden_engine=create_engine(borden_engine_string,pool_pre_ping=True)

# set a function to retrieve sql queries
def sql_query_retriever(name: str) -> str:
    path = f"sql_queries/{name}.sql"
    with open(path, "r", encoding="utf-8") as f:
        query = f.read().strip()
    return query

logger.debug(text(sql_query_retriever('datasets_df')))

# retrieve some dcp tables into dataframes
with dcp_engine.connect() as dcp_conn:
    projects_df = pd.read_sql_query(text(sql_query_retriever('projects_df')),dcp_conn)
    pis_df = pd.read_sql_query(text(sql_query_retriever('pis_df')),dcp_conn)

with borden_engine.connect() as borden_conn:
    borden_datasets_df = pd.read_sql_query(text(sql_query_retriever('datasets_df')),borden_conn)


# Convert df['site'] into dropdown options
dropdown_options = [{"label": s, "value": s} for s in projects_df["Project"].unique()]

logger.debug(dropdown_options)

app.layout = html.Div(
    
    style={ "width": "95%",           # Responsive width
            "maxWidth": "900px",      # Maximum width for large screens
            "minWidth": "320px",      # Optional: minimum width for small screens
            "margin": "40px auto",
            "fontFamily": "sans-serif"},
    children=[
        html.Div(
            style={
                "backgroundImage": "url('/assets/IMG_0180.jpg')",  # Replace with your image URL or local asset
                "backgroundSize": "cover",
                "backgroundPosition": "center",
                "padding": "40px 0",
                "borderRadius": "12px",
                "marginBottom": "24px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
            },
            children=[
                html.H1(
                    "AQRP DES OUTPUT TOOL",
                    style={
                        "textAlign": "center",
                        "color": "white",
                        "textShadow": "2px 2px 8px #333",
                        "margin": 0,
                    },
                )
            ],
        ),
        html.H5("PICK A PROJECT"),#, date & time (timezone aware)"),

        # Dropdown menu
        dcc.Dropdown(
            id="project-dropdown",
            options=dropdown_options,
            value=projects_df["Project"].iloc[0],  # default
            clearable=False,
            style={"marginBottom": "12px"}
        ),

        # Date picker
        dcc.DatePickerSingle(
            id="date",
            display_format="YYYY-MM-DD",
            placeholder="Select date",
            clearable=True,
        ),

        # Time input
        dcc.Input(
            id="time",
            type="time",
            value="12:00",  # default time
            style={"marginLeft": "12px"}
        ),

        html.Hr(),
        html.Div(id="picked-output", style={"fontSize": 18}),
    ],
)

@callback(
    Output("picked-output", "children"),
    Input("project-dropdown", "value"),
    Input("date", "date"),
    Input("time", "value"),
)
def update_output(site, date, time_value):
    if not date or not time_value:
        return "Please pick a site, date, and time."

    # Combine into datetime (timezone aware example: UTC)
    dt_str = f"{date} {time_value}"
    timestamp = dt.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)

    return f"Site: {site} | Selected datetime (UTC): {timestamp}"
    
if __name__ == "__main__":
    app.run(port=8080, debug=True)
    # sql_engine.dispose()



# def show_datetime(date_str, time_str):
#     if not date_str and not time_str:
#         return "Nothing selected yet."

#     try:
#         # parse into a Python datetime
#         if date_str and time_str:
#             naive = dt.fromisoformat(f"{date_str} {time_str}")
#         elif date_str:
#             naive = dt.fromisoformat(date_str)  # midnight default
#         else:
#             # if only time is given, use today
#             today = dt.now(tz)
#             naive = dt.fromisoformat(today.strftime("%Y-%m-%d") + " " + time_str)

#         # localize to the chosen timezone
#         aware = tz.localize(naive)

#         # show both local and UTC
#         return f"You picked: {aware.isoformat()}  (UTC: {aware.astimezone(pytz.UTC).isoformat()})"

#     except Exception as e:
#         return f"Error parsing selection: {e}"