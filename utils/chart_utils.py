"""
Chart Utilities
==============
Shared chart creation utilities for Cortex Analyst and Report Designer.
This module provides centralized chart generation logic to ensure consistent
visualization between different parts of the application.
"""
import pandas as pd
import altair as alt
import streamlit as st
import sys
import numpy as np
import time  # Add time for generating unique keys

# Imports for geospatial visualization
GEOSPATIAL_LIBRARIES_AVAILABLE = True
try:
    import pydeck as pdk
    import h3
    import branca.colormap as cm
    print("Successfully imported geospatial libraries at module level")
except ImportError as e:
    GEOSPATIAL_LIBRARIES_AVAILABLE = False
    print(f"Warning: Geospatial libraries not available at module level: {str(e)}")
    # These libraries may not be available in all environments
    # We'll attempt to import them again in the specific functions that need them

# Define color schemes for geospatial maps, adapted from 3_Geospatial_Analysis.py
GEOSPATIAL_COLORS = {
    "White-Blue": ['#ffffff', '#ddddff', '#bbbbff', '#9999ff', '#7777ff', '#1F00FF'],
    "White-Red": ['#ffffff', '#ffdddd', '#ffbbbb', '#ff9999', '#ff7777', '#FF1F00'],
    "White-Green": ['#ffffff', '#ddffdd', '#bbffbb', '#99ff99', '#77ff77', '#00FF1F'],
    "Yellow-Blue": ['#fafa6e','#e1f46e','#caee70','#b3e773','#9ddf77','#89d77b','#75cf7f','#62c682',
                  '#51bd86','#40b488','#31aa89','#24a08a','#199689','#138c87','#138284','#17787f',
                  '#1d6e79','#226472','#265b6b','#285162','#2a4858'],
    "Yellow-Red": ['#ffff00', '#ffdd00', '#ffbb00', '#ff9900', '#ff5500', '#ff0000'],
    "Blue-Green": ['#0000ff', '#0044ff', '#0088ff', '#00ccff', '#00ee99', '#00ff00']
}


def create_chart_from_metadata(df):
    """
    Create an Altair chart based on the chart_metadata in the dataframe.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with chart_metadata attribute containing chart configuration
        
    Returns:
    --------
    altair.Chart or None
        The created chart object or None if chart couldn't be created
    """
    try:
        if not hasattr(df, 'attrs') or 'chart_metadata' not in df.attrs:
            return None
            
        chart_metadata = df.attrs.get('chart_metadata', {})
        
        # Determine which chart type to create based on metadata
        if 'chart1_columns' in chart_metadata:
            return create_chart1(df, chart_metadata['chart1_columns'])
        elif 'chart2_columns' in chart_metadata:
            return create_chart2(df, chart_metadata['chart2_columns'])
        elif 'chart3_columns' in chart_metadata:
            return create_chart3(df, chart_metadata['chart3_columns'])
        elif 'chart4_columns' in chart_metadata:
            return create_chart4(df, chart_metadata['chart4_columns'])
        elif 'chart5_columns' in chart_metadata:
            return create_chart5(df, chart_metadata['chart5_columns'])
        elif 'chart6_columns' in chart_metadata:
            return create_chart6(df, chart_metadata['chart6_columns'])
        elif 'chart7_columns' in chart_metadata:
            return create_chart7(df, chart_metadata['chart7_columns'])
        elif 'chart8_columns' in chart_metadata:
            return create_chart8(df, chart_metadata['chart8_columns'])
        elif 'chart9_columns' in chart_metadata:
            return create_chart9(df, chart_metadata['chart9_columns'])
        elif 'chart10_columns' in chart_metadata:
            return create_chart10(df, chart_metadata['chart10_columns'])
        elif 'chart11_columns' in chart_metadata:
            return create_chart11(df, chart_metadata['chart11_columns'])
        
        # If no specific metadata found, return None
        return None
        
    except Exception as e:
        print(f"Error creating chart from metadata: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def create_chart1(df, cols):
    """
    Create Chart 1: Bar Chart by Date
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col and numeric_col
        
    Returns:
    --------
    altair.Chart
        Bar chart with date on x-axis and numeric value on y-axis
    """
    try:
        date_col = cols.get('date_col')
        numeric_col = cols.get('numeric_col')
        
        # Display chart type as normal text
        st.text("Bar Chart by Date")
        
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q'),
            tooltip=[date_col, numeric_col]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 1: {str(e)}")
        return None


def create_chart2(df, cols):
    """
    Create Chart 2: Dual Axis Line Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, num_col1, and num_col2
        
    Returns:
    --------
    altair.LayerChart
        Dual line chart with date on x-axis and two numeric values on independent y-axes
    """
    try:
        date_col = cols.get('date_col')
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        
        # Display chart type as normal text
        st.text("Dual Axis Line Chart")
        
        base = alt.Chart(df).encode(x=alt.X(date_col + ':T', sort='ascending'))
        line1 = base.mark_line(color='blue').encode(
            y=alt.Y(num_col1 + ':Q', axis=alt.Axis(title=num_col1)),
            tooltip=[date_col, num_col1]
        )
        line2 = base.mark_line(color='red').encode(
            y=alt.Y(num_col2 + ':Q', axis=alt.Axis(title=num_col2)),
            tooltip=[date_col, num_col2]
        )
        return alt.layer(line1, line2).resolve_scale(
            y='independent'
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 2: {str(e)}")
        return None


def create_chart3(df, cols):
    """
    Create Chart 3: Stacked Bar Chart by Date
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, text_col, and numeric_col
        
    Returns:
    --------
    altair.Chart
        Stacked bar chart with date on x-axis, numeric value on y-axis, and categorical color
    """
    try:
        date_col = cols.get('date_col')
        text_col = cols.get('text_col')
        numeric_col = cols.get('numeric_col')
        
        # Display chart type as normal text
        st.text("Stacked Bar Chart by Date")
        
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q', stack='zero'),
            color=alt.Color(text_col + ':N'),
            tooltip=[date_col, text_col, numeric_col]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 3: {str(e)}")
        return None


def create_chart4(df, cols):
    """
    Create Chart 4: Stacked Bar Chart with Text Column Selector for Colors
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, text_cols, and numeric_col
        
    Returns:
    --------
    altair.Chart
        Stacked bar chart with date on x-axis, numeric value on y-axis, and selectable categorical colors
    """
    try:
        date_col = cols.get('date_col')
        text_cols = cols.get('text_cols', [])
        numeric_col = cols.get('numeric_col')
        
        # Display chart type as normal text
        st.text("Stacked Bar Chart with Selectable Colors")
        
        # Ensure we have at least one text column
        if not text_cols:
            # Find suitable text columns if not specified
            all_cols = list(df.columns)
            possible_text_cols = [col for col in all_cols if col != date_col and col != numeric_col]
            if possible_text_cols:
                text_cols = possible_text_cols
            else:
                # If no text columns available, return None
                return None
        
        # Generate a unique key for this chart based on dataframe and columns
        df_hash = hash(str(df.shape) + str(df.columns.tolist()))
        widget_key = f"chart4_select_{df_hash}"
        
        # Initialize the session state value if it doesn't exist
        if widget_key not in st.session_state:
            st.session_state[widget_key] = text_cols[0]
        # If the value exists but is not in text_cols (changed data), reset it
        elif st.session_state[widget_key] not in text_cols:
            st.session_state[widget_key] = text_cols[0]
        
        # Get the selected column from session state
        selected_text_col = st.selectbox(
            "Select column for color grouping:",
            options=text_cols,
            index=text_cols.index(st.session_state[widget_key]),
            key=widget_key
        )
        
        # Create the chart with the selected text column
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q', stack='zero'),
            color=alt.Color(selected_text_col + ':N', title=selected_text_col),
            tooltip=[date_col, selected_text_col, numeric_col]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 4: {str(e)}")
        return None


def create_chart5(df, cols):
    """
    Create Chart 5: Scatter Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, and text_col
        
    Returns:
    --------
    altair.Chart
        Scatter chart with numeric x/y and categorical color
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        text_col = cols.get('text_col')
        
        # Display chart type as normal text
        st.text("Scatter Chart")
        
        return alt.Chart(df).mark_circle(size=100).encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            color=alt.Color(text_col + ':N'),
            tooltip=[text_col, num_col1, num_col2]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 5: {str(e)}")
        return None


def create_chart6(df, cols):
    """
    Create Chart 6: Scatter Chart with Multiple Dimensions
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, text_col1, and text_col2
        
    Returns:
    --------
    altair.Chart
        Scatter chart with numeric x/y and categorical color and shape
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        text_col1 = cols.get('text_col1')
        text_col2 = cols.get('text_col2')
        
        # Display chart type as normal text
        st.text("Scatter Chart with Multiple Dimensions")
        
        return alt.Chart(df).mark_point(size=100).encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            color=alt.Color(text_col1 + ':N'),
            shape=alt.Shape(text_col2 + ':N', scale=alt.Scale(
                range=["circle", "square", "cross", "diamond", "triangle-up", "triangle-down", 
                       "triangle-right", "triangle-left", "arrow", "wedge", "stroke"]
            )),
            tooltip=[text_col1, text_col2, num_col1, num_col2]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 6: {str(e)}")
        return None


def create_chart7(df, cols):
    """
    Create Chart 7: Bubble Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, num_col3, and text_col
        
    Returns:
    --------
    altair.Chart
        Bubble chart with numeric x/y/size and categorical color
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        num_col3 = cols.get('num_col3')
        text_col = cols.get('text_col')
        
        # Display chart type as normal text
        st.text("Bubble Chart")
        
        return alt.Chart(df).mark_circle().encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            size=alt.Size(num_col3 + ':Q'),
            color=alt.Color(text_col + ':N'),
            tooltip=[text_col, num_col1, num_col2, num_col3]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 7: {str(e)}")
        return None


def create_chart8(df, cols):
    """
    Create Chart 8: Multi-Dimensional Bubble Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, num_col3, text_col1, and text_col2
        
    Returns:
    --------
    altair.Chart
        Multi-dimensional bubble chart with numeric x/y/size and categorical color and shape
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        num_col3 = cols.get('num_col3')
        text_col1 = cols.get('text_col1')
        text_col2 = cols.get('text_col2')
        
        # Display chart type as normal text
        st.text("Multi-Dimensional Bubble Chart")
        
        return alt.Chart(df).mark_point().encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            size=alt.Size(num_col3 + ':Q'),
            color=alt.Color(text_col1 + ':N'),
            shape=alt.Shape(text_col2 + ':N', scale=alt.Scale(
                range=["circle", "square", "cross", "diamond", "triangle-up", "triangle-down", 
                       "triangle-right", "triangle-left", "arrow", "wedge", "stroke"]
            )),
            tooltip=[text_col1, text_col2, num_col1, num_col2, num_col3]
        ).properties(title='')
    except Exception as e:
        print(f"Error creating Chart 8: {str(e)}")
        return None


def create_chart9(df, cols):
    """
    Create Chart 9: Bar Chart with Text Column Selector
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with numeric_col and text_cols
        
    Returns:
    --------
    altair.Chart and selectbox widget
        Bar chart with numeric value on y-axis and selected text column on x-axis
    """
    try:
        numeric_col = cols.get('numeric_col')
        text_cols = cols.get('text_cols', [])
        
        if not text_cols:
            return None
        
        # Display chart type as normal text
        st.text("Bar Chart with Selectable X-Axis and Color")
        
        # Generate a unique key for this chart based on dataframe and columns
        df_hash = hash(str(df.shape) + str(df.columns.tolist()))
        widget_key = f"chart9_select_{df_hash}"
        color_widget_key = f"chart9_color_select_{df_hash}"
        
        # Initialize the session state value if it doesn't exist
        if widget_key not in st.session_state:
            st.session_state[widget_key] = text_cols[0]
        # If the value exists but is not in text_cols (changed data), reset it
        elif st.session_state[widget_key] not in text_cols:
            st.session_state[widget_key] = text_cols[0]
        
        # Initialize the color selector session state value if it doesn't exist
        if color_widget_key not in st.session_state:
            st.session_state[color_widget_key] = text_cols[0] if len(text_cols) > 0 else None
        # If the value exists but is not in text_cols (changed data), reset it
        elif st.session_state[color_widget_key] not in text_cols:
            st.session_state[color_widget_key] = text_cols[0] if len(text_cols) > 0 else None
        
        # Create columns for the dropdown selectors
        col1, col2 = st.columns(2)
        
        # Get the selected column for x-axis from session state
        with col1:
            selected_text_col = st.selectbox(
                "Select column for X-axis:",
                options=text_cols,
                index=text_cols.index(st.session_state[widget_key]),
                key=widget_key
            )
        
        # Get the selected column for color from session state
        with col2:
            selected_color_col = st.selectbox(
                "Select column for Color:",
                options=text_cols,
                index=text_cols.index(st.session_state[color_widget_key]),
                key=color_widget_key
            )
        
        # Create the bar chart with the selected x-axis column and color column
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{selected_text_col}:N", sort='-y'),
            y=alt.Y(f"{numeric_col}:Q", stack='zero'),
            color=alt.Color(f"{selected_color_col}:N", title=selected_color_col),
            tooltip=[selected_text_col, selected_color_col, numeric_col]
        ).properties(title='')
        
        return chart
    except Exception as e:
        print(f"Error creating Chart 9: {str(e)}")
        return None


