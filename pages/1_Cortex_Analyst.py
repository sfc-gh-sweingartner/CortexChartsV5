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
from snowflake.snowpark.files import SnowflakeFile
import sys
import os

# Geospatial visualization imports
try:
    import pydeck as pdk
    import numpy as np
except ImportError as e:
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
    "SYNTHEA.SYNTHEA.SYNTHEA/syntheav4.yaml",
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
    # Make sure the reset flag is initialized
    if "reset_requested" not in st.session_state:
        st.session_state.reset_requested = False
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
    
    # Clear column selections
    st.session_state.selected_columns = set()  # Selected columns from semantic model
    st.session_state.column_operations = {}  # Operations for selected columns
    
    # Clear prompt related state
    st.session_state.generated_prompt = None  # Generated prompt from column selections
    st.session_state.show_prompt_preview = False  # Flag to control prompt preview visibility
    st.session_state.pending_prompt = None  # Prompt waiting to be sent to chat
    
    # Set a flag to indicate a reset was requested rather than trying to modify widget values directly
    st.session_state.reset_requested = True
    
    # Instead of trying to modify checkbox values directly (which causes errors),
    # we'll use the reset_requested flag when initializing the checkboxes


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
        if btn_container.button("Clear Chat History", type="primary", use_container_width=True):
            reset_session_state()
            # Trigger a rerun to ensure the UI refreshes completely
            st.rerun()


