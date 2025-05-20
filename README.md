# CortexCharts V3

CortexCharts is a powerful visualization tool designed to work seamlessly with Snowflake, offering an intuitive interface for creating and managing various types of charts and visualizations. This tool is perfect for data analysts and business users who want to create compelling visual representations of their data.

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
2. MapBox API key (for geospatial features)
3. Proper database permissions

## How to Deploy
1. In Snowsight, open a SQL worksheet and run this with ACCOUNTADMIN to allow your env to see this GIT project: CREATE OR REPLACE API INTEGRATION git_sweingartner API_PROVIDER = git_https_api API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-sweingartner') ENABLED = TRUE;
2. click Projects > Streamlit
3. Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
4. Click "Create Git Repository"
5. In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexChartsV3
6. In the API Integration drop down box, choose GIT_SWEINGARTNER
7. Deploy it into any DB, Schema and use any WH
8. Click Home.py then "Select File"
9. Click create
10. Open the code editor panel and edit which yaml files (i.e. semantic model) that the solution is looking at. You will find the line to alter at line 50 of the 1_Cortex_Analyst.py file
11. Edit the app in SiS and add the following packages via the drop down box above the code: altair, branca, h3-py, matplotlib-base, numpy, pandas, plotly, pydeck, scipy 
12. Run the App.

Note that if you want to demo against the Synthea healthcare Dataset, refer to this Git and request a datashare: https://github.com/sfc-gh-sweingartner/synthea/tree/main

If you want to demo geospatial reporting against the telco network data, first install this project and leverage that yaml file (and thus the data): 
https://github.com/sfc-gh-sweingartner/network_optmise

Reach out to stephen.weingartner@snowflake.com with any issues.