def create_chart10(df, cols=None):
    """
    Create Chart 10: KPI Tiles
    
    This chart type is designed for single-row data frames with 1-4 numeric columns.
    It displays each numeric value as a KPI tile using Streamlit's native metric component.
    """
    try:
        # Add debug logging
        print(f"Creating KPI tiles for DataFrame:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Data types:\n{df.dtypes}")
        
        # Check if we have a single row dataframe
        if len(df) != 1:
            st.warning("KPI tiles are designed for single row results only.")
            return None
            
        # Detect numeric columns automatically if not specified in cols
        if cols and 'numeric_cols' in cols:
            numeric_cols = cols.get('numeric_cols')
            print(f"Using specified numeric columns: {numeric_cols}")
            # Get custom labels if provided
            labels = cols.get('labels', {})
        else:
            col_types = detect_column_types(df)
            numeric_cols = col_types['numeric_cols']
            print(f"Auto-detected numeric columns: {numeric_cols}")
            labels = {}
        
        # If no numeric columns, return None
        if not numeric_cols:
            st.warning("No numeric columns found for KPI tiles.")
            return None
        
        # Create a special object to handle both direct rendering and deferred rendering
        # This helps ensure compatibility with both Cortex Analyst and Dashboard
        kpi_data = {
            "type": "kpi_tiles",
            "data": {
                "df": df,
                "numeric_cols": numeric_cols,
                "labels": labels,
                "n_cols": min(len(numeric_cols), 4)
            },
            "render_method": "_render_kpi_tiles"
        }
        
        # Always render KPIs in the Cortex Analyst page
        # This simplifies our approach instead of using frame inspection
        # The frame inspection was causing issues with KPI tiles not showing in Cortex Analyst
        try:
            calling_module = sys._getframe(1).f_globals.get('__name__', '')
            
            # Check if we're being called from display_chart in the Cortex_Analyst page
            # or if we're in a context where we should directly render
            render_directly = (
                'pages.1_Cortex_Analyst' in calling_module or
                'display_chart' in sys._getframe(1).f_code.co_name
            )
            
            if render_directly:
                _render_kpi_tiles(kpi_data["data"])
                # Add a title with normal text size (not heading)
                st.text("KPI Tiles")
        except Exception as e:
            # If there's an error with the frame inspection, fall back to direct rendering
            # This ensures KPIs still show up even if the detection fails
            print(f"Frame inspection error, falling back to direct rendering: {str(e)}")
            _render_kpi_tiles(kpi_data["data"])
            st.text("KPI Tiles")
        
        return kpi_data
    except Exception as e:
        print(f"Error creating Chart 10: {str(e)}")
        return None


