-- Mapbox Keyless Configuration Script
-- This script configures network access for Mapbox tiles in Snowflake for the Streamlit app,
-- relying on Streamlit's default map rendering capabilities without requiring a personal API key.
-- Prerequisites: ACCOUNTADMIN role access.
-- Last updated: May 29, 2024

---------------------------------------------------------------------------
-- STEP 1: Set Configuration Variables
---------------------------------------------------------------------------
SET APP_CREATOR_ROLE = 'ACCOUNTADMIN';
-- No need for Mapbox API key anymore
SET DB_NAME = 'CortexChartsV4';  
SET SCHEMA_NAME = 'CortexChartsV4';    
SET APP_NAME = 'CortexChartsV4';   

Use DATABASE  IDENTIFIER($DB_NAME);
Use SCHEMA  IDENTIFIER($SCHEMA_NAME);

---------------------------------------------------------------------------
-- STEP 2: Create Network Rule for Mapbox Servers
---------------------------------------------------------------------------
-- This rule allows egress to Mapbox tile servers, which st.map() and pydeck use by default.
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
-- STEP 3: Create External Access Integration
---------------------------------------------------------------------------
-- The integration only references the network rule, no API key secret needed
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION map_access_int
  ALLOWED_NETWORK_RULES = (map_tile_rule)
  ENABLED = TRUE;

-- Verify integration creation
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'map_access_int';

---------------------------------------------------------------------------
-- STEP 4: Grant Necessary Privileges
---------------------------------------------------------------------------
-- Grant access to the integration
GRANT USAGE ON INTEGRATION map_access_int
  TO ROLE IDENTIFIER($APP_CREATOR_ROLE);

---------------------------------------------------------------------------
-- STEP 5: Configure Streamlit App Access
---------------------------------------------------------------------------
-- Run SHOW STREAMLITS; first to find your app's auto-generated name
SHOW STREAMLITS;

-- Then use the app name from the SHOW STREAMLITS output in the command below
-- IMPORTANT: Replace with your actual Streamlit app name
ALTER STREAMLIT IDENTIFIER('YOUR_STREAMLIT_APP_NAME')
  SET EXTERNAL_ACCESS_INTEGRATIONS = (map_access_int);


-- Example of ALTER STREAMLIT command:
-- ALTER STREAMLIT TELCO_NETWORK_OPTIMIZATION_PROD.RAW.FQYVZ89K8QDAWHRK
--   SET EXTERNAL_ACCESS_INTEGRATIONS = (map_access_int);

---------------------------------------------------------------------------
-- STEP 6: Verify Final Configuration
---------------------------------------------------------------------------
-- Run these commands to verify all components are properly configured
SHOW NETWORK RULES LIKE 'map_tile_rule';
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'map_access_int';
SHOW STREAMLITS; -- Check your app's configuration

---------------------------------------------------------------------------
-- Troubleshooting Guide
---------------------------------------------------------------------------
-- If you encounter issues:
-- 1. Verify all SHOW commands return expected results for the objects.
-- 2. Ensure your app name is correct in the ALTER STREAMLIT statement.
-- 3. Confirm your role has ACCOUNTADMIN privileges.
-- 4. Verify the database and schema names match your deployment.
-- 5. Try refreshing your Streamlit app after configuration.
-- 6. If maps still don't appear, check the Network Logs in your browser's developer tools.
--    Look for requests to Mapbox servers and check if there are any errors.
-- 7. If all else fails, you might need to use a personal Mapbox API key.
--    In that case, refer to the original mapbox_access_setup.sql script. 