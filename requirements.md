
## Cursor behaviour
1. If I issue you a challenging task where there are several options or confusion in my request, then ask me questions and / or give me options before proceeding with any code changes
2. While we are starting a task, I will enjoy your creativity.  However, as we progress through a task in debugging and testing I do not want creativity.  I want minimal changes to fix problems.  
3. If I ask you to do something that is is in conflict with any of the rules files, then make the related change to the rules files so that I can review the change

## high level design
CortexCharts is a Streamlit in Snowflake app that offers an intuitive interface for creating and managing various types of charts and visualizations against Cortex Analyst. This tool is perfect for data analysts and business users who want to use Text 2 SQL to create compelling visual representations of their data.  

## Architecture and Tech requirements:
This is built for Streamlit in Snowflake and can also be run locally on a laptop for development and testing.  

Limit python libraries to using those available on this anaconda channel:  
https://repo.anaconda.com/pkgs/snowflake/

The app will have access to a Snowflake database but default the app will not have access to external data.  It also has access to an API and license key to enable the mapbox charting.   When needed, you can assist the developer to set up external network connections, API keys, etc... to connect to external information


##  Detailed design
1. For the existing designs, see: map-designer-page.mdc and chart-system.mdc for the existing designs. 


## Project Tasks - Enhancement
Your task as part of this project is to do the following which will be accomplished in phases rather than all in one-shot.  I would like you to break this out into sensible phases that can be developed and tested independently.  The main goal of this enhancemment is to allow users to see which columns are available in the semantic model so that they can choose them and form a very precise prompt which they can then pass into the Cortex Analyst LLM.  
1. Look at the included example semantic model (*.yaml) and the Snowflake documentation for these:  https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/semantic-model-spec the main goal of this enhancement is that we want the users to be able to see this information in the streamlit app and use it.  I have one model to build for and two to test against.  Typically each yaml files will have between 50 and 300 columns
2. You will generate some code that can parse any snowflake semantic model yaml file and provide users the ability to view this information in a list.  This list will appear in the left menu under the SQL Execututon mode buttons on 1_Cortex_analyst page.  This list is based on which yaml file was selected in the drop down box on that left menu
3. Allow users to scroll up and down select multiple columns from that list via tick boxes.  When the user hovers over the columns they can see the column name.  They can also see the table column name, column type (i.e. metric, dimension or date) and also the business definition of that column
4. The action of step three will generate a new table right under the list in step 3.  This new table will have one row for each selected column this table will have three columns.  The columns are column name, results, and filter.  The column name is simply the name of the column from step 3.   The results column allows the user to state that they want to see this column in the results.  Drop down box options are (Group BY, Sum, Count, Avg, Min, Max, Don't Show)   The filter column is default "Don't Filter"  but the user can override that text and type anything they want in English (e.g. chocolate bars)  Note that the samantic model defines the joins so the users will not need to guide joins
5. Under the table of task 4 is a button that a user can push to "Generate Prompt".  When they push this, an English statement appears in the "What is your question?" field at the bottom of the page.   You will generate a prompt with phrases like "Show me" "Grouped By" "where" "equals"  "greater than" for example, you will make a statement like: "Show me Store ID and Sum of Sales Retail WHERE it is filtered by Financial Year = 2021 Group by Store ID"  Note the goal here is that this prompt will allow the LLM to produce a more accurate SQL statement than a vague request.
6. This task is a future task.  For the first phase above, I expect only 1_Cortex_Analyst will need to change.  But in a future phase, I am then going to ask that all of the pages are modifed so that all pages are aware of the semantic model.  Right now, what happens is that on 1_Cortex_Analyst a user asks a question and then SQL is run and data is retuned.  A table exists with table column names.  The business name of the column was lost.  Additionally, whether that column is a date, dimension or metric was also lost.   As part of the existing solution, it looks at the dataframe and it identifies whether a column is a number or a string or a date or a lat, lon and based on that it makes charts.  I will also want it to understand whether the column is a dimension or a metric and what is the business name and that should reflect in reports.  So, looking forward, I'm thiking that when the user selects some columns in step 3, the related information from the YAML file is saved and passed on to the other pages.  



## Documentation
1. You will create end user documentation so they know how to use the app.  This should appear in a single page within the app
2. Code should have a lot of comments to make it easy for humans to understand
3. The rules documents will act as the functional and technical designs and you will update these accordingly as we progress with the design and development of the app 


## Optional: Version Control Guidelines
1. I have a git repository already created.  
2. I will ask you to push changes and then I will test them in that Streamlit in Snowflake environment