def _render_kpi_tiles(data):
    """
    Helper function to render KPI tiles.
    
    Parameters:
    -----------
    data : dict
        Dictionary with data needed for rendering
    """
    df = data["df"]
    numeric_cols = data["numeric_cols"]
    labels = data.get("labels", {})
    n_cols = data.get("n_cols", min(len(numeric_cols), 4))
    
    # Create a layout with the appropriate number of columns
    columns = st.columns(n_cols)
    
    # Add KPI tiles for each numeric column
    for i, col_name in enumerate(numeric_cols[:n_cols]):
        # Get the value for this column
        value = df[col_name].iloc[0]
        
        # Format the value based on its magnitude
        if abs(value) >= 1_000_000:
            formatted_value = f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            formatted_value = f"{value/1_000:.1f}K"
        else:
            formatted_value = f"{value:.1f}"
        
        # Use custom label if provided, otherwise use column name
        label = labels.get(col_name, col_name)
        
        # Display the KPI tile in the appropriate column
        columns[i].metric(
            label=label,
            value=formatted_value
        )
    
    # Return None to indicate this is a direct rendering
    return None


# Utility functions for common chart operations
def detect_column_types(df):
    """
    Automatically detect different column types in a DataFrame
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to analyze
        
    Returns:
    --------
    dict
        Dictionary with categorized columns (date_cols, numeric_cols, text_cols)
    """
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    text_cols = [col for col in df.columns if col not in numeric_cols and col not in date_cols]
    
    return {
        'date_cols': date_cols,
        'numeric_cols': numeric_cols,
        'text_cols': text_cols
    }


def suggest_chart_type(df):
    """
    Analyze a DataFrame and suggest an appropriate chart type
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to analyze
        
    Returns:
    --------
    str
        Suggested chart type based on data structure
    """
    col_types = detect_column_types(df)
    date_cols = col_types['date_cols']
    numeric_cols = col_types['numeric_cols']
    text_cols = col_types['text_cols']
    
    # Chart 1: Single date column, single numeric column
    if len(date_cols) == 1 and len(numeric_cols) == 1 and len(text_cols) == 0:
        return 'chart1'
        
    # Chart 2: Single date column, multiple numeric columns
    elif len(date_cols) == 1 and len(numeric_cols) >= 2 and len(text_cols) == 0:
        return 'chart2'
        
    # Chart 3: Date column, numeric column, and one categorical column
    elif len(date_cols) == 1 and len(numeric_cols) >= 1 and len(text_cols) == 1:
        return 'chart3'
        
    # Chart 4: Date column, numeric column, and multiple categorical columns
    elif len(date_cols) == 1 and len(numeric_cols) >= 1 and len(text_cols) >= 2:
        return 'chart4'
        
    # Default to generic bar chart
    return 'bar'


