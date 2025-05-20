---This secript can be run to enable mapbox integration in Snowflake
-- This script is for the Cortex Analyst V3 app
-- you need to modify the mapbox key, database name, schema name, and app below to match your own environment

show streamlits;

--note in my case the name is GO04L1G9G7UTYZDE which is pasted below.  
--run the following in the db where your streamlit was installed
-- Replace these values with your specific information
-- SET VARIABLES
SET APP_CREATOR_ROLE = 'ACCOUNTADMIN'; 
SET DB_NAME = 'QUANTIUM_DEMO';  
SET SCHEMA_NAME = 'TEXT2SQL';    
SET APP_NAME = 'Cortex Analyst V3';   
SET MAPBOX_API_KEY = '[paste your mapbox api key here]';      -- Your Mapbox API key

-- Create network rule for map tile servers
CREATE OR REPLACE NETWORK RULE map_tile_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = (
    'api.mapbox.com', 
    'a.tiles.mapbox.com', 
    'b.tiles.mapbox.com', 
    'c.tiles.mapbox.com', 
    'd.tiles.mapbox.com'
  );

-- Create secret for Mapbox API key
CREATE OR REPLACE SECRET mapbox_key
  TYPE = GENERIC_STRING
  SECRET_STRING = $MAPBOX_API_KEY;

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION map_access_int
  ALLOWED_NETWORK_RULES = (map_tile_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (mapbox_key)
  ENABLED = TRUE;

-- Grant necessary privileges
GRANT READ ON SECRET mapbox_key TO ROLE IDENTIFIER($APP_CREATOR_ROLE);
GRANT USAGE ON INTEGRATION map_access_int TO ROLE IDENTIFIER($APP_CREATOR_ROLE);

--find the name of your streamlit app
  show streamlits;

-- Enable the Streamlit app to use the integration and secret
-- note you will need to change the streamlit app name to match the one you are using
ALTER STREAMLIT QUANTIUM_DEMO.TEXT2SQL.GO04L1G9G7UTYZDE
  SET EXTERNAL_ACCESS_INTEGRATIONS = (map_access_int)
  SECRETS = ('mapbox_key' = QUANTIUM_DEMO.TEXT2SQL.mapbox_key);

  
-- Verify configuration
SHOW NETWORK RULES LIKE 'map_tile_rule';
SHOW SECRETS LIKE 'mapbox_key';
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'map_access_int'; 
SHOW SECRETS LIKE 'mapbox_key' IN TELCO_NETWORK_OPTIMIZATION_PROD.RAW;

-- note you will need to change the streamlit app name to match the one you are using
 ALTER STREAMLIT QUANTIUM_DEMO.TEXT2SQL.GO04L1G9G7UTYZDE
  SET EXTERNAL_ACCESS_INTEGRATIONS = (map_access_int)
  SECRETS = ('mapbox_key' = mapbox_key);

 