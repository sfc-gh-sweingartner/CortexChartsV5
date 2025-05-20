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
3. You need to make SiS UI aware of the new DB.  Refreshing the dbs via the UI doesn't work.  So, refresh your entire browser (e.g. log out and in again or hit Control - Shift - R on a Mac )
4. click Projects > Streamlit
5. Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
6. Click "Create Git Repository"
7. In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV3
8. You can leave the repository name as the default
9. In the API Integration drop down box, choose GIT_SWEINGARTNER
10. Deploy it into the CortexChartsV3 database and CortexChartsV3 schema, and use any WH
11. Click Home.py then "Select File"
12. Choose the db CortexChartsV3 and schema CortexChartsV3
13. Name it CortexChartsV3 (You can rename after everything is working)
14. Choose any warehouse you want (maybe small or above) and click create
15. Open the code editor panel and edit which yaml file(s) (i.e. semantic model) that your solution is going to use.  You will find the line to alter at line 50 of the /pages/1_Cortex_Analyst.py file
16. Add the following packages via the drop down box above the code: altair, branca, h3-py, matplotlib-base, numpy, pandas, plotly, pydeck, scipy 
17. Click the blue "Run" button (It will take a minute to download all those map libraries)
18. Note that background maps won't work until you set up mapbox.  

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

2. **Get Your App's Auto-generated Name**:
   - In Snowsight, open a worksheet using the db and schema CortexChartsV3
   - Run `SHOW STREAMLITS;` in Snowflake
   - Find your app with title 'CortexChartsV3'
   - Copy its "name" value (this is an auto-generated ID like 'FFLFTTR_22W04CI0')

3. **Configure the Script**:
   - Open `connectMapBox.sql` in your editor
   - Update your Mapbox API key in the MAPBOX_API_KEY variable
   - Update the APP_NAME variable with your app's auto-generated name from step 2

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

Note the if you want to demo against synthea and / or the telco network and want a datashare, then send an email or Slack to stephen.weingartner@snowflake.com with your account details where I can do a direct share: 
SELECT CURRENT_ORGANIZATION_NAME() || '.' || CURRENT_ACCOUNT_NAME();


Reach out to stephen.weingartner@snowflake.com with any issues.