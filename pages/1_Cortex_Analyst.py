"""
Cortex Analyst App
====================
This app allows users to interact with their data using natural language.
"""
import json  # To handle JSON data
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import _snowflake  # For interacting with Snowflake-specific APIs
import pandas as pd
import streamlit as st  # Streamlit library for building the web app
import altair as alt  # For creating interactive charts
from snowflake.snowpark.context import (
    get_active_session,
)  # To interact with Snowflake sessions
from snowflake.snowpark.exceptions import SnowparkSQLException
import sys
import os

# Geospatial visualization imports
try:
    import pydeck as pdk
    import numpy as np
    print("Successfully imported pydeck and numpy for geospatial visualization")
except ImportError as e:
    print(f"Warning: Failed to import geospatial libraries: {str(e)}")
    # These dependencies may not be available
    pass

# Add path for utils module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.chart_utils import (
    create_chart1, create_chart2, create_chart3, create_chart4,
    create_chart5, create_chart6, create_chart7, create_chart8, create_chart9, create_chart10,
    create_chart11  # Add new chart type for geospatial visualization
)

# Set page config
st.set_page_config(
    page_title="Cortex Analyst",
    page_icon="❄️",
    layout="wide",
)

# List of available semantic model paths in the format: <DATABASE>.<SCHEMA>.<STAGE>/<FILE-NAME>
# Each path points to a YAML file defining a semantic model
AVAILABLE_SEMANTIC_MODELS_PATHS = [
    "SYNTHEA.SYNTHEA.SYNTHEA/synthea_joins_03.yaml",
    "QUANTIUM_DEMO.TEXT2SQL.TEXT2SQL/fakesalesmap.yaml",
    "TELCO_NETWORK_OPTIMIZATION_PROD.RAW.DATA/telco_network_opt.yaml"
]
API_ENDPOINT = "/api/v2/cortex/analyst/message"
FEEDBACK_API_ENDPOINT = "/api/v2/cortex/analyst/feedback"
API_TIMEOUT = 50000  # in milliseconds

# Initialize a Snowpark session for executing queries
session = get_active_session()


def main():
    # Initialize session state
    if "messages" not in st.session_state:
        reset_session_state()
    show_header_and_sidebar()
    display_conversation()
    handle_user_inputs()
    handle_error_notifications()
    # display_warnings()  # Commented out to hide warnings from users


def reset_session_state():
    """Reset important session state elements."""
    st.session_state.messages = []  # List to store conversation messages
    st.session_state.active_suggestion = None  # Currently selected suggestion
    st.session_state.warnings = []  # List to store warnings
    st.session_state.form_submitted = (
        {}
    )  # Dictionary to store feedback submission for each request
    st.session_state.sql_execution_mode = "Run"  # Default SQL execution mode


def show_header_and_sidebar():
    """Display the header and sidebar of the app."""
    # Set the title and introductory text of the app
    st.title("Cortex Analyst")
    st.markdown(
        "Welcome to Cortex Analyst! Type your questions below to interact with your data. "
    )

    # Sidebar with a reset button
    with st.sidebar:
        st.selectbox(
            "Selected semantic model:",
            AVAILABLE_SEMANTIC_MODELS_PATHS,
            format_func=lambda s: s.split("/")[-1],
            key="selected_semantic_model_path",
            on_change=reset_session_state,
        )
        st.divider()
        # Center this button
        _, btn_container, _ = st.columns([2, 6, 2])
        if btn_container.button("Clear Chat History", use_container_width=True):
            reset_session_state()
            
        # Add SQL execution mode toggle
        st.radio(
            "SQL Execution Mode:",
            options=["Run", "View"],
            index=0,
            key="sql_execution_mode",
            horizontal=True,
        )


def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # Handle chat input
    user_input = st.chat_input("What is your question?")
    if user_input:
        process_user_input(user_input)
    # Handle suggested question click
    elif st.session_state.active_suggestion is not None:
        suggestion = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(suggestion)


