# CortexCharts V3

CortexCharts is a Streamlit in Snowflake app that offers an intuitive interface for creating and managing various types of charts and visualizations against Cortex Analyst. This tool is perfect for data analysts and business users who want to use Text 2 SQL to create compelling visual representations of their data.

This V3 is an uplift from V2 to add mapping capabilites.  

You can find V2 here: https://github.com/sfc-gh-sweingartner/CortexCharts/tree/main

## Features

### Pages
1. **Home** - Landing page with overview and quick access to key features
2. **Cortex Analyst** - Main workspace for data analysis and visualization
3. **Report Designer** - Create and customize detailed reports
4. **Dashboard** - View and manage all your visualizations
5. **Map Designer** - Create and customize geospatial visualizations

### Supported Visualizations
1. Line Chart
2. Bar Chart
3. Scatter Plot
4. Pie Chart
5. Area Chart
6. Bubble Chart
7. Histogram
8. Box Plot
9. Heatmap
10. Treemap
11. Maps (Geospatial Visualization)

## Chart Rules and Requirements

The following table outlines the requirements for each type of visualization:

| Rule | # Dates | # Dimensions | # Metrics |
|------|---------|-------------|-----------|
| 1    | 1       | 0           | 1         |
| 2    | 1       | 0           | 2         |
| 3    | 1       | 1           | 1         |
| 4    | 1       | 2           | 1         |
| 5    | 0       | 1           | 2         |
| 6    | 0       | 2           | 2         |
| 7    | 0       | 1           | 3         |
| 8    | 0       | 2           | 3         |
| 9    | 0       | Any         | 1         |
| 10   | Single Row | Any      | 1 to 4    |
| 11   | Maps always appear if there is a lat and lon column


## Configuration
Before running the application, ensure you have:
1. Valid Snowflake credentials
2. MapBox API key (for the background map for geospatial features) 
3. Proper database permissions


## How to Deploy the App
1. In Snowsight, open a SQL worksheet and run this with ACCOUNTADMIN to allow your env to see this GIT project: CREATE OR REPLACE API INTEGRATION git_sweingartner API_PROVIDER = git_https_api API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-sweingartner') ENABLED = TRUE;
2. Run the create_reports_table.sql script which will create the CortexChartsV3 database and schema, and create the two tables that hold report designs
3. click Projects > Streamlit
4. Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
5. Click "Create Git Repository"
6. In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV3
7. In the API Integration drop down box, choose GIT_SWEINGARTNER
8. Deploy it into the CortexChartsV3 database and CortexChartsV3 schema, and use any WH
9. Click Home.py then "Select File"
10. Click create
11. Open the code editor panel and edit which yaml files (i.e. semantic model) that the solution is looking at. You will find the line to alter at line 50 of the 1_Cortex_Analyst.py file
12. Edit the app in SiS and add the following packages via the drop down box above the code: altair, branca, h3-py, matplotlib-base, numpy, pandas, plotly, pydeck, scipy 
13. Run the App.
14. Note that background maps won't work until you set up mapbox.  

## How to Set Up Mapbox

### Prerequisites
- ACCOUNTADMIN role access in Snowflake
- A deployed Streamlit in Snowflake (SiS) app
- Database and schema information where your app is deployed

### Step-by-Step Setup

1. **Get Mapbox Access Token**:
   - Create/sign in to your account at mapbox.com
   - Go to Account Settings > Access Tokens
   - Copy your default public token or create a new one
   - Keep this token handy for the configuration

2. **Prepare Your App Information**:
   - Note your app's database and schema names
   - In Snowflake, run `SHOW STREAMLITS;` to find your app's unique identifier
   - Note the name you gave your app when creating it

3. **Configure the Script**:
   - Open `connectMapBox.sql` in your editor
   - Update the following variables at the top of the script:
     - `APP_CREATOR_ROLE` (usually 'ACCOUNTADMIN')
     - `DB_NAME` (your app's database)
     - `SCHEMA_NAME` (your app's schema)
     - `APP_NAME` (your Streamlit app name)
     - `MAPBOX_API_KEY` (your Mapbox token)
     - `YOUR_APP_ID` in the ALTER STREAMLIT statement

4. **Execute the Script**:
   - Connect to Snowflake as ACCOUNTADMIN
   - Execute each section of the script in sequence
   - Pay attention to the verification steps after each section
   - Fix any errors before proceeding to the next section

5. **Verify Setup**:
   - Refresh your Streamlit app
   - Open the Map Designer page
   - Confirm that map backgrounds load correctly

### Troubleshooting
If maps don't load:
- Verify all SHOW commands in the script return expected results
- Check that your Mapbox API key is valid
- Ensure your app ID is correct in the ALTER STREAMLIT statement
- Confirm all grants were successful
- Try refreshing your browser cache


Note that if you want to demo against the Synthea healthcare Dataset, refer to this Git and request a datashare: https://github.com/sfc-gh-sweingartner/synthea/tree/main

If you want to demo geospatial reporting against the telco network data, first install this project and leverage that yaml file (and thus the data): 
https://github.com/sfc-gh-sweingartner/network_optmise

Reach out to stephen.weingartner@snowflake.com with any issues.