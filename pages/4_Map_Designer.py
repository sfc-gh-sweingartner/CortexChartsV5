"""
Map Designer App
====================
This app allows users to customize geospatial visualizations.
"""
import json
import pandas as pd
import streamlit as st
from datetime import datetime
import sys
import os
import numpy as np

# Add path for utils module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import map visualization libraries
try:
    import pydeck as pdk
    import h3
    import branca.colormap as cm
    print("Successfully imported geospatial libraries")
except ImportError as e:
    st.error(f"Failed to import required geospatial libraries: {str(e)}")
    st.error("Please ensure pydeck, h3, and branca are available in your environment.")

# Import utilities
from utils.chart_utils import (
    prepare_geospatial_data,
    create_h3_layer,
    get_quantiles,
    calculate_rgba_color,
    GEOSPATIAL_COLORS
)
from snowflake.snowpark.context import get_active_session

# Set page config
st.set_page_config(
    page_title="Map Designer",
    page_icon="🗺️",
    layout="wide",
)

# Initialize a Snowpark session for executing queries
session = get_active_session()

def init_session_state():
    """Initialize the session state variables."""
    if "map_transfer" not in st.session_state:
        st.session_state.map_transfer = {}
    
    if "current_map_data" not in st.session_state:
        st.session_state.current_map_data = None
    
    if "sql_statement" not in st.session_state:
        st.session_state.sql_statement = ""
    
    if "chart_code" not in st.session_state:
        st.session_state.chart_code = ""
    
    if "chart_metadata" not in st.session_state:
        st.session_state.chart_metadata = {}
    
    if "report_prompt" not in st.session_state:
        st.session_state.report_prompt = ""
    
    if "selected_metrics" not in st.session_state:
        st.session_state.selected_metrics = []
    
    if "h3_resolution" not in st.session_state:
        st.session_state.h3_resolution = 6
    
    if "layer_opacity" not in st.session_state:
        st.session_state.layer_opacity = 0.75
    
    if "height_multiplier" not in st.session_state:
        st.session_state.height_multiplier = 100
    
    if "normalize_heights" not in st.session_state:
        st.session_state.normalize_heights = True
    
    if "color_schemes" not in st.session_state:
        st.session_state.color_schemes = {}
    
    if "height_metric" not in st.session_state:
        st.session_state.height_metric = None
        
    # Add tracking for report editing
    if "report_id" not in st.session_state:
        st.session_state.report_id = None
    
    if "editing_mode" not in st.session_state:
        st.session_state.editing_mode = False
        
    if "report_name" not in st.session_state:
        st.session_state.report_name = ""

def get_metric_config(metric_name, index):
    """
    Get configuration settings for a metric. Similar to the approach in 
    3_Geospatial_Analysis.py but adapted for the Map Designer.
    
    Parameters:
    -----------
    metric_name: str
        Name of the metric
    index: int
        Index of the metric in the selected metrics list
        
    Returns:
    --------
    dict
        Configuration dictionary with resolution, opacity, and color scheme
    """
    with st.expander(f"⚙️ {metric_name} Controls", expanded=True):
        # Resolution selector for H3 level
        resolution = st.slider(
            f"{metric_name} H3 Resolution",
            min_value=4,
            max_value=11,
            value=st.session_state.get(f"h3_resolution_{metric_name}", 6),
            key=f"h3_resolution_{metric_name}",
            help="Higher values mean smaller, more numerous hexagons (4=Largest, 11=Smallest). Level 6 is a good default."
        )
        
        # Opacity selector
        opacity = st.slider(
            f"{metric_name} Opacity",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get(f"opacity_{metric_name}", 0.75),
            step=0.05,
            key=f"opacity_{metric_name}",
            help="Adjust the transparency of hexagons (0=Transparent, 1=Opaque)"
        )
        
        # Set default color scheme based on index
        if metric_name not in st.session_state.color_schemes:
            if index == 0:
                default_color = "White-Blue"
            elif index == 1:
                default_color = "White-Red"
            elif index == 2:
                default_color = "White-Green"
            else:
                # Cycle through colors if somehow we have more than 3 metrics
                colors = ["White-Blue", "White-Red", "White-Green"]
                default_color = colors[index % 3]
            st.session_state.color_schemes[metric_name] = default_color
        
        # Color scheme selector
        color_scheme = st.selectbox(
            f"{metric_name} Color Scheme",
            options=list(GEOSPATIAL_COLORS.keys()),
            index=list(GEOSPATIAL_COLORS.keys()).index(st.session_state.color_schemes.get(metric_name, "White-Blue")),
            key=f"color_scheme_{metric_name}"
        )
        
        # Update color scheme in session state (this is safe since it's not tied directly to the widget key)
        st.session_state.color_schemes[metric_name] = color_scheme
        
        return {
            "resolution": resolution,
            "opacity": opacity,
            "color_scheme": color_scheme
        }