def handle_error_notifications():
    if st.session_state.get("fire_API_error_notify"):
        st.toast("An API error has occured!", icon="🚨")
        st.session_state["fire_API_error_notify"] = False


def process_user_input(prompt: str):
    """
    Process user input and update the conversation history.

    Args:
        prompt (str): The user's input.
    """
    # Clear previous warnings at the start of a new request
    st.session_state.warnings = []

    # Create a new message, append to history and display imidiately
    new_user_message = {
        "role": "user",
        "content": [{"type": "text", "text": prompt}],
    }
    st.session_state.messages.append(new_user_message)
    with st.chat_message("user"):
        user_msg_index = len(st.session_state.messages) - 1
        display_message(new_user_message["content"], user_msg_index)

    # Show progress indicator inside analyst chat message while waiting for response
    with st.chat_message("analyst"):
        with st.spinner("Waiting for Analyst's response..."):
            time.sleep(1)
            response, error_msg = get_analyst_response(st.session_state.messages)
            if error_msg is None:
                analyst_message = {
                    "role": "analyst",
                    "content": response["message"]["content"],
                    "request_id": response["request_id"],
                }
            else:
                analyst_message = {
                    "role": "analyst",
                    "content": [{"type": "text", "text": error_msg}],
                    "request_id": response["request_id"],
                }
                st.session_state["fire_API_error_notify"] = True

            # if "warnings" in response:
            #     st.session_state.warnings = response["warnings"]

            st.session_state.messages.append(analyst_message)
            st.rerun()


def display_warnings():
    """
    Display warnings to the user.
    """
    # warnings = st.session_state.warnings
    # for warning in warnings:
    #     st.warning(warning["message"], icon="⚠️")


def get_analyst_response(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """
    Send chat history to the Cortex Analyst API and return the response.

    Args:
        messages (List[Dict]): The conversation history.

    Returns:
        Optional[Dict]: The response from the Cortex Analyst API.
    """
    # Prepare the request body with the user's prompt
    request_body = {
        "messages": messages,
        "semantic_model_file": f"@{st.session_state.selected_semantic_model_path}",
    }

    # Send a POST request to the Cortex Analyst API endpoint
    # Adjusted to use positional arguments as per the API's requirement
    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )

    # Content is a string with serialized JSON object
    parsed_content = json.loads(resp["content"])

    # Check if the response is successful
    if resp["status"] < 400:
        # Return the content of the response as a JSON object
        return parsed_content, None
    else:
        # Craft readable error message
        error_msg = f"""
🚨 An Analyst API error has occurred 🚨

* response code: `{resp['status']}`
* request-id: `{parsed_content['request_id']}`
* error code: `{parsed_content['error_code']}`

Message:
```
{parsed_content['message']}
```
        """
        return parsed_content, error_msg


def display_conversation():
    """
    Display the conversation history between the user and the assistant.
    """
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            if role == "analyst":
                display_message(content, idx, message["request_id"])
            else:
                display_message(content, idx)


def display_message(
    content: List[Dict[str, Union[str, Dict]]],
    message_index: int,
    request_id: Union[str, None] = None,
):
    """
    Display a single message content.

    Args:
        content (List[Dict[str, str]]): The message content.
        message_index (int): The index of the message.
    """
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            # Display suggestions as buttons
            for suggestion_index, suggestion in enumerate(item["suggestions"]):
                if st.button(
                    suggestion, key=f"suggestion_{message_index}_{suggestion_index}"
                ):
                    st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            # Display the SQL query and results
            display_sql_query(
                item["statement"], message_index, item["confidence"], request_id
            )
        else:
            # Handle other content types if necessary
            pass


