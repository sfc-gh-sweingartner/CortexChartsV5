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
from utils.semantic_model_utils import SemanticModelParser, ColumnType
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
    st.session_state.form_submitted = {}  # Dictionary to store feedback submission for each request
    st.session_state.sql_execution_mode = "Run"  # Default SQL execution mode
    st.session_state.selected_columns = set()  # Selected columns from semantic model
    st.session_state.column_operations = {}  # Operations for selected columns
    st.session_state.generated_prompt = None  # Generated prompt from column selections


def show_header_and_sidebar():
    """Display the header and sidebar of the app."""
    # Set the title and introductory text of the app
    st.title("Cortex Analyst")
    st.markdown(
        "Welcome to Cortex Analyst! Type your questions below to interact with your data. "
    )

    # Sidebar with a reset button and semantic model selector
    with st.sidebar:
        selected_model = st.selectbox(
            "Selected semantic model:",
            AVAILABLE_SEMANTIC_MODELS_PATHS,
            format_func=lambda s: s.split("/")[-1],
            key="selected_semantic_model_path",
            on_change=reset_session_state,
        )
        
        st.divider()
        
        # Add SQL execution mode toggle
        st.radio(
            "SQL Execution Mode:",
            options=["Run", "View"],
            index=0,
            key="sql_execution_mode",
            horizontal=True,
        )
        
        st.divider()
        
        # Display semantic model columns
        display_semantic_model_columns(selected_model)
        
        st.divider()
        
        # Center this button
        _, btn_container, _ = st.columns([2, 6, 2])
        if btn_container.button("Clear Chat History", use_container_width=True):
            reset_session_state()


def display_semantic_model_columns(model_path: str):
    """Display columns from the semantic model in the sidebar.
    
    Args:
        model_path: Path to the semantic model YAML file
    """
    try:
        # Read the semantic model file
        file_path = model_path.split("@")[-1]  # Remove @ prefix if present
        yaml_content = session.sql(f"SELECT GET_STAGE_FILE_CONTENT('@{file_path}')").collect()[0][0]
        
        # Parse the semantic model
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Initialize session state for selected columns if not exists
        if "selected_columns" not in st.session_state:
            st.session_state.selected_columns = set()
        
        st.markdown("### Available Columns")
        
        # Create an expander for each table
        for table in sorted(tables, key=lambda x: x.name):
            with st.expander(f"📊 {table.name}", expanded=False):
                for col in table.columns:
                    # Create unique key for checkbox
                    col_key = f"{table.name}.{col.name}"
                    
                    # Create tooltip text
                    tooltip = f"""
                    **Column:** {col.name}
                    **Type:** {col.column_type.value}
                    **Data Type:** {col.data_type}
                    **Description:** {col.description or 'No description available'}
                    """
                    
                    # Create a container for the checkbox and tooltip
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        if st.checkbox(
                            col.name,
                            key=f"col_{col_key}",
                            value=col_key in st.session_state.selected_columns
                        ):
                            st.session_state.selected_columns.add(col_key)
                        else:
                            st.session_state.selected_columns.discard(col_key)
                    with col2:
                        st.markdown(f"<div title='{tooltip}'>ℹ️</div>", unsafe_allow_html=True)
        
        # If columns are selected, show the operation selection table
        if st.session_state.selected_columns:
            st.markdown("### Selected Columns")
            
            # Initialize operation selections if not exists
            if "column_operations" not in st.session_state:
                st.session_state.column_operations = {}
            
            # Create a DataFrame for the operations table
            operations_data = []
            for col_key in sorted(st.session_state.selected_columns):
                table_name, col_name = col_key.split(".")
                
                # Get or initialize operation settings
                if col_key not in st.session_state.column_operations:
                    st.session_state.column_operations[col_key] = {
                        "results": "Group By",
                        "filter": "Don't Filter"
                    }
                
                operations_data.append({
                    "Column": col_name,
                    "Results": st.selectbox(
                        f"Results for {col_name}",
                        ["Group By", "Sum", "Count", "Avg", "Min", "Max", "Don't Show"],
                        key=f"results_{col_key}",
                        index=["Group By", "Sum", "Count", "Avg", "Min", "Max", "Don't Show"].index(
                            st.session_state.column_operations[col_key]["results"]
                        )
                    ),
                    "Filter": st.text_input(
                        f"Filter for {col_name}",
                        value=st.session_state.column_operations[col_key]["filter"],
                        key=f"filter_{col_key}"
                    )
                })
                
                # Update the operations in session state
                st.session_state.column_operations[col_key] = {
                    "results": operations_data[-1]["Results"],
                    "filter": operations_data[-1]["Filter"]
                }
            
            # Add Generate Prompt button
            if st.button("Generate Prompt"):
                prompt = generate_prompt_from_selections()
                # Update the chat input with the generated prompt
                st.session_state.generated_prompt = prompt
                st.experimental_rerun()

    except Exception as e:
        st.error(f"Error loading semantic model: {str(e)}")


