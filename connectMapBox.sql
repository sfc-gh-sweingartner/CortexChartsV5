-- Mapbox Integration Setup Script for Cortex Analyst V3
-- This script configures Mapbox integration in Snowflake for the Streamlit app
-- Prerequisites: ACCOUNTADMIN role access and valid Mapbox API key

---------------------------------------------------------------------------
-- STEP 1: Set Configuration Variables
---------------------------------------------------------------------------
-- Replace these values with your specific information before running
SET APP_CREATOR_ROLE = 'ACCOUNTADMIN';  -- Role that created the Streamlit app
SET DB_NAME = 'YOUR_DATABASE_NAME';      -- Database where your app is deployed
SET SCHEMA_NAME = 'YOUR_SCHEMA_NAME';    -- Schema where your app is deployed
SET APP_NAME = 'YOUR_APP_NAME';          -- Name you gave your app in Streamlit
SET MAPBOX_API_KEY = 'YOUR_MAPBOX_KEY';  -- Your Mapbox API key

-- Get your Streamlit app identifier
SHOW STREAMLITS;
-- Note: Find your app and copy its identifier (e.g., GO04L1G9G7UTYZDE)
-- You'll need this for the ALTER STREAMLIT command below

---------------------------------------------------------------------------
-- STEP 2: Create Network Rule for Mapbox Servers
---------------------------------------------------------------------------
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

-- Verify network rule creation
SHOW NETWORK RULES LIKE 'map_tile_rule';

---------------------------------------------------------------------------
-- STEP 3: Create Secret for Mapbox API Key
---------------------------------------------------------------------------
CREATE OR REPLACE SECRET mapbox_key
  TYPE = GENERIC_STRING
  SECRET_STRING = $MAPBOX_API_KEY;

-- Verify secret creation
SHOW SECRETS LIKE 'mapbox_key';

---------------------------------------------------------------------------
-- STEP 4: Create External Access Integration
---------------------------------------------------------------------------
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION map_access_int
  ALLOWED_NETWORK_RULES = (map_tile_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (mapbox_key)
  ENABLED = TRUE;

-- Verify integration creation
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'map_access_int';

---------------------------------------------------------------------------
-- STEP 5: Grant Necessary Privileges
---------------------------------------------------------------------------
-- Grant access to the secret
GRANT READ ON SECRET mapbox_key 
  TO ROLE IDENTIFIER($APP_CREATOR_ROLE);

-- Grant access to the integration
GRANT USAGE ON INTEGRATION map_access_int 
  TO ROLE IDENTIFIER($APP_CREATOR_ROLE);

---------------------------------------------------------------------------
-- STEP 6: Configure Streamlit App Access
---------------------------------------------------------------------------
-- Replace YOUR_APP_ID with your Streamlit app identifier from STEP 1
ALTER STREAMLIT IDENTIFIER($DB_NAME).IDENTIFIER($SCHEMA_NAME).YOUR_APP_ID
  SET EXTERNAL_ACCESS_INTEGRATIONS = (map_access_int)
  SECRETS = ('mapbox_key' = mapbox_key);

---------------------------------------------------------------------------
-- STEP 7: Verify Final Configuration
---------------------------------------------------------------------------
-- Run these commands to verify all components are properly configured
SHOW NETWORK RULES LIKE 'map_tile_rule';
SHOW SECRETS LIKE 'mapbox_key';
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'map_access_int';
SHOW STREAMLITS;

---------------------------------------------------------------------------
-- Troubleshooting Guide
---------------------------------------------------------------------------
-- If you encounter issues:
-- 1. Verify all SHOW commands return expected results
-- 2. Ensure your app ID is correct in the ALTER STREAMLIT statement
-- 3. Confirm your Mapbox API key is valid
-- 4. Check that your role has ACCOUNTADMIN privileges
-- 5. Verify the database and schema names match your deployment
-- 6. Try refreshing your Streamlit app after configuration 