@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute the SQL query and convert the results to a pandas DataFrame.

    Args:
        query (str): The SQL query.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: The query results and the error message.
    """
    global session
    try:
        df = session.sql(query).to_pandas()
        return df, None
    except SnowparkSQLException as e:
        return None, str(e)


def display_sql_confidence(confidence: dict):
    if confidence is None:
        return
    verified_query_used = confidence["verified_query_used"]
    with st.popover(
        "Verified Query Used",
        help="The verified query from [Verified Query Repository](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/verified-query-repository), used to generate the SQL",
    ):
        with st.container():
            if verified_query_used is None:
                st.text(
                    "There is no query from the Verified Query Repository used to generate this SQL answer"
                )
                return
            st.text(f"Name: {verified_query_used['name']}")
            st.text(f"Question: {verified_query_used['question']}")
            st.text(f"Verified by: {verified_query_used['verified_by']}")
            st.text(
                f"Verified at: {datetime.fromtimestamp(verified_query_used['verified_at'])}"
            )
            st.text("SQL query:")
            st.code(verified_query_used["sql"], language="sql", wrap_lines=True)


def display_sql_query(
    sql: str, message_index: int, confidence: dict, request_id: Union[str, None] = None
):
    """
    Executes the SQL query and displays the results in form of data frame and charts.

    Args:
        sql (str): The SQL query.
        message_index (int): The index of the message.
        confidence (dict): The confidence information of SQL query generation
        request_id (str): Request id from user request
    """

    # Display the SQL query
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")
        display_sql_confidence(confidence)

    # Check if we should execute the SQL or just display it
    if st.session_state.sql_execution_mode == "Run":
        # Display the results of the SQL query
        with st.expander("Results", expanded=True):
            with st.spinner("Running SQL..."):
                df, err_msg = get_query_exec_result(sql)
                if df is None:
                    st.error(f"Could not execute generated SQL query. Error: {err_msg}")
                elif df.empty:
                    st.write("Query returned no data")
                else:
                    st.dataframe(df, use_container_width=True)
                    display_chart(df, message_index)
    else:
        # Display a message indicating SQL execution is disabled
        with st.expander("Results", expanded=True):
            st.info("SQL execution is disabled. Switch to 'Run' mode to execute queries.")
            
    if request_id:
        display_feedback_section(request_id)


def display_chart(df: pd.DataFrame, message_index: int) -> None:
    """
    Display the charts using Altair charts based on data structure.

    Args:
        df (pd.DataFrame): The query results.
        message_index (int): The index of the message.
    """
    # Add debug logging
    print(f"Input DataFrame type: {type(df)}")
    print(f"Input DataFrame shape: {df.shape}")
    print(f"Input DataFrame columns: {df.columns.tolist()}")
    print(f"Input DataFrame dtypes:\n{df.dtypes}")
    
    # Ensure we're working with a pandas DataFrame
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
            print("Successfully converted input to DataFrame")
        except Exception as e:
            print(f"Error converting to DataFrame: {str(e)}")
            st.error("Could not process data into proper format for visualization")
            return

    # Limit to the top 5000 rows for visualization
    df_display = df.head(5000)
    
    # Create an Altair chart based on DataFrame content using predefined rules
    try:
        # Identify column types
        numeric_cols = [col for col in df_display.columns if pd.api.types.is_numeric_dtype(df_display[col])]
        
        # Improved date detection - first look for datetime types, then try to detect string date columns
        date_cols = [col for col in df_display.columns if pd.api.types.is_datetime64_any_dtype(df_display[col])]
        
        # Check for month/date columns that might be in various formats
        if not date_cols:
            # List all columns that could potentially be date columns
            potential_date_cols = []
            
            # First check columns with date-related names
            date_related_terms = ['date', 'month', 'year', 'day', 'time', 'dt', 'period']
            for col in df_display.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in date_related_terms):
                    potential_date_cols.append(col)
            
            # Then check other string and object columns
            other_cols = [col for col in df_display.columns if col not in potential_date_cols 
                         and (pd.api.types.is_string_dtype(df_display[col]) or pd.api.types.is_object_dtype(df_display[col]))]
            potential_date_cols.extend(other_cols)
            
            # Try to convert potential date columns
            for col in potential_date_cols:
                try:
                    # Try to convert to datetime
                    temp_series = pd.to_datetime(df_display[col], errors='coerce')
                    # If at least 90% of non-null values converted successfully, consider it a date column
                    non_null_count = df_display[col].count()
                    if non_null_count > 0:
                        success_rate = temp_series.count() / non_null_count
                        if success_rate >= 0.9:
                            df_display[col] = temp_series
                            date_cols.append(col)
                            break  # Stop after finding one good date column
                except Exception as e:
                    continue
        
        # Recalculate text columns after date detection
        text_cols = [col for col in df_display.columns if col not in numeric_cols and col not in date_cols and 
                    (pd.api.types.is_string_dtype(df_display[col]) or pd.api.types.is_object_dtype(df_display[col]))]

        # Debug information for column detection
        print(f"DataFrame columns: {df_display.columns.tolist()}")
        print(f"DataFrame dtypes: {df_display.dtypes}")
        print(f"Detected numeric columns: {numeric_cols}")
        print(f"Detected date columns: {date_cols}")
        print(f"Detected text columns: {text_cols}")
        print(f"Column type detection summary: date_cols={len(date_cols)}, text_cols={len(text_cols)}, numeric_cols={len(numeric_cols)}")
        
        # Flag to track if we've created a chart successfully
        chart_created = False
        alt_chart = None
        
        # STEP 1: First check for geospatial data (latitude and longitude columns)
        # Check using common naming patterns in lowercase
        lat_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lat', 'latitude'])]
        lon_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lon', 'long', 'longitude'])]
        
        # If not found, try checking for uppercase patterns
        if not (lat_cols and lon_cols):
            # Look for any column names containing LAT and LON in uppercase
            lat_cols_upper = [col for col in df_display.columns if "LAT" in col.upper()]
            lon_cols_upper = [col for col in df_display.columns if "LON" in col.upper()]
            
            # If potential columns found, verify they contain actual coordinate values
            if lat_cols_upper and lon_cols_upper:
                print(f"Found potential lat/lon columns: {lat_cols_upper} and {lon_cols_upper}")
                # Convert to numeric and check first few values
                valid_lat_cols = []
                valid_lon_cols = []
                
                for lat_col in lat_cols_upper:
                    try:
                        # Convert to numeric, coerce errors to NaN
                        temp_lat = pd.to_numeric(df_display[lat_col], errors='coerce')
                        # Drop NaN values for checking
                        temp_lat = temp_lat.dropna()
                        # Check if values are in latitude range (-90 to 90)
                        if not temp_lat.empty and temp_lat.min() >= -90 and temp_lat.max() <= 90:
                            valid_lat_cols.append(lat_col)
                            print(f"Validated {lat_col} as latitude: min={temp_lat.min()}, max={temp_lat.max()}")
                    except Exception as e:
                        print(f"Error validating {lat_col}: {str(e)}")
                
                for lon_col in lon_cols_upper:
                    try:
                        # Convert to numeric, coerce errors to NaN
                        temp_lon = pd.to_numeric(df_display[lon_col], errors='coerce')
                        # Drop NaN values for checking
                        temp_lon = temp_lon.dropna()
                        # Check if values are in longitude range (-180 to 180)
                        if not temp_lon.empty and temp_lon.min() >= -180 and temp_lon.max() <= 180:
                            valid_lon_cols.append(lon_col)
                            print(f"Validated {lon_col} as longitude: min={temp_lon.min()}, max={temp_lon.max()}")
                    except Exception as e:
                        print(f"Error validating {lon_col}: {str(e)}")
                
                # If valid columns found, use them
                if valid_lat_cols and valid_lon_cols:
                    lat_cols = valid_lat_cols
                    lon_cols = valid_lon_cols
        
        # Try to create a map visualization if we have both latitude and longitude columns
        if lat_cols and lon_cols:
            print(f"Detected geospatial data with lat column: {lat_cols[0]} and lon column: {lon_cols[0]}")
            # Find a suitable value column (can be customized later in Map Designer)
            value_col = None
            if len(numeric_cols) > 0:
                # Use the first numeric column that's not lat/lon
                for col in numeric_cols:
                    if col not in lat_cols and col not in lon_cols:
                        value_col = col
                        break
            
            chart_metadata = {
                'chart11_columns': {
                    'lat_col': lat_cols[0],
                    'lon_col': lon_cols[0],
                    'value_col': value_col
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            print(f"Creating map with chart_metadata: {chart_metadata}")
            alt_chart = create_chart11(df_display, chart_metadata['chart11_columns'])
            
            # Debug output to help identify what create_chart11 returned
            if alt_chart is None:
                print("create_chart11 returned None")
            else:
                print(f"create_chart11 returned object of type: {type(alt_chart)}")
                if isinstance(alt_chart, pdk.Deck) and hasattr(alt_chart, 'layers') and alt_chart.layers:
                    print("Valid map with layers detected")
                    chart_created = True
                else:
                    print("Invalid map object returned - no layers or not a pdk.Deck")
        
        # STEP 2: If geospatial visualization wasn't created or failed, try other chart types
        if not chart_created or alt_chart is None:
            print("Geospatial visualization not created or failed, trying other chart types")
            
            # Try all chart types based on their specific data structure requirements
            # Order: from most specific (more column requirements) to more general
            
            # Chart Type 8: Multiple text columns, multiple numeric columns - Multi-Dimension Bubble
            if not chart_created and len(text_cols) >= 2 and len(numeric_cols) >= 3:
                chart_metadata = {
                    'chart8_columns': {
                        'text_col1': text_cols[0],
                        'text_col2': text_cols[1],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1],
                        'num_col3': numeric_cols[2]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 8 with metadata: {chart_metadata}")
                alt_chart = create_chart8(df_display, chart_metadata['chart8_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 8")
                    chart_created = True
            
            # Chart Type 7: One text column, three numeric columns - Bubble Chart
            if not chart_created and len(text_cols) >= 1 and len(numeric_cols) >= 3:
                chart_metadata = {
                    'chart7_columns': {
                        'text_col': text_cols[0],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1],
                        'num_col3': numeric_cols[2]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 7 with metadata: {chart_metadata}")
                alt_chart = create_chart7(df_display, chart_metadata['chart7_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 7")
                    chart_created = True
            
            # Chart Type 6: Two text columns, two numeric columns - Multi-Dimension Scatter
            if not chart_created and len(text_cols) >= 2 and len(numeric_cols) >= 2:
                chart_metadata = {
                    'chart6_columns': {
                        'text_col1': text_cols[0],
                        'text_col2': text_cols[1],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 6 with metadata: {chart_metadata}")
                alt_chart = create_chart6(df_display, chart_metadata['chart6_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 6")
                    chart_created = True
            
            # Chart Type 4: Date column, multiple categorical columns, and numeric column - Stacked Bar with Selector
            if not chart_created and len(date_cols) == 1 and len(text_cols) >= 2 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart4_columns': {
                        'date_col': date_cols[0],
                        'text_cols': text_cols,
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 4 with metadata: {chart_metadata}")
                alt_chart = create_chart4(df_display, chart_metadata['chart4_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 4")
                    chart_created = True
            
            # Chart Type 2: Single date column, two numeric columns - Dual Axis Line Chart 
            if not chart_created and len(date_cols) == 1 and len(numeric_cols) >= 2:
                chart_metadata = {
                    'chart2_columns': {
                        'date_col': date_cols[0],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 2 with metadata: {chart_metadata}")
                alt_chart = create_chart2(df_display, chart_metadata['chart2_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 2")
                    chart_created = True
            
            # Chart Type 3: Date column, categorical column, and numeric column - Stacked Bar Chart
            if not chart_created and len(date_cols) == 1 and len(text_cols) >= 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart3_columns': {
                        'date_col': date_cols[0],
                        'text_col': text_cols[0],
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 3 with metadata: {chart_metadata}")
                alt_chart = create_chart3(df_display, chart_metadata['chart3_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 3")
                    chart_created = True
            
            # Chart Type 5: Two numeric columns and one text column - Scatter Plot
            if not chart_created and len(numeric_cols) >= 2 and len(text_cols) >= 1:
                chart_metadata = {
                    'chart5_columns': {
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1],
                        'text_col': text_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 5 with metadata: {chart_metadata}")
                alt_chart = create_chart5(df_display, chart_metadata['chart5_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 5")
                    chart_created = True
            
            # Chart Type 1: Single date column and single numeric column - Line Chart
            if not chart_created and len(date_cols) == 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart1_columns': {
                        'date_col': date_cols[0],
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 1 with metadata: {chart_metadata}")
                alt_chart = create_chart1(df_display, chart_metadata['chart1_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 1")
                    chart_created = True
            
            # Chart Type 9: Text columns and numeric columns - Bar Chart with Selectors
            if not chart_created and len(text_cols) >= 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart9_columns': {
                        'text_cols': text_cols,
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 9 with metadata: {chart_metadata}")
                alt_chart = create_chart9(df_display, chart_metadata['chart9_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 9")
                    chart_created = True
            
            # Chart Type 10: Single row with multiple numeric columns - KPI Tiles
            if not chart_created and len(df_display) == 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart10_columns': {
                        'numeric_cols': numeric_cols
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                print(f"Trying Chart Type 10 with metadata: {chart_metadata}")
                alt_chart = create_chart10(df_display, chart_metadata['chart10_columns'])
                if alt_chart:
                    print("Successfully created Chart Type 10")
                    chart_created = True
        
        # STEP 3: Display the appropriate chart based on what was created
        if alt_chart == "__KPI_RENDERED__":
            # KPI tiles were already rendered directly by create_chart10
            # Just show the "Open in Designer" button
            if st.button("Open in Designer", key=f"send_to_designer_{message_index}"):
                # Store data in session state to be accessed by Report Designer
                if "report_transfer" not in st.session_state:
                    st.session_state.report_transfer = {}
                
                # Extract the SQL statement from the message
                sql_statement = ""
                prompt = ""
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "sql":
                                sql_statement = item["statement"]
                    elif message["role"] == "user" and len(st.session_state.messages) - 2 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                prompt = item["text"]
                
                # Extract interpretation from the assistant's message if possible
                interpretation = None
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                text = item["text"]
                                # Look for the interpretation pattern
                                if "This is our interpretation of your question:" in text:
                                    interpretation_parts = text.split("This is our interpretation of your question:")
                                    if len(interpretation_parts) > 1:
                                        interpretation = interpretation_parts[1].strip()
                                        # Remove quotes if present
                                        if interpretation.startswith('"') and interpretation.endswith('"'):
                                            interpretation = interpretation[1:-1].strip()
                
                # Use interpretation if found, otherwise use original prompt
                description = interpretation if interpretation else prompt
                
                # Generate chart code based on chart type by using a wrapper function
                from utils.chart_utils import generate_chart_code_for_dataframe
                chart_code = generate_chart_code_for_dataframe(df_display)
                
                # Store data to be accessed by the Report Designer
                st.session_state.report_transfer = {
                    "df": df_display,
                    "sql": sql_statement,
                    "prompt": description,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "redirect": True,
                    "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                    "chart_code": chart_code
                }
                
                # Navigate to Report Designer
                st.switch_page("pages/2_Report_Designer.py")
        elif isinstance(alt_chart, pdk.Deck):
            # Handle pydeck map visualization
            print(f"Displaying pydeck.Deck map visualization")
            try:
                # Ensure we have a valid pydeck object
                if hasattr(alt_chart, 'layers') and alt_chart.layers:
                    print(f"Map has {len(alt_chart.layers)} layers")
                    # If we have layers, display the map
                    st.pydeck_chart(alt_chart)
                    print("Map successfully displayed with st.pydeck_chart")
                else:
                    # If no layers, show an error
                    print("Map has no layers to display")
                    st.error("Map visualization has no data layers to display")
            except Exception as e:
                print(f"Error displaying map with st.pydeck_chart: {str(e)}")
                import traceback
                print(traceback.format_exc())
                st.error(f"Error displaying map: {str(e)}")
            
            # Check if we have chart metadata for a geospatial chart
            is_map = False
            if hasattr(df_display, 'attrs') and 'chart_metadata' in df_display.attrs:
                chart_metadata = df_display.attrs['chart_metadata']
                is_map = 'chart11_columns' in chart_metadata
                print(f"Chart metadata indicates this is a map: {is_map}")
            
            # Add "Open in Map Designer" button for maps
            if is_map:
                button_text = "Open in Map Designer"
                target_page = "pages/4_Map_Designer.py"  # This will be created in Step 3
                print(f"Using 'Open in Map Designer' button pointing to {target_page}")
            else:
                button_text = "Open in Designer"
                target_page = "pages/2_Report_Designer.py"
                print(f"Using standard 'Open in Designer' button")
                
            if st.button(button_text, key=f"send_to_designer_{message_index}"):
                # Store data in session state to be accessed by the Designer
                session_state_key = "map_transfer" if is_map else "report_transfer"
                if session_state_key not in st.session_state:
                    st.session_state[session_state_key] = {}
                
                # Extract the SQL statement from the message
                sql_statement = ""
                prompt = ""
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "sql":
                                sql_statement = item["statement"]
                    elif message["role"] == "user" and len(st.session_state.messages) - 2 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                prompt = item["text"]
                
                # Extract interpretation from the assistant's message if possible
                interpretation = None
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                text = item["text"]
                                # Look for the interpretation pattern
                                if "This is our interpretation of your question:" in text:
                                    interpretation_parts = text.split("This is our interpretation of your question:")
                                    if len(interpretation_parts) > 1:
                                        interpretation = interpretation_parts[1].strip()
                                        # Remove quotes if present
                                        if interpretation.startswith('"') and interpretation.endswith('"'):
                                            interpretation = interpretation[1:-1].strip()
                
                # Use interpretation if found, otherwise use original prompt
                description = interpretation if interpretation else prompt
                
                # Generate chart code based on chart type by using a wrapper function
                from utils.chart_utils import generate_chart_code_for_dataframe
                chart_code = generate_chart_code_for_dataframe(df_display)
                
                # Store data to be accessed by the Designer
                st.session_state[session_state_key] = {
                    "df": df_display,
                    "sql": sql_statement,
                    "prompt": description,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "redirect": True,
                    "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                    "chart_code": chart_code  # Add the generated chart code
                }
                
                # Use Streamlit's native navigation to redirect to the appropriate designer
                st.switch_page(target_page)
        elif alt_chart:
            # Handle regular Altair charts
            st.altair_chart(alt_chart, use_container_width=True)
            
            # Add "Open in Designer" button
            if st.button("Open in Designer", key=f"send_to_designer_{message_index}"):
                # Store data in session state to be accessed by Report Designer
                if "report_transfer" not in st.session_state:
                    st.session_state.report_transfer = {}
                
                # Extract the SQL statement from the message
                sql_statement = ""
                prompt = ""
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "sql":
                                sql_statement = item["statement"]
                    elif message["role"] == "user" and len(st.session_state.messages) - 2 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                prompt = item["text"]
                
                # Extract interpretation from the assistant's message if possible
                interpretation = None
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                text = item["text"]
                                # Look for the interpretation pattern
                                if "This is our interpretation of your question:" in text:
                                    interpretation_parts = text.split("This is our interpretation of your question:")
                                    if len(interpretation_parts) > 1:
                                        interpretation = interpretation_parts[1].strip()
                                        # Remove quotes if present
                                        if interpretation.startswith('"') and interpretation.endswith('"'):
                                            interpretation = interpretation[1:-1].strip()
                
                # Use interpretation if found, otherwise use original prompt
                description = interpretation if interpretation else prompt
                
                # Generate chart code based on the dataframe
                from utils.chart_utils import generate_chart_code_for_dataframe
                chart_code = generate_chart_code_for_dataframe(df_display)
                
                # Store data to be accessed by the Report Designer
                st.session_state.report_transfer = {
                    "df": df_display,
                    "sql": sql_statement,
                    "prompt": description,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "redirect": True,
                    "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                    "chart_code": chart_code
                }
                
                # Navigate to Report Designer
                st.switch_page("pages/2_Report_Designer.py")
        else:
            # No valid chart could be created
            print("No appropriate chart found for this data")
            
            # Check specifically for geospatial data
            lat_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lat', 'latitude']) 
                      or "LAT" in col.upper()]
            lon_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lon', 'long', 'longitude'])
                      or "LON" in col.upper()]
            
            if lat_cols and lon_cols:
                st.warning("Geospatial data detected but visualization could not be created. "
                          "The system attempted to create a 3D map but failed. "
                          "This might be due to invalid coordinate data or other issues with map creation.")
            else:
                st.warning("No appropriate chart found for this data. Try a different query or data structure.")
                
    except Exception as e:
        print(f"Error in display_chart: {str(e)}")
        import traceback
        print(traceback.format_exc())
        st.error(f"Error creating visualization: {str(e)}")


def display_feedback_section(request_id: str):
    with st.popover("📝 Query Feedback"):
        if request_id not in st.session_state.form_submitted:
            with st.form(f"feedback_form_{request_id}", clear_on_submit=True):
                positive = st.radio(
                    "Rate the generated SQL", options=["👍", "👎"], horizontal=True
                )
                positive = positive == "👍"
                submit_disabled = (
                    request_id in st.session_state.form_submitted
                    and st.session_state.form_submitted[request_id]
                )

                feedback_message = st.text_input("Optional feedback message")
                submitted = st.form_submit_button("Submit", disabled=submit_disabled)
                if submitted:
                    err_msg = submit_feedback(request_id, positive, feedback_message)
                    st.session_state.form_submitted[request_id] = {"error": err_msg}
                    st.session_state.popover_open = False
                    st.rerun()
        elif (
            request_id in st.session_state.form_submitted
            and st.session_state.form_submitted[request_id]["error"] is None
        ):
            st.success("Feedback submitted", icon="✅")
        else:
            st.error(st.session_state.form_submitted[request_id]["error"])


def submit_feedback(
    request_id: str, positive: bool, feedback_message: str
) -> Optional[str]:
    request_body = {
        "request_id": request_id,
        "positive": positive,
        "feedback_message": feedback_message,
    }
    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        FEEDBACK_API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )
    if resp["status"] == 200:
        return None

    parsed_content = json.loads(resp["content"])
    # Craft readable error message
    err_msg = f"""
        🚨 An Analyst API error has occurred 🚨
        
        * response code: `{resp['status']}`
        * request-id: `{parsed_content['request_id']}`
        * error code: `{parsed_content['error_code']}`
        
        Message:
        ```
        {parsed_content['message']}
        ```
        """
    return err_msg


if __name__ == "__main__":
    main() 