def get_map_from_transfer():
    """Retrieve map data from the transfer object and initialize the session."""
    if "map_transfer" in st.session_state and st.session_state.map_transfer:
        if "redirect" in st.session_state.map_transfer and st.session_state.map_transfer["redirect"]:
            # Clear the redirect flag to prevent reloading on refresh
            st.session_state.map_transfer["redirect"] = False
            
            # Store the transferred data in the session state
            st.session_state.current_map_data = st.session_state.map_transfer.get("df")
            st.session_state.sql_statement = st.session_state.map_transfer.get("sql", "")
            st.session_state.report_prompt = st.session_state.map_transfer.get("prompt", "")
            st.session_state.chart_metadata = st.session_state.map_transfer.get("chart_metadata", {})
            st.session_state.chart_code = st.session_state.map_transfer.get("chart_code", "")
            
            # Extract lat/lon columns from chart metadata
            if "chart_metadata" in st.session_state.map_transfer and "chart11_columns" in st.session_state.map_transfer["chart_metadata"]:
                cols = st.session_state.map_transfer["chart_metadata"]["chart11_columns"]
                lat_col = cols.get("lat_col")
                lon_col = cols.get("lon_col")
                value_col = cols.get("value_col")
                
                # Initialize the first metric
                if value_col and value_col in st.session_state.current_map_data.columns:
                    st.session_state.selected_metrics = [value_col]
                    st.session_state.height_metric = value_col
                    # Set default color scheme
                    st.session_state.color_schemes = {value_col: "White-Blue"}
            
            return True
    return False

def execute_sql_query(sql_statement):
    """Execute the SQL query and return the results."""
    try:
        df = session.sql(sql_statement).to_pandas()
        return df, None
    except Exception as e:
        return None, str(e)

