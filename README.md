# CortexCharts V5

CortexCharts is a Streamlit in Snowflake application that allows users to interact with their data using natural language powered by Snowflake's Cortex Agents. Users can ask questions about their data, generate SQL queries, create visualizations, and build dashboards.

This V5 is an uplift from V4 to use Cortex Agents instead of Cortex Analyst, adding enhanced multi-turn conversations, multi-semantic model support, and advanced AI reasoning capabilities.

## Key Features

- **Natural Language to SQL**: Ask questions about your data in plain English
- **Cortex Agents Integration**: Advanced AI reasoning with multi-turn conversation support
- **Multiple Semantic Models**: Automatic selection from multiple data models
- **Interactive Visualizations**: 11 different chart types including geospatial maps
- **Report Designer**: Customize and save reports with interactive charts
- **Dashboard Builder**: Create multi-report dashboards
- **Map Designer**: Specialized interface for geospatial data visualization

## Architecture

The application consists of four main pages:

1. **Cortex Agents** (`pages/1_Cortex_Analyst.py`): Main interface for natural language queries
2. **Report Designer** (`pages/2_Report_Designer.py`): Customize and save reports
3. **Dashboard** (`pages/3_Dashboard.py`): Create and manage dashboards
4. **Map Designer** (`pages/4_Map_Designer.py`): Design geospatial visualizations

## Supported Chart Types

The application supports 11 different visualization types:

1. **Line/Bar Chart by Date** - Time series data with single metric
2. **Dual Axis Line Chart** - Time series with two metrics
3. **Stacked Bar Chart by Date** - Time series with categories
4. **Stacked Bar with Column Selector** - Interactive category selection
5. **Scatter Plot** - Two numeric dimensions with categories
6. **Multi-Dimension Scatter** - Advanced scatter with multiple categories
7. **Bubble Chart** - Three numeric dimensions with categories
8. **Multi-Dimension Bubble** - Complex bubble charts with multiple categories
9. **Bar Chart with Selectors** - Interactive bar charts
10. **KPI Tiles** - Single-row metric displays
11. **Geospatial Map** - 3D hexagon maps for location data

## Semantic Models

The application works with YAML semantic models that define:
- Table relationships and joins
- Column types (dimensions, facts, time dimensions)
- Business definitions and descriptions
- Sample data and validation rules

## Installation and Setup

### Prerequisites

- Snowflake account with Cortex Agents access
- Streamlit in Snowflake enabled
- Appropriate privileges to create databases, schemas, and tables

### Setup Steps

1. **Database Setup**: 
   - Run the `create_reports_table.sql` script which will create the CortexChartsV5 database and schema, and create the two tables that hold report designs

2. **Deploy Streamlit App**:
   - Create a new Streamlit in Snowflake app
   - In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV5
   - Set the main file to `Home.py`
   - Deploy it into the CortexChartsV5 database and CortexChartsV5 schema, and use any warehouse
   - Choose the database CortexChartsV5 and schema CortexChartsV5
   - Name it CortexChartsV5 (You can rename after everything is working)

3. **Configure Semantic Models**:
   - Upload your semantic model YAML files to appropriate Snowflake stages
   - Update the `AVAILABLE_SEMANTIC_MODELS_PATHS` in `pages/1_Cortex_Analyst.py` with your model paths

4. **Test the Application**:
   - Find your app with title 'CortexChartsV5'
   - Navigate through the different pages to ensure functionality
   - Test natural language queries with your semantic models

## Usage

### Basic Workflow

1. **Ask Questions**: Use natural language to query your data
2. **Review Results**: See generated SQL, data results, and automatic visualizations
3. **Customize**: Use Report Designer to modify charts and SQL
4. **Save Reports**: Store customized reports for reuse
5. **Build Dashboards**: Combine multiple reports into dashboards

### Advanced Features

- **Multi-Model Queries**: Select multiple semantic models for comprehensive analysis
- **Conversation Context**: Build on previous questions with follow-up queries
- **Interactive Charts**: Use selectors and filters in visualizations
- **Geospatial Analysis**: Create 3D maps for location-based data

## File Structure

```
CortexChartsV5/
├── Home.py                     # Main application entry point
├── pages/
│   ├── 1_Cortex_Analyst.py    # Cortex Agents interface
│   ├── 2_Report_Designer.py   # Report customization
│   ├── 3_Dashboard.py         # Dashboard management
│   └── 4_Map_Designer.py      # Geospatial visualization
├── utils/
│   ├── chart_utils.py         # Chart creation functions
│   ├── semantic_model_utils.py # YAML parsing utilities
│   └── test_semantic_model_utils.py # Unit tests
├── Dev/                       # Sample semantic models
├── docs/                      # Documentation
├── create_reports_table.sql   # Database setup
└── README.md                  # This file
```

## Contributing

This project is part of Snowflake's Cortex AI platform demonstration. For questions or issues, please refer to the Snowflake documentation or contact your Snowflake representative.

## License

This project is provided as-is for demonstration purposes as part of Snowflake's Cortex platform.

## Features

### Pages
1. **Home** - Landing page with overview and quick access to key features
2. **Cortex Analyst** - Main workspace for data analysis and visualization
3. **Report Designer** - Create and customize detailed reports
4. **Dashboard** - View and manage all your visualizations
5. **Map Designer** - Create and customize geospatial visualizations

## Your Data
You can install this on top of your existing yaml files (and thus your own data)
To get a better experience with with charts, you can add statments like these as custom instructions to your yaml files:

custom_instructions: 
  1. Avoid returning date columns unless asked to show the date or break out the info by date.  For example, if you are asked to bring back something for the entire time period, do not bring back the start and end date.  
  2. If you are asked to return the location of something, bring back both the latitude and the longitude columns.
  3. All week, month, and year columns should be in a date type rather than as text.  When aggregating a date, use date_truc() which returns a date rather than date_part() or year() which returns a number
  4. If a query includes location (e.g. lat, lon) then use ifnull to convert all null fact columns to zero

## Chart Selection Logic

The chart selection system follows a 3-step process to determine the best visualization based on your data structure:

### Step 1: Check for Geospatial Data (Highest Priority)
First, the system checks if the data contains latitude and longitude columns with valid coordinate ranges.

### Step 2: Check for Single Row with Numeric Data
If there's a single row of data with 1-4 numeric columns, KPI tiles are displayed.

### Step 3: Evaluate Data Structure
The system analyzes the number of date, text, and numeric columns to select the most appropriate chart type.

## Chart Rules and Requirements

The following table outlines the requirements and resulting chart types for each visualization rule:

| Chart | Chart Type | # Date Cols | # Text Cols | # Numeric Cols | Special Conditions |
|-------|------------|-------------|-------------|----------------|-------------------|
| 1 | Line/Bar Chart by Date | 1 | 0 | 1 | - |
| 2 | Dual Axis Line Chart | 1 | 0 | 2 | - |
| 3 | Stacked Bar Chart by Date | 1 | 1 | 1 | - |
| 4 | Stacked Bar with Column Selector | 1 | 2+ | 1 | - |
| 5 | Scatter Plot | 0 | 1 | 2 | - |
| 6 | Multi-Dimension Scatter | 0 | 2 | 2 | - |
| 7 | Bubble Chart | 0 | 1 | 3 | - |
| 8 | Multi-Dimension Bubble | 0 | 2+ | 3+ | - |
| 9 | Bar Chart with Selectors | 0 | 1+ | 1 | - |
| 10 | KPI Tiles | Any | Any | 1-4 | Single row of data |
| 11 | Geospatial Map | Any | Any | Any | Latitude & longitude columns present |

## Configuration
Before running the application, ensure you have:
1. Valid Snowflake credentials
2. Proper database permissions


## How to Deploy the App
1. In Snowsight, open a SQL worksheet and run this with ACCOUNTADMIN to allow your env to see this GIT project: CREATE OR REPLACE API INTEGRATION git_sweingartner API_PROVIDER = git_https_api API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-sweingartner') ENABLED = TRUE;
2. Run the create_reports_table.sql script which will create the CortexChartsV5 database and schema, and create the two tables that hold report designs
3. You need to make SiS UI aware of the new DB.  Refreshing the dbs via the UI doesn't work.  So, refresh your entire browser (e.g. log out and in again or hit Control - Shift - R on a Mac )
4. click Projects > Streamlit
5. Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
6. Click "Create Git Repository"
7. In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV5
8. You can leave the repository name as the default
9. In the API Integration drop down box, choose GIT_SWEINGARTNER
10. Deploy it into the CortexChartsV5 database and CortexChartsV5 schema, and use any WH
11. Click Home.py then "Select File"
12. Choose the db CortexChartsV5 and schema CortexChartsV5
13. Name it CortexChartsV5 (You can rename after everything is working)
14. Choose any warehouse you want (maybe small or above) and click create
15. Open the code editor panel and edit which yaml file(s) (i.e. semantic model) that your solution is going to use.  You will find the line to alter at line 50 of the /pages/1_Cortex_Analyst.py file
16. Add the following packages via the drop down box above the code: altair, branca, h3-py, matplotlib-base, numpy, pandas, plotly, pydeck, scipy 
17. Click the blue "Run" button (It will take a minute to download all those map libraries)
18. Set up network access for maps using the instructions below.

## How to Set Up Map Access

1. **Configure Network Access**:
   - Open `connectMapBoxNoKey.sql` in your editor
   - Run each line one by one
   - When you get to the ALTER STREAMLIT statement:
     - Run the SHOW STREAMLITS command first
     - Find your app with title 'CortexChartsV5'
     - Copy its "name" value (an auto-generated ID like 'FFLFTTR_22W04CI0')
     - Replace "YOUR_STREAMLIT_APP_NAME" with this value
     - Continue to execute the rest of the script

### Troubleshooting
If maps don't load:
- Verify all SHOW commands in the script return expected results
- Ensure your app ID is correct in the ALTER STREAMLIT statement
- Confirm all grants were successful
- Try refreshing your browser cache
- Check the Network Logs in your browser's developer tools for requests to Mapbox servers
- If all else fails, you might need to use a personal Mapbox API key (refer to the original connectMapBox.sql)



Note that if you want to demo against the Synthea healthcare Dataset, refer to this Git and request a datashare: https://github.com/sfc-gh-sweingartner/synthea/tree/main

If you want to demo geospatial reporting against the telco network data, first install this project and leverage that yaml file (and thus the data): 
https://github.com/sfc-gh-sweingartner/network_optmise

Note the if you want to demo against synthea and / or the telco network and want a datashare, then send an email or Slack to stephen.weingartner@snowflake.com with your account details where I can do a direct share: 
SELECT CURRENT_ORGANIZATION_NAME() || '.' || CURRENT_ACCOUNT_NAME();

Reach out to stephen.weingartner@snowflake.com with any issues.

## Semantic Model Parser 

The semantic model parser allows users to explore and utilize Snowflake semantic models directly within Cortex Analyst.

### Usage

1. Select a semantic model from the dropdown in the sidebar
2. Browse and select columns from the model (grouped by table)
3. Configure operations and filters for selected columns
4. Click "Generate Prompt" to create a natural language query
5. Submit the prompt to get SQL and visualization results