def generate_chart_code_for_dataframe(df):
    """
    Generate chart code for a dataframe based on its chart_metadata.
    This centralizes chart code generation to avoid duplication across pages.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with chart_metadata attribute containing chart configuration
        
    Returns:
    --------
    str
        The generated chart code as a string
    """
    import io
    buf = io.StringIO()
    print("import altair as alt", file=buf)
    print("import pandas as pd", file=buf)
    print("import streamlit as st", file=buf)
    print("\n# Chart code", file=buf)
    print("def create_chart(df):", file=buf)
    
    # Determine which chart type we have based on metadata and generate appropriate code
    if hasattr(df, 'attrs') and 'chart_metadata' in df.attrs:
        chart_metadata = df.attrs['chart_metadata']
        
        if 'chart10_columns' in chart_metadata:
            cols = chart_metadata['chart10_columns']
            numeric_cols = cols.get('numeric_cols', [])
            
            if not numeric_cols:
                print(f"    # Error: Missing required columns for chart10", file=buf)
                print(f"    st.error('Missing required columns for KPI Tiles')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # KPI Tiles - uses Streamlit native components", file=buf)
                print(f"    if len(df) != 1:", file=buf)
                print(f"        st.warning('KPI tiles are designed for single row results only.')", file=buf)
                print(f"        return None", file=buf)
                print(f"", file=buf)
                print(f"    # Get the number of columns to display (maximum 4)", file=buf)
                print(f"    numeric_cols = {numeric_cols}", file=buf)
                print(f"    n_cols = min(len(numeric_cols), 4)", file=buf)
                print(f"", file=buf)
                print(f"    # Create columns for the KPI layout", file=buf)
                print(f"    columns = st.columns(n_cols)", file=buf)
                print(f"", file=buf)
                print(f"    # Display each KPI in its own column", file=buf)
                print(f"    for i, col_name in enumerate(numeric_cols[:n_cols]):", file=buf)
                print(f"        # Get the value", file=buf)
                print(f"        value = df[col_name].iloc[0]", file=buf)
                print(f"", file=buf)
                print(f"        # Format based on magnitude", file=buf)
                print(f"        if abs(value) >= 1_000_000:", file=buf)
                print(f"            formatted_value = f\"{{value/1_000_000:.1f}}M\"", file=buf)
                print(f"        elif abs(value) >= 1_000:", file=buf)
                print(f"            formatted_value = f\"{{value/1_000:.1f}}K\"", file=buf)
                print(f"        else:", file=buf)
                print(f"            formatted_value = f\"{{value:.1f}}\"", file=buf)
                print(f"", file=buf)
                print(f"        # Display the metric", file=buf)
                print(f"        columns[i].metric(", file=buf)
                print(f"            label=col_name,", file=buf)
                print(f"            value=formatted_value", file=buf)
                print(f"        )", file=buf)
                print(f"", file=buf)
                print(f"    # Add a title for the KPI section", file=buf)
                print(f"    st.markdown('### KPI Tiles')", file=buf)
                print(f"", file=buf)
                print(f"    # Return None as we've rendered the components directly", file=buf)
                print(f"    return None", file=buf)
                
        elif 'chart1_columns' in chart_metadata:
            cols = chart_metadata['chart1_columns']
            date_col = cols.get('date_col')
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not numeric_col:
                print(f"    # Error: Missing required columns for chart1", file=buf)
                print(f"    st.error('Missing required columns for Bar Chart by Date')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q'),", file=buf)
                print(f"        tooltip=['{date_col}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Bar Chart by Date')", file=buf)
            
        elif 'chart2_columns' in chart_metadata:
            cols = chart_metadata['chart2_columns']
            date_col = cols.get('date_col')
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            
            if not date_col or not num_col1 or not num_col2:
                print(f"    # Error: Missing required columns for chart2", file=buf)
                print(f"    st.error('Missing required columns for Dual Axis Line Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    base = alt.Chart(df).encode(x=alt.X('{date_col}:T', sort='ascending'))", file=buf)
                print(f"    line1 = base.mark_line(color='blue').encode(", file=buf)
                print(f"        y=alt.Y('{num_col1}:Q', axis=alt.Axis(title='{num_col1}')),", file=buf)
                print(f"        tooltip=['{date_col}', '{num_col1}']", file=buf)
                print(f"    )", file=buf)
                print(f"    line2 = base.mark_line(color='red').encode(", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q', axis=alt.Axis(title='{num_col2}')),", file=buf)
                print(f"        tooltip=['{date_col}', '{num_col2}']", file=buf)
                print(f"    )", file=buf)
                print(f"    return alt.layer(line1, line2).resolve_scale(", file=buf)
                print(f"        y='independent'", file=buf)
                print(f"    ).properties(title='Dual Axis Line Chart')", file=buf)
        
        elif 'chart3_columns' in chart_metadata:
            cols = chart_metadata['chart3_columns']
            date_col = cols.get('date_col')
            text_col = cols.get('text_col')
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not text_col or not numeric_col:
                print(f"    # Error: Missing required columns for chart3", file=buf)
                print(f"    st.error('Missing required columns for Stacked Bar Chart by Date')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q', stack='zero'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{date_col}', '{text_col}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Stacked Bar Chart by Date')", file=buf)
        
        elif 'chart4_columns' in chart_metadata:
            cols = chart_metadata['chart4_columns']
            date_col = cols.get('date_col')
            text_cols = cols.get('text_cols', [])
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not text_cols or not numeric_col or len(text_cols) < 2:
                print(f"    # Error: Missing required columns for chart4", file=buf)
                print(f"    st.error('Missing required columns for Stacked Bar Chart with Text Column Selector for Colors')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # Generate a unique key for this chart based on dataframe and columns", file=buf)
                print(f"    df_hash = hash(str(df.shape) + str(df.columns.tolist()))", file=buf)
                print(f"    widget_key = f\"chart4_select_{{df_hash}}\"", file=buf)
                print(f"", file=buf)
                print(f"    # Initialize the session state value if it doesn't exist", file=buf)
                print(f"    if widget_key not in st.session_state:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"    # If the value exists but is not in text_cols (changed data), reset it", file=buf)
                print(f"    elif st.session_state[widget_key] not in {text_cols}:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Get the selected column from session state", file=buf)
                print(f"    selected_text_col = st.selectbox(", file=buf)
                print(f"        \"Select column for color grouping:\",", file=buf)
                print(f"        options={text_cols},", file=buf)
                print(f"        index={text_cols}.index(st.session_state[widget_key]),", file=buf)
                print(f"        key=widget_key", file=buf)
                print(f"    )", file=buf)
                print(f"", file=buf)
                print(f"    # Create the chart with the selected text column", file=buf)
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q', stack='zero'),", file=buf)
                print(f"        color=alt.Color('{{selected_text_col}}:N', title='{{selected_text_col}}'),", file=buf)
                print(f"        tooltip=['{date_col}', '{{selected_text_col}}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Stacked Bar Chart with Selectable Colors')", file=buf)
        
        elif 'chart5_columns' in chart_metadata:
            cols = chart_metadata['chart5_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            text_col = cols.get('text_col')
            
            if not num_col1 or not num_col2 or not text_col:
                print(f"    # Error: Missing required columns for chart5", file=buf)
                print(f"    st.error('Missing required columns for Scatter Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_circle(size=60).encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{num_col1}', '{num_col2}', '{text_col}']", file=buf)
                print(f"    ).properties(title='Scatter Plot')", file=buf)
        
        elif 'chart6_columns' in chart_metadata:
            cols = chart_metadata['chart6_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            text_col1 = cols.get('text_col1')
            text_col2 = cols.get('text_col2')
            
            if not num_col1 or not num_col2 or not text_col1 or not text_col2:
                print(f"    # Error: Missing required columns for chart6", file=buf)
                print(f"    st.error('Missing required columns for Scatter Chart with Multiple Dimensions')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_point(size=100).encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col1}:N'),", file=buf)
                print(f"        shape=alt.Shape('{text_col2}:N', scale=alt.Scale(", file=buf)
                print(f"            range=[\"circle\", \"square\", \"cross\", \"diamond\", \"triangle-up\", \"triangle-down\", ", file=buf)
                print(f"                   \"triangle-right\", \"triangle-left\", \"arrow\", \"wedge\", \"stroke\"]", file=buf)
                print(f"        )),", file=buf)
                print(f"        tooltip=['{text_col1}', '{text_col2}', '{num_col1}', '{num_col2}']", file=buf)
                print(f"    ).properties(title='Scatter Chart with Multiple Dimensions')", file=buf)
        
        elif 'chart7_columns' in chart_metadata:
            cols = chart_metadata['chart7_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            num_col3 = cols.get('num_col3')
            text_col = cols.get('text_col')
            
            if not num_col1 or not num_col2 or not num_col3 or not text_col:
                print(f"    # Error: Missing required columns for chart7", file=buf)
                print(f"    st.error('Missing required columns for Bubble Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_circle().encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        size=alt.Size('{num_col3}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{num_col1}', '{num_col2}', '{num_col3}', '{text_col}']", file=buf)
                print(f"    ).properties(title='Bubble Chart')", file=buf)
        
        elif 'chart8_columns' in chart_metadata:
            cols = chart_metadata['chart8_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            num_col3 = cols.get('num_col3')
            text_col1 = cols.get('text_col1')
            text_col2 = cols.get('text_col2')
            
            if not num_col1 or not num_col2 or not num_col3 or not text_col1 or not text_col2:
                print(f"    # Error: Missing required columns for chart8", file=buf)
                print(f"    st.error('Missing required columns for Multi-Dimensional Bubble Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_point().encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        size=alt.Size('{num_col3}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col1}:N'),", file=buf)
                print(f"        shape=alt.Shape('{text_col2}:N', scale=alt.Scale(", file=buf)
                print(f"            range=[\"circle\", \"square\", \"cross\", \"diamond\", \"triangle-up\", \"triangle-down\", ", file=buf)
                print(f"                   \"triangle-right\", \"triangle-left\", \"arrow\", \"wedge\", \"stroke\"]", file=buf)
                print(f"        )),", file=buf)
                print(f"        tooltip=['{text_col1}', '{text_col2}', '{num_col1}', '{num_col2}', '{num_col3}']", file=buf)
                print(f"    ).properties(title='Multi-Dimensional Bubble Chart')", file=buf)
        
        elif 'chart9_columns' in chart_metadata:
            cols = chart_metadata['chart9_columns']
            numeric_col = cols.get('numeric_col')
            text_cols = cols.get('text_cols', [])
            
            if not numeric_col or not text_cols or len(text_cols) == 0:
                print(f"    # Error: Missing required columns for chart9", file=buf)
                print(f"    st.error('Missing required columns for Bar Chart with Text Column Selector')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # Generate a unique key for this chart based on dataframe and columns", file=buf)
                print(f"    df_hash = hash(str(df.shape) + str(df.columns.tolist()))", file=buf)
                print(f"    widget_key = f\"chart9_select_{{df_hash}}\"", file=buf)
                print(f"    color_widget_key = f\"chart9_color_select_{{df_hash}}\"", file=buf)
                print(f"", file=buf)
                print(f"    # Initialize the session state value if it doesn't exist", file=buf)
                print(f"    if widget_key not in st.session_state:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"    # If the value exists but is not in text_cols (changed data), reset it", file=buf)
                print(f"    elif st.session_state[widget_key] not in {text_cols}:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Initialize the color selector session state value if it doesn't exist", file=buf)
                print(f"    if color_widget_key not in st.session_state:", file=buf)
                print(f"        st.session_state[color_widget_key] = {text_cols}[0]", file=buf)
                print(f"    # If the value exists but is not in text_cols (changed data), reset it", file=buf)
                print(f"    elif st.session_state[color_widget_key] not in {text_cols}:", file=buf)
                print(f"        st.session_state[color_widget_key] = {text_cols}[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Create columns for the dropdown selectors", file=buf)
                print(f"    col1, col2 = st.columns(2)", file=buf)
                print(f"", file=buf)
                print(f"    # Get the selected column for x-axis from session state", file=buf)
                print(f"    with col1:", file=buf)
                print(f"        selected_text_col = st.selectbox(", file=buf)
                print(f"            \"Select column for X-axis:\",", file=buf)
                print(f"            options={text_cols},", file=buf)
                print(f"            index={text_cols}.index(st.session_state[widget_key]),", file=buf)
                print(f"            key=widget_key", file=buf)
                print(f"        )", file=buf)
                print(f"", file=buf)
                print(f"    # Get the selected column for color from session state", file=buf)
                print(f"    with col2:", file=buf)
                print(f"        selected_color_col = st.selectbox(", file=buf)
                print(f"            \"Select column for Color:\",", file=buf)
                print(f"            options={text_cols},", file=buf)
                print(f"            index={text_cols}.index(st.session_state[color_widget_key]),", file=buf)
                print(f"            key=color_widget_key", file=buf)
                print(f"        )", file=buf)
                print(f"", file=buf)
                print(f"    # Create the bar chart with the selected text column and color column", file=buf)
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X(f\"{{selected_text_col}}:N\", sort='-y'),", file=buf)
                print(f"        y=alt.Y(f\"{numeric_col}:Q\", stack='zero'),", file=buf)
                print(f"        color=alt.Color(f\"{{selected_color_col}}:N\", title=selected_color_col),", file=buf)
                print(f"        tooltip=[selected_text_col, selected_color_col, '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Bar Chart with Selectable X-Axis and Color')", file=buf)
        
        elif 'chart11_columns' in chart_metadata:
            cols = chart_metadata['chart11_columns']
            lat_col = cols.get('lat_col')
            lon_col = cols.get('lon_col')
            value_col = cols.get('value_col')
            
            if not lat_col or not lon_col:
                print(f"    # Error: Missing required columns for chart11", file=buf)
                print(f"    st.error('Missing required columns for Geospatial Map')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # Import required libraries for geospatial visualization", file=buf)
                print(f"    import pydeck as pdk", file=buf)
                print(f"    import numpy as np", file=buf)
                print(f"    import h3", file=buf)
                print(f"    import branca.colormap as cm", file=buf)
                print(f"", file=buf)
                print(f"    # Prepare data for visualization", file=buf)
                print(f"    from utils.chart_utils import prepare_geospatial_data, create_h3_layer", file=buf)
                print(f"", file=buf)
                print(f"    # Find all available numeric columns (excluding lat/lon columns)", file=buf)
                print(f"    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])", file=buf)
                print(f"                 and col != '{lat_col}' and col != '{lon_col}']", file=buf)
                print(f"", file=buf)
                print(f"    # Handle case with no numeric columns", file=buf)
                print(f"    if not numeric_cols:", file=buf)
                print(f"        df['value'] = 1", file=buf)
                print(f"        numeric_cols = ['value']", file=buf)
                print(f"        value_col = 'value'", file=buf)
                print(f"    else:", file=buf)
                print(f"        # Set default value column", file=buf)
                print(f"        value_col = {repr(value_col) if value_col else 'None'}", file=buf)
                print(f"        if not value_col or value_col not in numeric_cols:", file=buf)
                print(f"            value_col = numeric_cols[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Create a dropdown for metric selection if multiple numeric columns exist", file=buf)
                print(f"    if len(numeric_cols) > 1:", file=buf)
                print(f"        # Generate a unique key for this dropdown", file=buf)
                print(f"        df_hash = hash(str(df.shape) + str(df.columns.tolist()))", file=buf)
                print(f"        dropdown_key = f'chart11_value_select_{{df_hash}}'", file=buf)
                print(f"", file=buf)
                print(f"        # Create the dropdown", file=buf)
                print(f"        selected_value_col = st.selectbox(", file=buf)
                print(f"            'Select metric to visualize:',", file=buf)
                print(f"            options=numeric_cols,", file=buf)
                print(f"            index=numeric_cols.index(value_col) if value_col in numeric_cols else 0,", file=buf)
                print(f"            key=dropdown_key", file=buf)
                print(f"        )", file=buf)
                print(f"        value_col = selected_value_col", file=buf)
                print(f"    ", file=buf)
                print(f"", file=buf)
                print(f"", file=buf)
                print(f"    # Prepare the geospatial data", file=buf)
                print(f"    h3_df = prepare_geospatial_data(df, '{lat_col}', '{lon_col}', value_col, resolution=6)", file=buf)
                print(f"", file=buf)
                print(f"    if h3_df.empty:", file=buf)
                print(f"        st.error('No valid data points for map visualization.')", file=buf)
                print(f"        return None", file=buf)
                print(f"", file=buf)
                print(f"    # Create map layer", file=buf)
                print(f"    layer = create_h3_layer(h3_df)", file=buf)
                print(f"", file=buf)
                print(f"    if layer is None:", file=buf)
                print(f"        st.error('Could not create map layer.')", file=buf)
                print(f"        return None", file=buf)
                print(f"", file=buf)
                print(f"    # Calculate map center", file=buf)
                print(f"    center_lat = df['{lat_col}'].mean()", file=buf)
                print(f"    center_lon = df['{lon_col}'].mean()", file=buf)
                print(f"", file=buf)
                print(f"    # Create the map", file=buf)
                print(f"    deck = pdk.Deck(", file=buf)
                print(f"        map_style='mapbox://styles/mapbox/light-v9',", file=buf)
                print(f"        initial_view_state=pdk.ViewState(", file=buf)
                print(f"            latitude=center_lat,", file=buf)
                print(f"            longitude=center_lon,", file=buf)
                print(f"            zoom=6,", file=buf)
                print(f"            pitch=0,", file=buf)
                print(f"            bearing=0", file=buf)
                print(f"        ),", file=buf)
                print(f"        layers=[layer],", file=buf)
                print(f"        tooltip={{", file=buf)
                print(f"            'html': f'<b>Value:</b> {{{{value}}}}<br><b>Count:</b> {{{{count}}}}',", file=buf)
                print(f"            'style': {{'backgroundColor': 'steelblue', 'color': 'white'}}", file=buf)
                print(f"        }}", file=buf)
                print(f"    )", file=buf)
                print(f"", file=buf)
                print(f"    return deck", file=buf)
        
        else:
            # No specific chart type identified in metadata
            print(f"    # No chart type identified in metadata", file=buf)
            print(f"    st.error('No valid chart type found in metadata. Please provide chart configuration.')", file=buf)
            print(f"    return None", file=buf)
    else:
        # No chart metadata
        print(f"    # No chart metadata available", file=buf)
        print(f"    st.error('No chart metadata available. Please provide chart configuration.')", file=buf)
        print(f"    return None", file=buf)
    
    # Return the generated code
    return buf.getvalue()

# Helper functions for geospatial visualization
def get_quantiles(df_column, num_quantiles=20):
    """
    Get quantiles for a dataframe column to use in colormap.
    
    Parameters:
    -----------
    df_column : pandas.Series
        Column with numeric values
    num_quantiles : int, optional
        Number of quantiles to generate
        
    Returns:
    --------
    numpy.ndarray
        Array of quantile values
    """
    try:
        # Check for problematic values
        has_inf = np.isinf(df_column).any()
        has_nan = np.isnan(df_column).any()
        
        if has_inf or has_nan:
            # Clean the data
            df_column = df_column.replace([np.inf, -np.inf], np.nan).dropna()
            if df_column.empty:
                raise ValueError("No valid data points after removing inf/NaN values")
        
        # Check if we have enough unique values to create meaningful quantiles
        unique_values = df_column.nunique()
        
        if unique_values <= 1:
            # If only one unique value, create a simple two-point scale around that value
            value = df_column.iloc[0]
            # Create a small range around the value to ensure color variation
            if value == 0:
                return np.array([-0.01, 0, 0.01])
            else:
                low = value * 0.95 if value > 0 else value * 1.05
                high = value * 1.05 if value > 0 else value * 0.95
                return np.array([low, value, high])
        
        # If enough unique values, generate proper quantiles
        # Use fewer quantiles if there are fewer unique values, but ensure at least 3
        if unique_values < num_quantiles:
            # Adjust quantiles based on unique values, but keep at least 3 for good color range
            adjusted_quantiles = max(min(unique_values, 5), 3)
            
            # Use numpy linspace directly for more control
            points = np.linspace(0, 1, adjusted_quantiles)
            try:
                result = np.array([df_column.quantile(p) for p in points])
                return result
            except Exception:
                # If quantile method fails, fall back to min/max/median approach
                return np.array([df_column.min(), df_column.median(), df_column.max()])
        
        # Normal case - enough unique values for full quantile range
        try:
            result = df_column.quantile(np.linspace(0, 1, num_quantiles + 1))
            return result
        except Exception:
            # If quantile method fails, fall back to evenly spaced range
            min_val = df_column.min()
            max_val = df_column.max()
            return np.linspace(min_val, max_val, num_quantiles + 1)
    except Exception:
        # Ultimate fallback: create a simple range 
        try:
            min_val = float(df_column.min())
            max_val = float(df_column.max())
            if min_val == max_val:
                # Create a range around the single value
                if min_val == 0:
                    return np.array([-0.1, 0, 0.1])
                else:
                    return np.array([min_val * 0.9, min_val, min_val * 1.1])
            else:
                mid_val = (min_val + max_val) / 2
                return np.array([min_val, mid_val, max_val])
        except Exception:
            # Last resort - just use a fixed range
            return np.array([0, 50, 100])

@st.cache_data(ttl=1)  # Short TTL to ensure fresh colors when color schemes change
def calculate_rgba_color(df_column, colors_hex_list, quantiles, opacity=0.8, reverse=False):
    """
    Calculate RGBA colors for values based on quantiles and a colormap.
    
    Parameters:
    -----------
    df_column : pandas.Series
        Column with numeric values
    colors_hex_list : list
        List of hex color values for the colormap
    quantiles : numpy.ndarray
        Array of quantile values
    opacity : float, optional
        Opacity for the colors (0-1)
    reverse : bool, optional
        Whether to reverse the color order
        
    Returns:
    --------
    list
        List of RGBA color arrays for each value
    """
    try:
        if reverse:
            colors_hex_list = colors_hex_list[::-1]
        
        # Sanity check for valid quantiles
        if len(quantiles) < 2:
            min_val = float(quantiles[0])
            quantiles = np.array([min_val * 0.9 if min_val != 0 else -0.1, 
                                 min_val, 
                                 min_val * 1.1 if min_val != 0 else 0.1])
            
        # Try different color mapping approaches
        try:
            # First try: Use branca's LinearColormap
            colormap = cm.LinearColormap(colors_hex_list, vmin=float(quantiles.min()), vmax=float(quantiles.max()))
            
            rgba_colors = []
            for val in df_column:
                if pd.isna(val):
                    rgba_colors.append([0, 0, 0, 0])  # Transparent for NaNs
                    continue
                
                # Clamp value to min/max range to prevent out-of-range errors
                safe_val = max(min(float(val), float(quantiles.max())), float(quantiles.min()))
                
                # Get color for this value
                rgb_hex = colormap(safe_val)  # Gets hex string like #RRGGBB
                r = int(rgb_hex[1:3], 16)
                g = int(rgb_hex[3:5], 16)
                b = int(rgb_hex[5:7], 16)
                rgba_colors.append([r, g, b, int(opacity * 255)])
            
            return rgba_colors
        
        except Exception:
            # Second try: Manual color interpolation with matplotlib
            try:
                import matplotlib.colors as mcolors
                import matplotlib.cm as mcm
                
                # Create a simple colormap using matplotlib
                cmap = mcm.get_cmap('Blues')
                
                # Normalize the values
                min_val = float(quantiles.min())
                max_val = float(quantiles.max())
                range_val = max_val - min_val
                
                if range_val == 0:
                    range_val = 1.0  # Prevent division by zero
                
                rgba_colors = []
                for val in df_column:
                    if pd.isna(val):
                        rgba_colors.append([0, 0, 0, 0])  # Transparent for NaNs
                        continue
                    
                    # Normalize to 0-1 range
                    norm_val = (float(val) - min_val) / range_val
                    norm_val = max(0.0, min(1.0, norm_val))  # Clamp to 0-1
                    
                    # Get color from matplotlib colormap
                    rgba = cmap(norm_val)
                    rgba_colors.append([int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255), int(opacity * 255)])
                
                return rgba_colors
                
            except Exception:
                # Third try: Simple linear gradient between two colors
                try:
                    # Parse hex colors to RGB
                    def hex_to_rgb(hex_color):
                        hex_color = hex_color.lstrip('#')
                        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    
                    start_rgb = hex_to_rgb(colors_hex_list[0])
                    end_rgb = hex_to_rgb(colors_hex_list[-1])
                    
                    # Normalize and interpolate
                    min_val = float(quantiles.min())
                    max_val = float(quantiles.max())
                    range_val = max_val - min_val
                    
                    if range_val == 0:
                        range_val = 1.0  # Prevent division by zero
                    
                    rgba_colors = []
                    for val in df_column:
                        if pd.isna(val):
                            rgba_colors.append([0, 0, 0, 0])  # Transparent for NaNs
                            continue
                        
                        # Normalize and clamp to 0-1
                        t = (float(val) - min_val) / range_val
                        t = max(0.0, min(1.0, t))
                        
                        # Linear interpolation
                        r = int(start_rgb[0] * (1-t) + end_rgb[0] * t)
                        g = int(start_rgb[1] * (1-t) + end_rgb[1] * t)
                        b = int(start_rgb[2] * (1-t) + end_rgb[2] * t)
                        
                        rgba_colors.append([r, g, b, int(opacity * 255)])
                    
                    return rgba_colors
                    
                except Exception:
                    pass  # Fall through to default color
    except Exception:
        pass  # Fall through to default color
    
    # Last resort: use a single color for all points
    color_hex = colors_hex_list[len(colors_hex_list) // 2]
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    a = int(opacity * 255)
    return [[r, g, b, a] for _ in range(len(df_column))]

def prepare_geospatial_data(df, lat_col, lon_col, value_col, resolution=6, color_scheme="White-Blue", opacity=0.8):
    """
    Prepare dataframe for H3 hexagon map visualization.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with geospatial data
    lat_col : str
        Name of latitude column
    lon_col : str
        Name of longitude column
    value_col : str
        Name of value column to visualize
    resolution : int, optional
        H3 resolution (4-11, higher is more detailed)
    color_scheme : str, optional
        Color scheme to use (must be a key in GEOSPATIAL_COLORS)
    opacity : float, optional
        Opacity for colors (0-1)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with H3 indices and prepared for visualization
    """
    try:
        # Check input parameters
        debug_info = {
            "input_shape": df.shape,
            "columns": df.columns.tolist(),
            "lat_col": lat_col,
            "lon_col": lon_col,
            "value_col": value_col,
            "missing_cols": [],
            "color_scheme": color_scheme,
            "opacity": opacity
        }
        
        # Check for missing columns
        for col in [lat_col, lon_col, value_col]:
            if col not in df.columns:
                debug_info["missing_cols"].append(col)
        
        if debug_info["missing_cols"]:
            return pd.DataFrame(), debug_info
        
        if df.empty:
            debug_info["error"] = "Empty dataframe"
            return pd.DataFrame(), debug_info
        
        # Try importing h3 and branca here to handle any import errors
        try:
            import h3
            import branca.colormap as cm
        except ImportError as e:
            debug_info["error"] = f"Error importing geospatial libraries: {str(e)}"
            return pd.DataFrame(), debug_info
        
        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        
        debug_info["original_rows"] = len(df_copy)
        
        # Convert to numeric if needed
        nan_counts = {}
        for col in [lat_col, lon_col, value_col]:
            if col in df_copy.columns:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                nan_counts[col] = df_copy[col].isna().sum()
        
        debug_info["nan_counts"] = nan_counts
        
        # Drop rows with NaN values in required columns
        original_len = len(df_copy)
        df_copy = df_copy.dropna(subset=[lat_col, lon_col, value_col])
        dropped_rows = original_len - len(df_copy)
        debug_info["dropped_nan_rows"] = dropped_rows
        
        if df_copy.empty:
            debug_info["error"] = "All rows contained NaN values in required columns"
            return pd.DataFrame(), debug_info
        
        # Check for valid coordinates
        invalid_lat = ((df_copy[lat_col] < -90) | (df_copy[lat_col] > 90)).sum()
        invalid_lon = ((df_copy[lon_col] < -180) | (df_copy[lon_col] > 180)).sum()
        
        debug_info["invalid_lat"] = invalid_lat
        debug_info["invalid_lon"] = invalid_lon
        
        if invalid_lat > 0 or invalid_lon > 0:
            # Filter out rows with invalid coordinates
            df_copy = df_copy[(df_copy[lat_col] >= -90) & (df_copy[lat_col] <= 90) & 
                             (df_copy[lon_col] >= -180) & (df_copy[lon_col] <= 180)]
            debug_info["rows_after_coord_filter"] = len(df_copy)
            
            if df_copy.empty:
                debug_info["error"] = "All coordinates were invalid"
                return pd.DataFrame(), debug_info
        
        # Generate H3 indices
        try:
            df_copy['h3_index'] = df_copy.apply(
                lambda row: h3.geo_to_h3(float(row[lat_col]), float(row[lon_col]), resolution),
                axis=1
            )
            debug_info["h3_indices_generated"] = True
        except Exception as e:
            debug_info["error"] = f"Error generating H3 indices: {str(e)}"
            return pd.DataFrame(), debug_info
        
        # Aggregate by H3 index
        try:
            agg_df = df_copy.groupby('h3_index').agg({
                value_col: 'mean',
                lat_col: 'mean',
                lon_col: 'mean'
            }).reset_index()
            
            debug_info["hexagon_count"] = len(agg_df)
            
            # Add count of points per hexagon for tooltip
            counts = df_copy.groupby('h3_index').size().reset_index(name='count')
            agg_df = pd.merge(agg_df, counts, on='h3_index')
            
            # Check if we have enough data points for visualization
            if len(agg_df) < 2:
                debug_info["warning"] = f"Only {len(agg_df)} data points after aggregation"
            
        except Exception as e:
            debug_info["error"] = f"Error during H3 aggregation: {str(e)}"
            return pd.DataFrame(), debug_info
        
        # Calculate quantiles and colors
        try:
            # Check for sufficient variation in the data
            unique_values = agg_df[value_col].nunique()
            value_min = agg_df[value_col].min()
            value_max = agg_df[value_col].max()
            
            debug_info["unique_values"] = unique_values
            debug_info["value_range"] = [value_min, value_max]
            
            # Select the color scheme based on input parameter or default logic
            if color_scheme in GEOSPATIAL_COLORS:
                colors = GEOSPATIAL_COLORS[color_scheme]
                debug_info["color_scheme_used"] = color_scheme
            else:
                # Fallback logic if the requested scheme doesn't exist
                if value_min < 0 and value_max > 0:
                    # Use divergent scheme when values include both negative and positive
                    colors = GEOSPATIAL_COLORS["Yellow-Blue"]
                    debug_info["color_scheme_used"] = "Yellow-Blue (fallback)"
                else:
                    # Use standard scheme for all positive or all negative values
                    colors = GEOSPATIAL_COLORS["White-Blue"]  # Default color scheme
                    debug_info["color_scheme_used"] = "White-Blue (fallback)"
            
            # Get appropriate quantiles
            try:
                quantiles = get_quantiles(agg_df[value_col])
                
                # Calculate colors with a unique key to prevent caching conflicts
                unique_key = f"{value_col}_{str(colors)[:20]}_{str(quantiles)[:20]}_{time.time()}"
                
                # Use the provided opacity value
                agg_df['rgba_color'] = calculate_rgba_color(agg_df[value_col], colors, quantiles, opacity)
                debug_info["colors_calculated"] = True
            except Exception as e:
                # Emergency fallback - assign a default color
                default_color = [100, 149, 237, int(opacity * 255)]  # Cornflower blue with given opacity
                agg_df['rgba_color'] = [default_color] * len(agg_df)
                debug_info["warning"] = f"Using default color due to quantile error: {str(e)}"
        except Exception as e:
            debug_info["error"] = f"Error in color calculation: {str(e)}"
            
            # Try one last emergency approach
            try:
                # Assign default colors without any calculations
                default_color = [100, 149, 237, int(opacity * 255)]  # Cornflower blue with given opacity
                agg_df['rgba_color'] = [default_color] * len(agg_df)
                return agg_df, debug_info
            except:
                # If even this fails, we have to give up
                return pd.DataFrame(), debug_info
        
        # Additional metadata for tooltips
        agg_df['metric_name'] = value_col
        agg_df['aggregated_value_display'] = agg_df[value_col].round(2).astype(str)
        
        return agg_df, debug_info
    except Exception as e:
        return pd.DataFrame(), {"error": str(e)}

def create_h3_layer(df, get_color_column='rgba_color', elevation_column=None, elevation_scale=1):
    """
    Create an H3 hexagon layer for pydeck.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with H3 indices and colors
    get_color_column : str, optional
        Column containing RGBA color values
    elevation_column : str, optional
        Column to use for hexagon height (3D)
    elevation_scale : float, optional
        Multiplier for elevation values
        
    Returns:
    --------
    pydeck.Layer
        H3HexagonLayer for rendering on a map
    """
    try:
        # Try importing pydeck here to handle any import errors
        try:
            import pydeck as pdk
            print("Successfully imported pydeck in create_h3_layer")
        except ImportError as e:
            print(f"Error importing pydeck in create_h3_layer: {str(e)}")
            return None
            
        print(f"Creating H3 layer with {len(df)} hexagons")
        print(f"Using color column: {get_color_column}")
        print(f"Using elevation column: {elevation_column}")
        
        return pdk.Layer(
            "H3HexagonLayer",
            data=df,
            pickable=True,
            stroked=True,
            filled=True,
            extruded=elevation_column is not None,
            get_hexagon="h3_index",
            get_fill_color=get_color_column,
            get_elevation=elevation_column if elevation_column else 0,
            elevation_scale=elevation_scale if elevation_column else 0
        )
    except Exception as e:
        print(f"Error in create_h3_layer: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def create_chart11(df, cols):
    """
    Create Chart 11: Geospatial Map
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with latitude and longitude data
    cols : dict
        Column configuration with lat_col, lon_col, and various visualization settings
        
    Returns:
    --------
    pydeck.Deck
        Interactive 3D map visualization
    """
    try:
        # Display chart type as normal text
        st.text("Geospatial Map")
        
        # Extract basic columns
        lat_col = cols.get('lat_col')
        lon_col = cols.get('lon_col')
        
        # Get advanced settings from Map Designer
        value_cols = cols.get('value_cols', [])  # Multiple metrics
        height_metric = cols.get('height_metric')  # Which metric controls height
        height_multiplier = cols.get('height_multiplier', 100)  # Height multiplier
        normalize_heights = cols.get('normalize_heights', True)  # Normalize heights
        color_schemes = cols.get('color_schemes', {})  # Color schemes per metric
        metric_settings = cols.get('metric_settings', {})  # Per-metric settings
        
        # Check if columns exist in dataframe
        missing_cols = []
        for col_name, col_type in [(lat_col, 'latitude'), (lon_col, 'longitude')]:
            if col_name not in df.columns:
                st.error(f"{col_type.capitalize()} column '{col_name}' not found in data")
                missing_cols.append(col_name)
        
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            return None
        
        # Handle case when no value_cols are specified
        if not value_cols:
            # Find all available numeric columns (excluding lat/lon columns)
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])
                          and col != lat_col and col != lon_col]
            
            # If no numeric columns found, create a default one
            if not numeric_cols:
                df = df.copy()
                df['value'] = 1
                numeric_cols = ['value']
                value_cols = ['value']
                st.warning("No numeric columns found, created default 'value' column")
            else:
                value_cols = [numeric_cols[0]]  # Use the first numeric column
        
        # Create a dropdown for user to select which numeric column to visualize if only 1 is specified
        # For multiple metrics, we use the preselected value_cols from the saved settings
        if len(value_cols) == 1:
            # Find all available numeric columns for dropdown
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])
                          and col != lat_col and col != lon_col]
            
            # Generate a unique key for this dropdown
            df_hash = hash(str(df.shape) + str(df.columns.tolist()))
            dropdown_key = f"chart11_value_select_{df_hash}"
            
            # Show dropdown only if there are multiple numeric columns
            if len(numeric_cols) > 1:
                selected_value_col = st.selectbox(
                    "Select metric to visualize:",
                    options=numeric_cols,
                    index=numeric_cols.index(value_cols[0]) if value_cols[0] in numeric_cols else 0,
                    key=dropdown_key
                )
                value_cols = [selected_value_col]
        
        # Import required libraries for geospatial visualization
        try:
            import pydeck as pdk
            import h3
            import branca.colormap as cm
            import numpy as np
        except ImportError as e:
            st.error(f"Error importing map libraries: {str(e)}")
            return None
        
        # Make a copy of the dataframe to avoid modifying the original
        df_copy = df.copy()
        
        # Ensure all selected value_cols are numeric
        for value_col in value_cols:
            try:
                if value_col in df_copy.columns:
                    df_copy[value_col] = pd.to_numeric(df_copy[value_col], errors='coerce')
                    nan_count = df_copy[value_col].isna().sum()
                    if nan_count > 0:
                        st.warning(f"Column {value_col} has {nan_count} NaN values after conversion")
                else:
                    st.error(f"Selected value column '{value_col}' not found in dataframe")
                    value_cols.remove(value_col)
            except Exception as e:
                st.error(f"Error converting {value_col} to numeric: {str(e)}")
                value_cols.remove(value_col)
        
        # If no valid metrics remain, return None
        if not value_cols:
            st.error("No valid metrics available for visualization")
            return None
        
        # Prepare data for each metric
        metric_data = {}
        center_lat = df_copy[lat_col].mean()
        center_lon = df_copy[lon_col].mean()
        
        for metric in value_cols:
            # Get metric-specific settings
            settings = metric_settings.get(metric, {})
            resolution = settings.get("resolution", 6)
            opacity = settings.get("opacity", 0.75)
            color_scheme = settings.get("color_scheme", color_schemes.get(metric, "White-Blue"))
            
            # Prepare H3 data for this metric with error handling
            try:
                # First try with all parameters
                h3_df, debug_info = prepare_geospatial_data(
                    df_copy, 
                    lat_col, 
                    lon_col, 
                    metric, 
                    resolution=resolution,
                    color_scheme=color_scheme,
                    opacity=opacity
                )
            except TypeError as e:
                error_msg = str(e)
                # Fallback to version without color_scheme parameter
                if "color_scheme" in error_msg:
                    try:
                        # Try with just opacity
                        h3_df, debug_info = prepare_geospatial_data(
                            df_copy, 
                            lat_col, 
                            lon_col, 
                            metric, 
                            resolution=resolution,
                            opacity=opacity
                        )
                    except TypeError as e2:
                        # If opacity also not supported, use minimal version
                        if "opacity" in str(e2):
                            h3_df, debug_info = prepare_geospatial_data(
                                df_copy, 
                                lat_col, 
                                lon_col, 
                                metric, 
                                resolution=resolution
                            )
                        else:
                            raise e2
                else:
                    raise e
            
            # Handle case where prepare_geospatial_data doesn't return a tuple
            if not isinstance(h3_df, tuple):
                debug_info = {}
            elif len(h3_df) == 2:
                h3_df, debug_info = h3_df
            
            # Check for errors in debug_info
            if isinstance(debug_info, dict) and debug_info.get("error"):
                st.error(f"Error processing {metric}: {debug_info.get('error')}")
                continue
            
            if h3_df.empty:
                st.warning(f"No valid data points for {metric}.")
                continue
            
            # Store prepared data
            metric_data[metric] = h3_df
        
        # If no metrics were successfully processed, return None
        if not metric_data:
            st.error("No valid data for any selected metrics.")
            return None
        
        # Process single vs multiple metrics
        if len(metric_data) == 1:
            # Single metric - create simple layer
            metric = list(metric_data.keys())[0]
            h3_df = metric_data[metric]
            
            # Create map layer
            is_3d = (metric == height_metric) and height_metric is not None
            layer = create_h3_layer(
                h3_df,
                elevation_column='agg_numeric_value' if is_3d else None,
                elevation_scale=height_multiplier if is_3d else 0
            )
            
            if layer is None:
                st.error(f"Could not create map layer for {metric}.")
                return None
            
            # Create the map
            deck = pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=6,
                    pitch=30 if is_3d else 0,
                    bearing=0
                ),
                layers=[layer],
                tooltip={
                    "html": "<b>{metric_name}:</b> {aggregated_value_display}<br><b>Count:</b> {count}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            )
            
            return deck
        else:
            # Multiple metrics - create blended visualization
            # Create a combined dataset of all unique H3 indices
            all_h3_indices = set()
            for h3_df in metric_data.values():
                all_h3_indices.update(h3_df['h3_index'].tolist())
            
            combined_data = []
            
            # Find min/max values for height normalization if needed
            height_min_val = None
            height_max_val = None
            
            if normalize_heights and height_metric in metric_data:
                height_df = metric_data[height_metric]
                if 'agg_numeric_value' in height_df.columns and not height_df.empty:
                    height_min_val = height_df['agg_numeric_value'].min()
                    height_max_val = height_df['agg_numeric_value'].max()
            
            # For each H3 index, collect data from all metrics
            for h3_index in all_h3_indices:
                # Initialize data for this hexagon
                hex_data = {
                    'h3_index': h3_index,
                    'rgba_color': [0, 0, 0, 0],  # Default transparent
                    'tooltip_parts': [],
                    'count': 0,
                    'elevation': 0
                }
                
                # Collect RGBA colors for blending
                colors_to_blend = []
                
                for metric in value_cols:
                    if metric in metric_data:
                        h3_df = metric_data[metric]
                        matching_rows = h3_df[h3_df['h3_index'] == h3_index]
                        
                        if not matching_rows.empty:
                            row = matching_rows.iloc[0]
                            
                            # Add color for blending if available
                            if 'rgba_color' in row and row['rgba_color'] is not None:
                                colors_to_blend.append(row['rgba_color'])
                            
                            # Add tooltip information
                            if 'aggregated_value_display' in row:
                                hex_data['tooltip_parts'].append(f"{metric}: {row['aggregated_value_display']}")
                            
                            # Set count if not already set
                            if hex_data['count'] == 0 and 'count' in row:
                                hex_data['count'] = row['count']
                            
                            # Set elevation if this is the height metric
                            if metric == height_metric and 'agg_numeric_value' in row:
                                value = row['agg_numeric_value']
                                
                                # Normalize height if requested and possible
                                if normalize_heights and height_min_val is not None and height_max_val is not None:
                                    if height_max_val > height_min_val:
                                        hex_data['elevation'] = ((value - height_min_val) / (height_max_val - height_min_val)) * 100
                                    else:
                                        hex_data['elevation'] = value
                                else:
                                    hex_data['elevation'] = value
                
                # Blend colors from all metrics
                if colors_to_blend:
                    # Average the RGB components
                    r_sum = g_sum = b_sum = 0
                    a_max = 0
                    
                    for color in colors_to_blend:
                        if isinstance(color, list) and len(color) >= 4:
                            r_sum += color[0]
                            g_sum += color[1]
                            b_sum += color[2]
                            a_max = max(a_max, color[3])
                    
                    num_colors = len(colors_to_blend)
                    hex_data['rgba_color'] = [
                        r_sum // num_colors,
                        g_sum // num_colors,
                        b_sum // num_colors,
                        a_max
                    ]
                
                # Create tooltip text
                hex_data['tooltip_text'] = "<br>".join(hex_data['tooltip_parts'])
                
                # Add to combined data
                combined_data.append(hex_data)
            
            # Create dataframe from combined data
            combined_df = pd.DataFrame(combined_data)
            
            # Check if we have data to display
            if combined_df.empty:
                st.error("No valid data points after combining metrics.")
                return None
            
            # Create the layer with blended colors
            is_3d = height_metric is not None
            layer = pdk.Layer(
                "H3HexagonLayer",
                data=combined_df,
                pickable=True,
                stroked=True,
                filled=True,
                extruded=is_3d,
                get_hexagon="h3_index",
                get_fill_color="rgba_color",
                get_elevation="elevation" if is_3d else 0,
                elevation_scale=height_multiplier if is_3d else 0
            )
            
            # Create the map
            deck = pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=6,
                    pitch=30 if is_3d else 0,
                    bearing=0
                ),
                layers=[layer],
                tooltip={
                    "html": "{tooltip_text}<br><b>Count:</b> {count}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            )
            
            return deck
            
    except Exception as e:
        st.error(f"Error creating Chart 11: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None