# CortexCharts V4

CortexCharts is a Streamlit in Snowflake app that offers an intuitive interface for creating and managing various types of charts and visualizations against Cortex Analyst. This tool is perfect for data analysts and business users who want to use Text 2 SQL to create compelling visual representations of their data.

This V4 is an uplift from V3 to add prompt generation  

You can find V2 here: https://github.com/sfc-gh-sweingartner/CortexCharts/tree/main
You can find V3 here: https://github.com/sfc-gh-sweingartner/CortexChartsV3/tree/main


## Features

### Pages
1. **Home** - Landing page with overview and quick access to key features
2. **Cortex Analyst** - Main workspace for data analysis and visualization
3. **Report Designer** - Create and customize detailed reports
4. **Dashboard** - View and manage all your visualizations
5. **Map Designer** - Create and customize geospatial visualizations

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
2. Run the create_reports_table.sql script which will create the CortexChartsV4 database and schema, and create the two tables that hold report designs
3. You need to make SiS UI aware of the new DB.  Refreshing the dbs via the UI doesn't work.  So, refresh your entire browser (e.g. log out and in again or hit Control - Shift - R on a Mac )
4. click Projects > Streamlit
5. Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
6. Click "Create Git Repository"
7. In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV4
8. You can leave the repository name as the default
9. In the API Integration drop down box, choose GIT_SWEINGARTNER
10. Deploy it into the CortexChartsV4 database and CortexChartsV4 schema, and use any WH
11. Click Home.py then "Select File"
12. Choose the db CortexChartsV4 and schema CortexChartsV4
13. Name it CortexChartsV4 (You can rename after everything is working)
14. Choose any warehouse you want (maybe small or above) and click create
15. Open the code editor panel and edit which yaml file(s) (i.e. semantic model) that your solution is going to use.  You will find the line to alter at line 50 of the /pages/1_Cortex_Analyst.py file
16. Add the following packages via the drop down box above the code: altair, branca, h3-py, matplotlib-base, numpy, pandas, plotly, pydeck, scipy 
17. Click the blue "Run" button (It will take a minute to download all those map libraries)
18. Set up network access for maps using the instructions below.

## How to Set Up Map Access

### Prerequisites
- ACCOUNTADMIN role access in Snowflake
- A deployed Streamlit in Snowflake (SiS) app
- Database and schema information where your app is deployed

### Step-by-Step Setup

1. **Configure Network Access**:
   - Open `connectMapBoxNoKey.sql` in your editor
   - When you get to the ALTER STREAMLIT statement:
     - Run the SHOW STREAMLITS command first
     - Find your app with title 'CortexChartsV4'
     - Copy its "name" value (an auto-generated ID like 'FFLFTTR_22W04CI0')
     - Replace "YOUR_STREAMLIT_APP_NAME" with this value

2. **Execute the Script**:
   - Connect to Snowflake as ACCOUNTADMIN
   - Execute each section of the script in sequence
   - Pay attention to the verification steps after each section
   - Fix any errors before proceeding to the next section

3. **Verify Setup**:
   - Refresh your Streamlit app
   - Open the Map Designer page
   - Confirm that map backgrounds load correctly

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

## Semantic Model Parser (Phase 1)

The semantic model parser allows users to explore and utilize Snowflake semantic models directly within Cortex Analyst.

### Features

- **YAML Parser Utility**: Parses semantic model YAML files to extract:
  - Dimensions, facts, and time dimensions
  - Column metadata (names, descriptions, types)
  - Relationships and joins between tables
  - Synonyms and sample values for columns
  
- **Column Display Interface**:
  - Groups columns by table
  - Supports filtering by column type (dimensions, facts, time dimensions)
  - Provides search functionality to find specific columns
  - Shows tooltips with detailed column information
  - Uses visual icons to distinguish between column types
  
- **Operation Configuration**:
  - Allows selecting operations for each column (Group By, Sum, Count, etc.)
  - Provides appropriate operation options based on column type
  - Supports filtering with free-form text
  - Default operations based on column type (Sum for facts, Group By for dimensions)
  
- **Prompt Generation**:
  - Creates natural language prompts from selected columns and operations
  - Includes table names in column references
  - Places filters at the beginning of the prompt
  - Automatically populates the chat input with the generated prompt

### Usage

1. Select a semantic model from the dropdown in the sidebar
2. Browse and select columns from the model (grouped by table)
3. Configure operations and filters for selected columns
4. Click "Generate Prompt" to create a natural language query
5. Submit the prompt to get SQL and visualization results

### Implementation

The implementation includes:

- `utils/semantic_model_utils.py`: Core parser utility with classes for tables, columns, and relationships
- `utils/test_semantic_model_utils.py`: Comprehensive unit tests
- Enhanced `display_semantic_model_columns()` function in `pages/1_Cortex_Analyst.py`
- Improved `generate_prompt_from_selections()` function for creating natural language prompts