def generate_prompt_from_selections() -> str:
    """Generate a natural language prompt from the selected columns and operations.
    
    Returns:
        str: The generated prompt
    """
    # Start with "Show me"
    parts = ["Show me"]
    
    # Add columns and their operations
    result_parts = []
    filter_parts = []
    
    for col_key, ops in st.session_state.column_operations.items():
        _, col_name = col_key.split(".")
        
        # Handle results
        if ops["results"] != "Don't Show":
            if ops["results"] == "Group By":
                result_parts.append(col_name)
            else:
                result_parts.append(f"{ops['results']} of {col_name}")
        
        # Handle filters
        if ops["filter"] and ops["filter"] != "Don't Filter":
            filter_parts.append(f"{col_name} is {ops['filter']}")
    
    # Combine parts
    parts.append(" and ".join(result_parts))
    
    if filter_parts:
        parts.append("WHERE")
        parts.append(" AND ".join(filter_parts))
    
    # Add Group By clause
    group_by_cols = [
        col_key.split(".")[1]
        for col_key, ops in st.session_state.column_operations.items()
        if ops["results"] == "Group By"
    ]
    if group_by_cols:
        parts.append("Group by")
        parts.append(", ".join(group_by_cols))
    
    return " ".join(parts)


def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # If we have a generated prompt, use it as the default
    default_input = st.session_state.get("generated_prompt", "")
    if default_input:
        st.session_state.generated_prompt = None  # Clear it after use
    
    # Handle chat input
    user_input = st.chat_input("What is your question?", value=default_input)
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
    # Ensure we're working with a pandas DataFrame
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception as e:
            st.error("Could not process data into proper format for visualization")
            return

    # Limit to the top 5000 rows for visualization
    df_display = df.head(5000)
    
    # Identify column types
    numeric_cols = [col for col in df_display.columns if pd.api.types.is_numeric_dtype(df_display[col])]
    date_cols = [col for col in df_display.columns if pd.api.types.is_datetime64_any_dtype(df_display[col])]
    text_cols = [col for col in df_display.columns if col not in numeric_cols and col not in date_cols]
    
    try:
        # Check for KPI tiles first (single row with numeric columns)
        if len(df_display) == 1 and len(numeric_cols) >= 1:
            chart_metadata = {
                'chart10_columns': {
                    'numeric_cols': numeric_cols
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            kpi_result = create_chart10(df_display, chart_metadata['chart10_columns'])
            if kpi_result:
                # KPI tiles were already rendered by create_chart10
                # Just show the "Open in Designer" button
                if st.button("Open in Designer", key=f"send_to_designer_{message_index}"):
                    if "report_transfer" not in st.session_state:
                        st.session_state.report_transfer = {}
                    
                    # Extract SQL and prompt
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
                    
                    # Generate chart code
                    from utils.chart_utils import generate_chart_code_for_dataframe
                    chart_code = generate_chart_code_for_dataframe(df_display)
                    
                    # Store data for Report Designer
                    st.session_state.report_transfer = {
                        "df": df_display,
                        "sql": sql_statement,
                        "prompt": prompt,
                        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "redirect": True,
                        "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                        "chart_code": chart_code
                    }
                    
                    # Navigate to Report Designer
                    st.switch_page("pages/2_Report_Designer.py")
                return
        
        # If not a KPI tile or KPI creation failed, continue with other chart types
        chart_created = False
        alt_chart = None
        
        # Try to create a map visualization if we have both latitude and longitude columns
        lat_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lat', 'latitude']) 
                   or "LAT" in col.upper()]
        lon_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lon', 'long', 'longitude'])
                   or "LON" in col.upper()]
        
        if lat_cols and lon_cols:
            value_col = None
            if len(numeric_cols) > 0:
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
            alt_chart = create_chart11(df_display, chart_metadata['chart11_columns'])
            if alt_chart is not None:
                chart_created = True
        
        # If map visualization wasn't created or failed, try other chart types
        if not chart_created:
            # Chart Type 8: Multiple text columns, multiple numeric columns - Multi-Dimension Bubble
            if len(text_cols) >= 2 and len(numeric_cols) >= 3:
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
                alt_chart = create_chart8(df_display, chart_metadata['chart8_columns'])
                if alt_chart:
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
                alt_chart = create_chart7(df_display, chart_metadata['chart7_columns'])
                if alt_chart:
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
                alt_chart = create_chart6(df_display, chart_metadata['chart6_columns'])
                if alt_chart:
                    chart_created = True
            
            # Chart Type 4: Date column, multiple categorical columns, and numeric column - Stacked Bar with Selector
            if not chart_created and len(date_cols) >= 1 and len(text_cols) >= 2 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart4_columns': {
                        'date_col': date_cols[0],
                        'text_cols': text_cols,
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                alt_chart = create_chart4(df_display, chart_metadata['chart4_columns'])
                if alt_chart:
                    chart_created = True
            
            # Chart Type 2: Single date column, two numeric columns - Dual Axis Line Chart
            if not chart_created and len(date_cols) >= 1 and len(numeric_cols) >= 2:
                chart_metadata = {
                    'chart2_columns': {
                        'date_col': date_cols[0],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                alt_chart = create_chart2(df_display, chart_metadata['chart2_columns'])
                if alt_chart:
                    chart_created = True
            
            # Chart Type 3: Date column, categorical column, and numeric column - Stacked Bar Chart
            if not chart_created and len(date_cols) >= 1 and len(text_cols) >= 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart3_columns': {
                        'date_col': date_cols[0],
                        'text_col': text_cols[0],
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                alt_chart = create_chart3(df_display, chart_metadata['chart3_columns'])
                if alt_chart:
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
                alt_chart = create_chart5(df_display, chart_metadata['chart5_columns'])
                if alt_chart:
                    chart_created = True
            
            # Chart Type 1: Single date column and single numeric column - Line Chart
            if not chart_created and len(date_cols) >= 1 and len(numeric_cols) >= 1:
                chart_metadata = {
                    'chart1_columns': {
                        'date_col': date_cols[0],
                        'numeric_col': numeric_cols[0]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                alt_chart = create_chart1(df_display, chart_metadata['chart1_columns'])
                if alt_chart:
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
                alt_chart = create_chart9(df_display, chart_metadata['chart9_columns'])
                if alt_chart:
                    chart_created = True
        
        # Display the chart if one was created
        if chart_created and alt_chart:
            if isinstance(alt_chart, pdk.Deck):
                st.pydeck_chart(alt_chart)
                # For maps (Chart 11), show "Open in Map Designer" button
                if st.button("Open in Map Designer", key=f"send_to_map_designer_{message_index}"):
                    if "map_transfer" not in st.session_state:
                        st.session_state.map_transfer = {}
                    
                    # Extract SQL and prompt
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
                    
                    # Generate chart code
                    from utils.chart_utils import generate_chart_code_for_dataframe
                    chart_code = generate_chart_code_for_dataframe(df_display)
                    
                    # Store data for Map Designer
                    st.session_state.map_transfer = {
                        "df": df_display,
                        "sql": sql_statement,
                        "prompt": prompt,
                        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "redirect": True,
                        "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                        "chart_code": chart_code
                    }
                    
                    # Navigate to Map Designer
                    st.switch_page("pages/3_Map_Designer.py")
            else:
                st.altair_chart(alt_chart, use_container_width=True)
                # For non-map charts (Chart 1-10), show "Open in Designer" button
                if st.button("Open in Designer", key=f"send_to_designer_{message_index}"):
                    if "report_transfer" not in st.session_state:
                        st.session_state.report_transfer = {}
                    
                    # Extract SQL and prompt
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
                    
                    # Generate chart code
                    from utils.chart_utils import generate_chart_code_for_dataframe
                    chart_code = generate_chart_code_for_dataframe(df_display)
                    
                    # Store data for Report Designer
                    st.session_state.report_transfer = {
                        "df": df_display,
                        "sql": sql_statement,
                        "prompt": prompt,
                        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "redirect": True,
                        "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                        "chart_code": chart_code
                    }
                    
                    # Navigate to Report Designer
                    st.switch_page("pages/2_Report_Designer.py")
        else:
            st.warning("No appropriate chart found for this data structure.")
            
    except Exception as e:
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