def display_semantic_model_columns(model_path: str):
    """Display columns from the semantic model in the sidebar.
    
    Args:
        model_path: Path to the semantic model YAML file
    """
    # Check if a reset was requested and clear selections if needed
    reset_requested = st.session_state.get("reset_requested", False)
    if reset_requested:
        # Clear the reset flag so it doesn't persist
        st.session_state.reset_requested = False
        
        # We only need to clear the selected_columns set, as the checkboxes
        # will be initialized based on this value
        st.session_state.selected_columns = set()
        st.session_state.column_operations = {}
    
    try:
        # Read the semantic model file using a different approach
        file_path = model_path.split("@")[-1]  # Remove @ prefix if present
        
        # Use SELECT $1 with a named 'raw text' file format
        yaml_content = None
        staged_file_access_path = f"@{file_path}" # e.g. @DATABASE.SCHEMA.STAGE/path/to/file.yaml
        
        # Ensure this named file format exists in your Snowflake environment and is accessible.
        # Example: CREATE OR REPLACE FILE FORMAT YOUR_DB.YOUR_SCHEMA.my_raw_text_format TYPE = CSV FIELD_DELIMITER = NONE EMPTY_FIELD_AS_NULL = FALSE ...;
        # Adjust the file format name if yours is different or in a different schema.
        # Assuming the format is in the session's current schema or fully qualified.
        # For simplicity, let's assume it's accessible as 'my_raw_text_format'. 
        # If it's in a specific schema, use 'YOUR_SCHEMA.my_raw_text_format'.
        # We will use the name you provided from scratch.sql, assuming it's in the session's default schema.
        named_file_format = "CortexChartsV4.cortex_read_yaml_format" # Using fully qualified name

        query = f"""SELECT $1 
FROM '{staged_file_access_path}' 
(FILE_FORMAT => '{named_file_format}');"""
        
        try:
            result_rows = session.sql(query).collect() # result_rows is a list of Snowpark Row objects
            if result_rows:
                # Each row in result_rows contains one line of the YAML in its first column (index 0).
                # Filter out potential None values if a line could be null for some reason.
                lines = [row[0] for row in result_rows if row[0] is not None]
                if lines:
                    yaml_content = "\n".join(lines)
            else:
                raise ValueError(f"Query with named file format '{named_file_format}' returned no data for '{file_path}'. File might be empty, inaccessible, or path/format name incorrect.")
        except Exception as e:
            if "Failed to parse stage location" in str(e) or "syntax error" in str(e).lower() or "does not exist or not authorized" in str(e).lower():
                 raise ValueError(f"Error with SQL query using named file format: {query}. Ensure path '{file_path}' and format '{named_file_format}' are correct and accessible. Original error: {str(e)}")
            raise ValueError(f"Error reading from stage with named file format '{named_file_format}' for '{file_path}': {str(e)}. Query: {query}")

        if yaml_content is None or not yaml_content.strip(): # Ensure content is not just whitespace
            raise ValueError(f"Failed to load YAML content from stage for '{file_path}'. Content is empty or could not be read.")
        
        # Parse the semantic model
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Initialize session state for selected columns if not exists
        if "selected_columns" not in st.session_state:
            st.session_state.selected_columns = set()
        
        # Display model information if available
        if tables:
            st.markdown("### Semantic Model Columns")
            st.write(f"**Tables:** {len(tables)}")
            
            # Create filter options for column types
            col_type_filter = st.multiselect(
                "Filter by column type:",
                ["Dimensions", "Facts", "Time Dimensions"],
                default=["Dimensions", "Facts", "Time Dimensions"],
                key="column_type_filter"
            )
            
            # Map the filter options to ColumnType enum values
            type_map = {
                "Dimensions": ColumnType.DIMENSION,
                "Facts": ColumnType.FACT,
                "Time Dimensions": ColumnType.TIME_DIMENSION
            }
            
            # Filter columns by type
            filtered_types = [type_map[t] for t in col_type_filter]
            
            # Optional search box for columns
            search_term = st.text_input("Search columns:", key="column_search").lower()
        
        # Add custom CSS for tooltips
        st.markdown("""
        <style>
        .column-tooltip {
            position: relative;
            display: inline-block;
        }
        
        .column-tooltip .tooltip-text {
            visibility: hidden;
            width: 250px;
            background-color: #333;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.8em;
            line-height: 1.2;
        }
        
        .column-tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create an expander for each table
        for table in sorted(tables, key=lambda x: x.name):
            # Filter columns in this table based on selected types
            table_columns = [col for col in table.columns if col.column_type in filtered_types]
            
            # Apply search filter if provided
            if search_term:
                table_columns = [col for col in table_columns if search_term in col.name.lower() or 
                                (col.description and search_term in col.description.lower())]
            
            # Skip empty tables after filtering
            if not table_columns:
                continue
                
            with st.expander(f"📊 {table.name}", expanded=False):
                # Show table description if available
                if table.description:
                    st.markdown(f"*{table.description}*")
                
                # Create a container for the columns
                for col in table_columns:
                    # Create unique key for checkbox
                    col_key = f"{table.name}.{col.name}"
                    
                    # Extract column info
                    type_display = col.column_type.value.replace('_', ' ').title()
                    description = col.description or "No description available"
                    
                    # Add icon based on column type
                    icon = "🔢" if col.column_type == ColumnType.FACT else "📅" if col.column_type == ColumnType.TIME_DIMENSION else "📝"
                    
                    # Add sample values if available
                    sample_text = ""
                    if hasattr(col, 'sample_values') and col.sample_values and len(col.sample_values) > 0:
                        samples = ", ".join([str(v) for v in col.sample_values[:3]])
                        sample_text = f"\n<strong>Examples:</strong> {samples}"
                    
                    # Use a single column instead of split columns and handle the checkbox state
                    # The value is determined solely by whether the column key is in selected_columns
                    # This avoids trying to directly modify widget values which causes errors
                    checked = st.checkbox(
                        f"{icon} {col.name}",
                        key=f"col_{col_key}",
                        value=col_key in st.session_state.selected_columns,
                        help=f"Type: {type_display} | Data Type: {col.data_type} | Description: {description}{sample_text}"
                    )
                    
                    # Update the selection state
                    if checked:
                        st.session_state.selected_columns.add(col_key)
                    else:
                        st.session_state.selected_columns.discard(col_key)
        
        # If columns are selected, show the operation selection table
        if st.session_state.selected_columns:
            st.markdown("### Selected Columns")
            
            # Prepare data for the operations table
            operations_data = []
            
            # Process each selected column
            for col_key in sorted(st.session_state.selected_columns):
                table_name, col_name = col_key.split(".")
                
                # Get or initialize operation settings
                if col_key not in st.session_state.column_operations:
                    # Default operation based on column type
                    default_op = "Group By"
                    for table in tables:
                        if table.name == table_name:
                            for col in table.columns:
                                if col.name == col_name:
                                    if col.column_type == ColumnType.FACT:
                                        default_op = "Sum"
                                    elif col.column_type == ColumnType.TIME_DIMENSION:
                                        default_op = "Group By"
                                    break
                            break
                            
                    st.session_state.column_operations[col_key] = {
                        "results": default_op,
                        "filter": "Don't Filter"
                    }
                
                # Determine available operations based on column type
                col_type = None
                for table in tables:
                    if table.name == table_name:
                        for col in table.columns:
                            if col.name == col_name:
                                col_type = col.column_type
                                break
                        break
                
                # Different operation options based on column type
                if col_type == ColumnType.FACT:
                    operations = ["Group By", "Sum", "Count", "Avg", "Min", "Max", "Don't Show"]
                elif col_type == ColumnType.TIME_DIMENSION:
                    operations = ["Group By", "Count", "Truncate to Day", "Truncate to Month", "Don't Show"]
                else:  # Dimension
                    operations = ["Group By", "Count", "Don't Show"]
                
                operations_data.append({
                    "Table": table_name,
                    "Column": col_name,
                    "Results": st.selectbox(
                        f"Results for {table_name}.{col_name}",
                        operations,
                        key=f"results_{col_key}",
                        index=operations.index(
                            st.session_state.column_operations[col_key]["results"]
                        ) if st.session_state.column_operations[col_key]["results"] in operations else 0
                    ),
                    "Filter": st.text_input(
                        f"Filter for {table_name}.{col_name}",
                        value=st.session_state.column_operations[col_key]["filter"],
                        key=f"filter_{col_key}"
                    )
                })
                
                # Update the operation in session state
                st.session_state.column_operations[col_key] = {
                    "results": operations_data[-1]["Results"],
                    "filter": operations_data[-1]["Filter"]
                }
            
            # Clean up operations for columns that are no longer selected
            for col_key in list(st.session_state.column_operations.keys()):
                if col_key not in st.session_state.selected_columns:
                    del st.session_state.column_operations[col_key]
            
            # Add Generate Prompt button and editable prompt area
            # Full width Generate Prompt button
            if st.button("Generate Prompt", use_container_width=True, type="primary"):
                prompt = generate_prompt_from_selections()
                # Store the prompt in session state to display in the preview area
                st.session_state.pending_prompt = prompt
                st.session_state.show_prompt_preview = True
                st.rerun()  # Rerun to show the preview
            
            # If we have a pending prompt, show the preview
            if st.session_state.show_prompt_preview and st.session_state.pending_prompt:
                st.markdown("### Preview Prompt")
                # Create an editable text area for the prompt
                edited_prompt = st.text_area(
                    "Edit your prompt before sending:",
                    value=st.session_state.pending_prompt,
                    height=100,
                    key="prompt_editor"
                )
                
                # Add Send to Chat button
                if st.button("Send to Chat", type="primary"):
                    # Instead of just storing the prompt, directly process it
                    prompt = edited_prompt
                    st.session_state.show_prompt_preview = False
                    st.session_state.pending_prompt = None
                    # Process the prompt directly
                    process_user_input(prompt)
                    # No need for st.rerun() since process_user_input will rerun
                
                # Add Clear button
                if st.button("Clear", type="secondary"):
                    st.session_state.show_prompt_preview = False
                    st.session_state.pending_prompt = None
                    st.rerun()

    except Exception as e:
        st.error(f"Error loading semantic model: {str(e)}")
        import traceback
        st.sidebar.error(f"Error details: {traceback.format_exc()}")


def generate_prompt_from_selections() -> str:
    """Generate a natural language prompt from the selected columns and operations.
    
    Returns:
        str: The generated prompt
    """
    parts = []
    
    # Add columns and their operations
    result_parts = []
    filter_parts = []
    group_by_parts = []
    
    for col_key, ops in st.session_state.column_operations.items():
        table_name, col_name = col_key.split(".")
        
        # Format with table name included
        qualified_col_name = f"{table_name} {col_name}"
        
        # Handle filters - collect them for the beginning of the prompt
        if ops["filter"] and ops["filter"] != "Don't Filter":
            filter_parts.append(f"{qualified_col_name} of {ops['filter']}")
        
        # Handle results
        if ops["results"] != "Don't Show":
            if ops["results"] == "Group By":
                result_parts.append(qualified_col_name)
                group_by_parts.append(qualified_col_name)
            elif ops["results"] == "Truncate to Day":
                result_parts.append(f"truncate {qualified_col_name} to day")
                group_by_parts.append(f"truncate {qualified_col_name} to day")
            elif ops["results"] == "Truncate to Month":
                result_parts.append(f"truncate {qualified_col_name} to month")
                group_by_parts.append(f"truncate {qualified_col_name} to month")
            else:
                result_parts.append(f"{ops['results']} of {qualified_col_name}")
    
    # Start with filter parts if they exist (For the X of Y, ...)
    if filter_parts:
        filters_text = " and ".join(filter_parts)
        parts.append(f"For the {filters_text},")
    
    # Add the main "Show me" part
    parts.append("Show me")
    
    # Add result columns
    if result_parts:
        parts.append(" and ".join(result_parts))
    
    # Add Group By clause at the end
    if group_by_parts:
        parts.append("Grouped by")
        parts.append(", ".join(group_by_parts))
    
    return " ".join(parts)


def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # Get the generated prompt if it exists
    prompt_from_generator = st.session_state.get("generated_prompt")
    
    # Handle chat input - Streamlit in Snowflake doesn't support the 'value' parameter
    user_input = st.chat_input(
        "What is your question?",
        key="chat_input"
    )
    
    # If we have a generated prompt, display it prominently above the chat input
    if prompt_from_generator:
        # Display the prompt in a highly visible way
        st.markdown("### 👇 Click in chat input below and paste this prompt:")
        st.code(prompt_from_generator, language=None)
        # Clear the generated prompt after displaying it
        st.session_state.generated_prompt = None
    
    # Process user input when provided
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
                    # Calculate approximate memory usage
                    df_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

                    # More aggressive row limit for large datasets
                    if df_size_mb > 20:  # If estimated size is over 20MB, use stricter limit
                        # Calculate a reasonable row limit based on size
                        # If 5,000 rows is 0.75 MB (from testing), we can estimate how many rows would reach ~10 MB
                        estimated_row_size_kb = (df_size_mb * 1024) / len(df)  # KB per row
                        safe_row_limit = int(10 * 1024 / estimated_row_size_kb)  # Rows for ~10 MB
                        
                        # Cap between 5,000 and 20,000
                        ROW_DISPLAY_LIMIT = max(5000, min(safe_row_limit, 20000))
                    else:
                        ROW_DISPLAY_LIMIT = 10000
                    
                    # Apply row limit for display
                    if len(df) > ROW_DISPLAY_LIMIT:
                        display_df = df.head(ROW_DISPLAY_LIMIT)
                        st.info(f"Showing first {ROW_DISPLAY_LIMIT:,} rows of {len(df):,} total rows to avoid size limitations.")
                    else:
                        display_df = df
                    
                    try:
                        st.dataframe(display_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying dataframe: {str(e)}")
                        # If display fails, try with even fewer rows
                        st.write("Attempting to display with fewer rows...")
                        try:
                            st.dataframe(display_df.head(1000), use_container_width=True)
                        except Exception as e2:
                            st.error(f"Still failed with reduced rows: {str(e2)}")
                    
                    # Pass a potentially reduced dataframe to chart display to avoid memory issues
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

    # Calculate dataframe size for optimizations
    df_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    # Calculate a reasonable row limit for visualization based on size
    if df_size_mb > 0:
        # Estimate how many rows would reach ~8 MB (safe for visualization)
        estimated_row_size_kb = (df_size_mb * 1024) / len(df)  # KB per row
        safe_row_limit = int(8 * 1024 / estimated_row_size_kb)  # Rows for ~8 MB
        
        # Cap between 3,000 and 20,000 rows
        MAX_CHART_ROWS = max(3000, min(safe_row_limit, 20000))
    else:
        MAX_CHART_ROWS = 3000

    # Apply the dynamic row limit
    if len(df) > MAX_CHART_ROWS:
        st.info(f"Chart visualization is limited to the first {MAX_CHART_ROWS:,} rows of {len(df):,} total rows.")
        df_display = df.head(MAX_CHART_ROWS)
    else:
        df_display = df
    
    # Further optimize the dataframe if it's still large
    display_size_mb = df_display.memory_usage(deep=True).sum() / (1024 * 1024)
    if display_size_mb > 10:  # If still over 10MB
        # Convert float64 to float32 and int64 to int32 to reduce memory
        for col in df_display.select_dtypes(include=['float64']).columns:
            df_display[col] = df_display[col].astype('float32')
        
        for col in df_display.select_dtypes(include=['int64']).columns:
            df_display[col] = df_display[col].astype('int32')
        
        # For string columns, limit the length if any are excessively long
        for col in df_display.select_dtypes(include=['object']).columns:
            # Check if we have any long string values
            max_len = df_display[col].astype(str).map(len).max()
            if max_len > 100:  # If strings longer than 100 chars
                df_display[col] = df_display[col].astype(str).str.slice(0, 100)
    
    # Identify column types
    numeric_cols = [col for col in df_display.columns if pd.api.types.is_numeric_dtype(df_display[col])]
    
    # Enhanced date column detection - also look for date-like string columns
    date_cols = [col for col in df_display.columns if pd.api.types.is_datetime64_any_dtype(df_display[col])]
    
    # If no date columns found, try to detect string columns that might contain dates
    if not date_cols:
        # Look for columns with common date-related names
        date_name_candidates = [col for col in df_display.columns 
                               if any(term in col.lower() for term in ['date', 'time', 'day', 'month', 'year'])]
        
        # Try to convert these columns to datetime
        for col in date_name_candidates:
            if col not in numeric_cols and col not in date_cols:  # Skip if already classified
                try:
                    # Sample a few values to check if they can be parsed as dates
                    sample = df_display[col].dropna().head(5)
                    if not sample.empty:
                        pd.to_datetime(sample, errors='raise')
                        # If successful, add to date columns and create a datetime version
                        date_cols.append(col)
                        # No need to convert the actual column, just identify it as a date column
                except (ValueError, TypeError):
                    # Not a date column, continue checking others
                    pass
    
    # Identify remaining text columns (those that are neither numeric nor dates)
    text_cols = [col for col in df_display.columns if col not in numeric_cols and col not in date_cols]
    
    try:
        # Initialize chart variables
        chart_created = False
        alt_chart = None
        chart_type = None

        # CHART SELECTION LOGIC - following the priority in chart-system rules
        
        # Check #1: Is there a latitude and longitude column? (Chart 11 - Geospatial Map)
        lat_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lat', 'latitude']) 
                  or "LAT" in col.upper()]
        lon_cols = [col for col in df_display.columns if any(term in col.lower() for term in ['lon', 'long', 'longitude'])
                  or "LON" in col.upper()]
        
        if lat_cols and lon_cols:
            # Find a numeric column for the value (if any)
            value_col = None
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
                chart_type = "Chart 11: Geospatial Map"
        
        # Check #2: Is there a single row of data with 1 to four numeric columns? (Chart 10 - KPI Tiles)
        if not chart_created and len(df_display) == 1 and len(numeric_cols) >= 1 and len(numeric_cols) <= 4:
            chart_metadata = {
                'chart10_columns': {
                    'numeric_cols': numeric_cols
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            kpi_result = create_chart10(df_display, chart_metadata['chart10_columns'])
            
            if kpi_result:
                chart_created = True
                chart_type = "Chart 10: KPI Tiles"
        
        # Check #3: Is there exactly one date column?
        if not chart_created and len(date_cols) == 1:
            # Case 3a: One date column + one numeric column = Chart 1 (Line/Bar Chart by Date)
            if len(numeric_cols) == 1 and len(text_cols) == 0:
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
                    chart_type = "Chart 1: Line/Bar Chart by Date"
            
            # Case 3b: One date column + two numeric columns = Chart 2 (Dual Axis Line Chart)
            elif len(numeric_cols) >= 2 and len(text_cols) == 0:
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
                    chart_type = "Chart 2: Dual Axis Line Chart"
            
            # Case 3c: One date column + one text column + one numeric column = Chart 3 (Stacked Bar Chart by Date)
            elif len(numeric_cols) >= 1 and len(text_cols) == 1:
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
                    chart_type = "Chart 3: Stacked Bar Chart by Date"
            
            # Case 3d: One date column + multiple text columns (2+) + one numeric column = Chart 4 (Stacked Bar with Column Selector)
            elif len(numeric_cols) >= 1 and len(text_cols) >= 2:
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
                    chart_type = "Chart 4: Stacked Bar with Column Selector"
        
        # If no date column and chart not created yet
        if not chart_created and len(date_cols) == 0:
            # Case: Multiple text columns (2+) + multiple numeric columns (3+) = Chart 8 (Multi-Dimension Bubble)
            # Check for Chart 8 first as it's more specific than Chart 6
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
                    chart_type = "Chart 8: Multi-Dimension Bubble"
            
            # Case: One text column + three numeric columns = Chart 7 (Bubble Chart)
            elif len(text_cols) == 1 and len(numeric_cols) >= 3:
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
                    chart_type = "Chart 7: Bubble Chart"
                    
            # Case: One text column + two numeric columns = Chart 5 (Scatter Plot)
            elif len(text_cols) == 1 and len(numeric_cols) >= 2:
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
                    chart_type = "Chart 5: Scatter Plot"
            
            # Case: Two text columns + two numeric columns = Chart 6 (Multi-Dimension Scatter)
            # Modified to be more specific - exactly 2 numeric columns
            elif len(text_cols) >= 2 and len(numeric_cols) == 2:
                chart_metadata = {
                    'chart6_columns': {
                        'text_col1': text_cols[0],
                        'text_col2': text_cols[1],
                        'num_col1': numeric_cols[0],
                        'num_col2': numeric_cols[1]
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                alt_charge = create_chart6(df_display, chart_metadata['chart6_columns'])
                
                if alt_charge:
                    chart_created = True
                    chart_type = "Chart 6: Multi-Dimension Scatter"
            
            # Case: Any number of text columns (1+) + one numeric column = Chart 9 (Bar Chart with Selectors)
            # IMPORTANT: This is a fallback option and should only be used when no other chart type matches
            elif len(text_cols) >= 1 and len(numeric_cols) >= 1:
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
                    chart_type = "Chart 9: Bar Chart with Selectors"
        
        # Display the chart if one was created
        if chart_created:
            # Display chart type information
            if chart_type:
                st.caption(f"**Selected Visualization**: {chart_type}")
            
            # Handle different chart display based on type
            if isinstance(alt_chart, pdk.Deck):
                st.pydeck_chart(alt_chart)
                # For maps (Chart 11), show "Open in Map Designer" button
                if st.button("Open in Map Designer", key=f"send_to_map_designer_{message_index}", type="primary"):
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
                    st.switch_page("pages/4_Map_Designer.py")
            elif chart_type == "Chart 10: KPI Tiles":
                # KPI tiles are already rendered by create_chart10
                # Just show the "Open in Designer" button
                if st.button("Open in Designer", key=f"send_to_designer_{message_index}", type="primary"):
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
                st.altair_chart(alt_chart, use_container_width=True)
                # For regular charts, show "Open in Designer" button
                if st.button("Open in Designer", key=f"send_to_designer_{message_index}", type="primary"):
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
        import traceback
        st.error(traceback.format_exc())


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