def create_map_visualization(df, selected_metrics, lat_col, lon_col, config):
    """Create a pydeck map visualization with the selected metrics."""
    if df is None or df.empty or not selected_metrics:
        return None
    
    if lat_col not in df.columns or lon_col not in df.columns:
        st.error(f"Latitude column '{lat_col}' or longitude column '{lon_col}' not found in data.")
        return None
    
    # Verify all selected metrics exist in dataframe
    missing_metrics = [metric for metric in selected_metrics if metric not in df.columns]
    if missing_metrics:
        st.error(f"Metrics not found in data: {', '.join(missing_metrics)}")
        return None
    
    # Prepare data for each metric
    metric_data = {}
    height_data = None
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    for metric in selected_metrics:
        # Get metric-specific settings from session state
        resolution = st.session_state.get(f"h3_resolution_{metric}", 6)
        opacity = st.session_state.get(f"opacity_{metric}", 0.75)
        # Get the color scheme for this specific metric
        color_scheme = st.session_state.color_schemes.get(metric, "White-Blue")
        
        # Prepare the H3 data for this metric
        try:
            # First try with all parameters
            result = prepare_geospatial_data(
                df, 
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
            if "got an unexpected keyword argument 'color_scheme'" in error_msg:
                st.warning(f"Using older version of prepare_geospatial_data that doesn't support color schemes")
                try:
                    # Try with just opacity
                    result = prepare_geospatial_data(
                        df, 
                        lat_col, 
                        lon_col, 
                        metric, 
                        resolution=resolution,
                        opacity=opacity
                    )
                except TypeError as e2:
                    # If opacity also not supported, use minimal version
                    if "got an unexpected keyword argument 'opacity'" in str(e2):
                        st.warning(f"Using minimal version of prepare_geospatial_data")
                        result = prepare_geospatial_data(
                            df, 
                            lat_col, 
                            lon_col, 
                            metric, 
                            resolution=resolution
                        )
                    else:
                        raise e2
            else:
                raise e
        
        # Handle different return formats
        if isinstance(result, tuple) and len(result) == 2:
            h3_df, debug_info = result
        else:
            h3_df = result
            debug_info = {}
        
        # Check for errors in debug_info
        if hasattr(debug_info, 'get') and debug_info.get("error"):
            st.error(f"Error processing {metric}: {debug_info.get('error')}")
            continue
        
        if h3_df.empty:
            st.warning(f"No valid data points for {metric}.")
            continue
        
        # Store the prepared data
        metric_data[metric] = h3_df
        
        # Save height data reference if this is the height metric
        if metric == config["height_metric"]:
            height_data = h3_df
    
    # If no metrics were successfully processed, return None
    if not metric_data:
        return None
    
    # Process for single metric vs multiple metrics
    if len(metric_data) == 1:
        # Single metric - create a simple layer
        metric = list(metric_data.keys())[0]
        h3_df = metric_data[metric]
        
        # Create the map layer
        is_3d = (metric == config["height_metric"]) and config["height_metric"] is not None
        layer = create_h3_layer(
            h3_df, 
            elevation_column='agg_numeric_value' if is_3d else None,
            elevation_scale=config["height_multiplier"] if is_3d else 0
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
        # Multiple metrics - blend colors and create a combined layer
        # Create combined dataframe with all unique H3 indices
        all_h3_indices = set()
        for h3_df in metric_data.values():
            all_h3_indices.update(h3_df['h3_index'].tolist())
        
        combined_data = []
        
        # Find min/max values for height normalization if needed
        height_min_val = None
        height_max_val = None
        
        if config["normalize_heights"] and config["height_metric"] in metric_data:
            height_df = metric_data[config["height_metric"]]
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
            
            # Collect RGBA colors from all metrics for blending
            colors_to_blend = []
            
            for metric in selected_metrics:
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
                        if metric == config["height_metric"] and 'agg_numeric_value' in row:
                            value = row['agg_numeric_value']
                            
                            # Normalize height if requested and possible
                            if config["normalize_heights"] and height_min_val is not None and height_max_val is not None:
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
        is_3d = config["height_metric"] is not None
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
            elevation_scale=config["height_multiplier"] if is_3d else 0
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

def save_report_to_snowflake():
    """Save the report to Snowflake."""
    if "current_map_data" not in st.session_state or st.session_state.current_map_data is None:
        st.error("No data to save.")
        return False
    
    report_name = st.session_state.get("report_name", "")
    if not report_name:
        st.error("Please enter a report name.")
        return False
    
    # Update chart metadata before saving
    update_chart_metadata()
    
    # Generate updated chart code
    update_chart_code()
    
    # Convert chart metadata to JSON string
    chart_metadata_json = json.dumps(st.session_state.chart_metadata)
    
    # Execute the SQL to save the report
    try:
        # Check if we're in editing mode with a report ID
        if st.session_state.editing_mode and st.session_state.report_id is not None:
            # Update existing report
            update_sql = f"""
            UPDATE CORTEX_ANALYST_REPORTS 
            SET REPORT_NAME = '{report_name}', 
                REPORT_DESCRIPTION = '{st.session_state.report_prompt}',
                SQL_STATEMENT = '{st.session_state.sql_statement.replace("'", "''")}',
                CHART_CODE = '{st.session_state.chart_code.replace("'", "''")}',
                CHART_METADATA = '{chart_metadata_json.replace("'", "''")}',
                UPDATED_AT = CURRENT_TIMESTAMP()
            WHERE REPORT_ID = {st.session_state.report_id}
            """
            session.sql(update_sql).collect()
            return True
        else:
            # Insert new report
            insert_sql = f"""
            INSERT INTO CORTEX_ANALYST_REPORTS (
                REPORT_NAME,
                REPORT_DESCRIPTION,
                SQL_STATEMENT,
                CHART_CODE,
                CHART_METADATA,
                CREATED_AT,
                UPDATED_AT
            ) VALUES (
                '{report_name}',
                '{st.session_state.report_prompt}',
                '{st.session_state.sql_statement.replace("'", "''")}',
                '{st.session_state.chart_code.replace("'", "''")}',
                '{chart_metadata_json.replace("'", "''")}',
                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()
            )
            """
            session.sql(insert_sql).collect()
            return True
    except Exception as e:
        st.error(f"Error saving report: {e}")
        return False

def update_chart_metadata():
    """Update the chart metadata based on user selections."""
    if st.session_state.current_map_data is None:
        return
    
    # Extract columns from chart metadata
    if "chart_metadata" in st.session_state and "chart11_columns" in st.session_state.chart_metadata:
        cols = st.session_state.chart_metadata["chart11_columns"]
        lat_col = cols.get("lat_col")
        lon_col = cols.get("lon_col")
        
        # Ensure we have valid color schemes for all metrics
        color_schemes = st.session_state.color_schemes
        
        # Collect per-metric settings
        metric_settings = {}
        for metric in st.session_state.selected_metrics:
            metric_settings[metric] = {
                "resolution": st.session_state.get(f"h3_resolution_{metric}", 6),
                "opacity": st.session_state.get(f"opacity_{metric}", 0.75),
                "color_scheme": color_schemes.get(metric, "White-Blue")
            }
        
        # Update the chart metadata with the current selections
        st.session_state.chart_metadata = {
            "chart11_columns": {
                "lat_col": lat_col,
                "lon_col": lon_col,
                "value_cols": st.session_state.selected_metrics,
                "height_metric": st.session_state.height_metric,
                "height_multiplier": st.session_state.height_multiplier,
                "normalize_heights": st.session_state.normalize_heights,
                "color_schemes": color_schemes,
                "metric_settings": metric_settings
            }
        }

def update_chart_code():
    """Update the chart code based on the current configuration."""
    if st.session_state.current_map_data is None:
        return
    
    # Generate code for the map visualization
    chart_metadata = st.session_state.chart_metadata
    if "chart11_columns" in chart_metadata:
        cols = chart_metadata["chart11_columns"]
        lat_col = cols.get("lat_col")
        lon_col = cols.get("lon_col")
        value_cols = cols.get("value_cols", [])
        height_metric = cols.get("height_metric")
        height_multiplier = cols.get("height_multiplier", 100)
        normalize_heights = cols.get("normalize_heights", True)
        color_schemes = cols.get("color_schemes", {})
        metric_settings = cols.get("metric_settings", {})
        
        # Generate Python code for creating the map
        code = f"""import pandas as pd
import pydeck as pdk
import h3
import streamlit as st
import numpy as np
from utils.chart_utils import prepare_geospatial_data, create_h3_layer, GEOSPATIAL_COLORS

def create_chart(df):
    # Map configuration
    lat_col = "{lat_col}"
    lon_col = "{lon_col}"
    selected_metrics = {value_cols}
    height_metric = {repr(height_metric)}
    height_multiplier = {height_multiplier}
    normalize_heights = {normalize_heights}
    color_schemes = {color_schemes}
    
    # Per-metric settings
    metric_settings = {metric_settings}
    
    # Prepare data for each metric
    metric_data = {{}}
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    for metric in selected_metrics:
        # Get metric-specific settings
        settings = metric_settings.get(metric, {{}})
        resolution = settings.get("resolution", 6)
        opacity = settings.get("opacity", 0.75)
        color_scheme = settings.get("color_scheme", color_schemes.get(metric, "White-Blue"))
        
        # Prepare H3 data for this metric with error handling
        try:
            # First try with all parameters
            h3_df, debug_info = prepare_geospatial_data(
                df, 
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
            if "got an unexpected keyword argument 'color_scheme'" in error_msg:
                st.warning(f"Using older version of prepare_geospatial_data that doesn't support color schemes")
                try:
                    # Try with just opacity
                    h3_df, debug_info = prepare_geospatial_data(
                        df, 
                        lat_col, 
                        lon_col, 
                        metric, 
                        resolution=resolution,
                        opacity=opacity
                    )
                except TypeError as e2:
                    # If opacity also not supported, use minimal version
                    if "got an unexpected keyword argument 'opacity'" in str(e2):
                        st.warning(f"Using minimal version of prepare_geospatial_data")
                        h3_df, debug_info = prepare_geospatial_data(
                            df, 
                            lat_col, 
                            lon_col, 
                            metric, 
                            resolution=resolution
                        )
                    else:
                        raise e2
            else:
                raise e
        
        if isinstance(h3_df, tuple) and len(h3_df) == 2:
            # Handle return value format where debug_info is part of the return value
            h3_df, debug_info = h3_df
            
        if hasattr(debug_info, 'get') and debug_info.get("error"):
            st.error(f"Error processing {{metric}}: {{debug_info.get('error')}}")
            continue
            
        if h3_df.empty:
            st.warning(f"No valid data points for {{metric}}.")
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
            st.error(f"Could not create map layer for {{metric}}.")
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
            tooltip={{
                "html": "<b>{{metric_name}}:</b> {{aggregated_value_display}}<br><b>Count:</b> {{count}}",
                "style": {{"backgroundColor": "steelblue", "color": "white"}}
            }}
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
            hex_data = {{
                'h3_index': h3_index,
                'rgba_color': [0, 0, 0, 0],  # Default transparent
                'tooltip_parts': [],
                'count': 0,
                'elevation': 0
            }}
            
            # Collect RGBA colors for blending
            colors_to_blend = []
            
            for metric in selected_metrics:
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
                            hex_data['tooltip_parts'].append(f"{{metric}}: {{row['aggregated_value_display']}}")
                        
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
            tooltip={{
                "html": "{{tooltip_text}}<br><b>Count:</b> {{count}}",
                "style": {{"backgroundColor": "steelblue", "color": "white"}}
            }}
        )
        
        return deck
"""
        
        # Update the session state with the generated code
        st.session_state.chart_code = code

def load_saved_reports():
    """Load saved reports from Snowflake."""
    try:
        query = """
        SELECT REPORT_ID, REPORT_NAME, REPORT_DESCRIPTION, 
               CHART_METADATA, UPDATED_AT
        FROM CORTEX_ANALYST_REPORTS 
        ORDER BY REPORT_NAME
        """
        reports = session.sql(query).collect()
        
        # Convert to DataFrame
        reports_df = pd.DataFrame(reports)
        
        if reports_df.empty:
            return pd.DataFrame(columns=["REPORT_ID", "REPORT_NAME", "REPORT_DESCRIPTION", "IS_MAP"])
        
        # Add a column to identify map reports
        reports_df["IS_MAP"] = False
        
        # Parse JSON in CHART_METADATA to identify map reports
        for idx, row in reports_df.iterrows():
            try:
                if row["CHART_METADATA"]:
                    metadata = json.loads(row["CHART_METADATA"])
                    # Check if it's a map (has chart11_columns)
                    if "chart11_columns" in metadata:
                        reports_df.at[idx, "IS_MAP"] = True
            except:
                # If JSON parsing fails, assume it's not a map
                pass
        
        return reports_df
    except Exception as e:
        st.error(f"Error loading reports: {str(e)}")
        return pd.DataFrame(columns=["REPORT_ID", "REPORT_NAME", "REPORT_DESCRIPTION", "IS_MAP"])

def load_report_by_id(report_id):
    """Load a specific report by ID."""
    try:
        query = f"""
        SELECT REPORT_ID, REPORT_NAME, REPORT_DESCRIPTION, 
               SQL_STATEMENT, CHART_CODE, CHART_METADATA
        FROM CORTEX_ANALYST_REPORTS 
        WHERE REPORT_ID = {report_id}
        """
        result = session.sql(query).collect()
        if not result:
            return None
        
        report = result[0]
        
        # Load chart metadata if available
        chart_metadata = None
        if report["CHART_METADATA"]:
            try:
                chart_metadata = json.loads(report["CHART_METADATA"])
                
                # Verify this is a map report
                if "chart11_columns" not in chart_metadata:
                    st.error("Selected report is not a map report")
                    return None
            except:
                st.error("Invalid chart metadata in report")
                return None
        else:
            st.error("No chart metadata in report")
            return None
        
        # Execute SQL to get data
        df = None
        if report["SQL_STATEMENT"]:
            try:
                df = session.sql(report["SQL_STATEMENT"]).to_pandas()
            except Exception as sql_error:
                st.error(f"Error executing SQL from saved report: {str(sql_error)}")
        
        return {
            "id": report["REPORT_ID"],
            "name": report["REPORT_NAME"],
            "description": report["REPORT_DESCRIPTION"],
            "sql": report["SQL_STATEMENT"],
            "chart_code": report["CHART_CODE"],
            "chart_metadata": chart_metadata,
            "data": df
        }
    except Exception as e:
        st.error(f"Error loading report: {str(e)}")
        return None

def main():
    """Main function to render the Map Designer app."""
    st.title("🗺️ Map Designer")
    
    # Initialize session state
    init_session_state()
    
    # Get data from transfer if available
    data_loaded = get_map_from_transfer()
    
    # Create sidebar
    with st.sidebar:
        st.header("Map Controls")
        
        # Saved Reports section
        st.subheader("Saved Reports")
        
        # Load saved reports
        reports_df = load_saved_reports()
        
        # Filter to only show map reports
        map_reports = reports_df[reports_df["IS_MAP"] == True]
        
        if not map_reports.empty:
            # Create a selectbox with report names
            report_options = ["-- Create New Map --"] + list(map_reports["REPORT_NAME"].values)
            report_indices = [None] + list(map_reports["REPORT_ID"].values)
            
            selected_index = 0  # Default to "Create New Map"
            if st.session_state.editing_mode and st.session_state.report_id in report_indices:
                selected_index = report_indices.index(st.session_state.report_id)
            
            selected_option = st.selectbox(
                "Select a map to edit:",
                options=report_options,
                index=selected_index,
                key="map_selector"
            )
            
            # Handle report selection
            if selected_option != "-- Create New Map --":
                selected_report_index = report_options.index(selected_option) - 1  # Adjust for "Create New" option
                selected_report_id = report_indices[selected_report_index + 1]  # +1 to adjust for None at index 0
                
                # Only load the report if we're not already editing it or if we're switching reports
                if not st.session_state.editing_mode or st.session_state.report_id != selected_report_id:
                    report = load_report_by_id(selected_report_id)
                    if report:
                        # Set session state variables
                        st.session_state.report_id = report["id"]
                        st.session_state.report_name = report["name"]
                        st.session_state.report_prompt = report["description"]
                        st.session_state.sql_statement = report["sql"]
                        st.session_state.chart_code = report["chart_code"]
                        st.session_state.chart_metadata = report["chart_metadata"]
                        st.session_state.current_map_data = report["data"]
                        
                        # Extract metrics from chart metadata
                        if "chart11_columns" in report["chart_metadata"]:
                            cols = report["chart_metadata"]["chart11_columns"]
                            value_cols = cols.get("value_cols", [])
                            height_metric = cols.get("height_metric")
                            color_schemes = cols.get("color_schemes", {})
                            
                            # Initialize metrics
                            st.session_state.selected_metrics = value_cols
                            st.session_state.height_metric = height_metric
                            st.session_state.color_schemes = color_schemes
                        
                        st.session_state.editing_mode = True
                        st.rerun()
            else:
                # Reset if "Create New Map" is selected
                if st.session_state.editing_mode:
                    # Clear session state for editing
                    st.session_state.report_id = None
                    st.session_state.editing_mode = False
                    st.session_state.report_name = ""
                    st.session_state.report_prompt = ""
                    # Don't clear the current data or SQL to make it easier to create variations
                    st.rerun()
        else:
            st.info("No saved map reports found")
        
        # Data Source section
        st.subheader("Data Source")
        if st.session_state.current_map_data is not None:
            st.info(f"Using data from Cortex Analyst with {len(st.session_state.current_map_data)} rows")
            
            if st.button("Re-run SQL"):
                # Re-execute the SQL to refresh the data
                df, error = execute_sql_query(st.session_state.sql_statement)
                if error:
                    st.error(f"Error executing SQL: {error}")
                else:
                    st.session_state.current_map_data = df
                    st.success("Data refreshed successfully")
                    st.rerun()
        else:
            st.warning("No data loaded. Return to Cortex Analyst to generate data.")
            
            # Allow direct SQL input
            sql_input = st.text_area("Or enter SQL directly:", height=150)
            if st.button("Run SQL"):
                if sql_input:
                    df, error = execute_sql_query(sql_input)
                    if error:
                        st.error(f"Error executing SQL: {error}")
                    else:
                        st.session_state.current_map_data = df
                        st.session_state.sql_statement = sql_input
                        st.success("SQL executed successfully")
                        st.rerun()
                else:
                    st.error("Please enter a SQL query")
        
        # Map Configuration section (only show if data is loaded)
        if st.session_state.current_map_data is not None:
            df = st.session_state.current_map_data
            
            st.divider()
            st.subheader("Map Configuration")
            
            # Extract lat/lon columns from chart metadata
            lat_col = None
            lon_col = None
            if "chart_metadata" in st.session_state and "chart11_columns" in st.session_state.chart_metadata:
                cols = st.session_state.chart_metadata["chart11_columns"]
                lat_col = cols.get("lat_col")
                lon_col = cols.get("lon_col")
            
            # Metric Selection section
            st.markdown("### Metrics Selection")
            
            # Find all numeric columns (excluding lat/lon if known)
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            # Filter out lat/lon columns if known
            if lat_col and lon_col:
                numeric_cols = [col for col in numeric_cols if col != lat_col and col != lon_col]
            
            # Limit to maximum 3 metrics as requested
            all_metrics = numeric_cols
            
            # Allow selecting up to 3 metrics
            selected_metrics = st.multiselect(
                "Select up to 3 metrics to display:",
                options=all_metrics,
                default=st.session_state.selected_metrics if st.session_state.selected_metrics else [],
                help="Select between 1-3 metrics to visualize on the map"
            )
            
            # Enforce limit of 3 metrics
            if len(selected_metrics) > 3:
                st.warning("Maximum 3 metrics allowed. Using the first 3 selected.")
                selected_metrics = selected_metrics[:3]
            
            # Update session state with selected metrics
            st.session_state.selected_metrics = selected_metrics
            
            # Create layer configuration for each selected metric
            if selected_metrics:
                st.markdown("### Metric Controls")
                
                # Create individual controls for each metric
                for i, metric in enumerate(selected_metrics):
                    get_metric_config(metric, i)
            
            # 3D Height controls
            st.markdown("### 3D Height Controls")
            
            # Height metric selector (if multiple metrics available)
            if len(selected_metrics) > 0:
                # Create an options list with "None" as the first option
                height_options = ["None"] + selected_metrics
                
                # Determine the correct index
                if st.session_state.height_metric is None:
                    selected_index = 0  # "None" option
                else:
                    # Find the index of the current height metric, or default to "None" if not found
                    try:
                        selected_index = height_options.index(st.session_state.height_metric)
                    except ValueError:
                        selected_index = 0  # Default to "None" if not found
                
                height_metric = st.radio(
                    "Which metric should control the hexagon height?",
                    options=height_options,
                    index=selected_index,
                    help="Select a metric to determine the height of hexagons, or 'None' for a 2D map"
                )
                
                # Update session state
                st.session_state.height_metric = None if height_metric == "None" else height_metric
                
                # Only show height controls if a height metric is selected
                if st.session_state.height_metric is not None:
                    # Height multiplier
                    height_multiplier = st.slider(
                        "Height Multiplier",
                        min_value=1,
                        max_value=200,
                        value=st.session_state.height_multiplier,
                        step=5,
                        help="Increase this value to make the height differences more pronounced"
                    )
                    st.session_state.height_multiplier = height_multiplier
                    
                    # Normalize heights
                    normalize_heights = st.checkbox(
                        "Normalize Height Values",
                        value=st.session_state.normalize_heights,
                        help="Normalize values to range from 0 to 100, making height differences more visible for metrics with small values or little variation"
                    )
                    st.session_state.normalize_heights = normalize_heights
            
            # Save Report section
            st.divider()
            st.subheader("Save Report")
            
            report_name = st.text_input("Report Name:", key="report_name", value=st.session_state.report_name)
            
            # Use a different label for the button depending on editing mode
            save_label = "Update Report" if st.session_state.editing_mode else "Save Report"
            if st.button(save_label):
                if save_report_to_snowflake():
                    success_msg = "Report updated successfully!" if st.session_state.editing_mode else "Report saved successfully!"
                    st.success(success_msg)
    
    # Display editing mode indicator if applicable
    if st.session_state.editing_mode:
        st.success(f"Editing map report: {st.session_state.report_name}")
    
    # Main content area
    if st.session_state.current_map_data is not None:
        df = st.session_state.current_map_data
        
        # Display prompt/description
        st.markdown(f"**Description:** {st.session_state.report_prompt}")
        
        # Display DataFrame preview
        with st.expander("Preview Data", expanded=False):
            st.dataframe(df, use_container_width=True)
        
        # Get lat/lon columns from metadata
        lat_col = None
        lon_col = None
        if "chart_metadata" in st.session_state and "chart11_columns" in st.session_state.chart_metadata:
            cols = st.session_state.chart_metadata["chart11_columns"]
            lat_col = cols.get("lat_col")
            lon_col = cols.get("lon_col")
        
        # Check if we have the necessary data for visualization
        if lat_col and lon_col and lat_col in df.columns and lon_col in df.columns and st.session_state.selected_metrics:
            # Create config for map visualization
            config = {
                "height_metric": st.session_state.height_metric,
                "height_multiplier": st.session_state.height_multiplier,
                "normalize_heights": st.session_state.normalize_heights,
                "color_schemes": st.session_state.color_schemes
            }
            
            # Create and display the map
            st.subheader("Map Visualization")
            deck = create_map_visualization(df, st.session_state.selected_metrics, lat_col, lon_col, config)
            
            if deck:
                # Create full-height layout for the map
                st.markdown("""
                <style>
                .element-container:has(iframe.deckgl-ui) {
                height: 600px;
                }
                iframe.deckgl-ui {
                height: 600px !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Display the map
                st.pydeck_chart(deck, use_container_width=True, height=600)
                
                # Update chart metadata and code after visualization is created
                update_chart_metadata()
                update_chart_code()
            else:
                st.error("Could not create map visualization. Please check your data and selections.")
        else:
            if not (lat_col and lon_col):
                st.error("Latitude and longitude columns are not defined in the metadata.")
            elif not (lat_col in df.columns and lon_col in df.columns):
                st.error(f"Latitude column '{lat_col}' or longitude column '{lon_col}' not found in data.")
            elif not st.session_state.selected_metrics:
                st.info("Please select at least one metric to visualize in the sidebar.")
    else:
        st.info("No data loaded. Use Cortex Analyst to generate a report or enter SQL directly in the sidebar.")

if __name__ == "__main__":
    main() 