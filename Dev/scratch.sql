SELECT $1 FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml';

SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml'
(FILE_FORMAT => (TYPE => CSV, FIELD_DELIMITER => NONE, EMPTY_FIELD_AS_NULL => FALSE, SKIP_HEADER => 0, TRIM_SPACE => FALSE, NULL_IF => (''))); -- Adjust NULL_IF and other options as needed


use database synthea;
use schema synthea; 

CREATE OR REPLACE FILE FORMAT my_raw_text_format
  TYPE = CSV
  FIELD_DELIMITER = NONE
  EMPTY_FIELD_AS_NULL = FALSE
  TRIM_SPACE = FALSE
  NULL_IF = (''); -- Adjust as needed

-- Then use it in your SELECT
SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml'
(FILE_FORMAT => 'my_raw_text_format');


SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml' -- Adjust quoting if necessary
(
    FILE_FORMAT => (
        TYPE => CSV,
        FIELD_DELIMITER => NONE,
        EMPTY_FIELD_AS_NULL => FALSE,
        SKIP_HEADER => 0,
        TRIM_SPACE => FALSE,
        NULL_IF => () -- Consider this if you don't want 'NONE' or 'NULL' strings to become SQL NULLs
    )
);


SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml' -- Or @SYNTHEA.SYNTHEA.SYNTHEA/syntheav5.yaml
(
    FILE_FORMAT => (
        TYPE => CSV,  -- This uses =>
        FIELD_DELIMITER = NONE, -- Subsequent options use = and are comma-separated
        EMPTY_FIELD_AS_NULL = FALSE,
        SKIP_HEADER = 0,
        TRIM_SPACE = FALSE,
        NULL_IF = ('NONE', 'NULL') -- Or NULL_IF = () if you prefer
    )
);

SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml' -- Or @SYNTHEA.SYNTHEA.SYNTHEA/syntheav5.yaml
(
    FILE_FORMAT => (
        TYPE => CSV,                    -- Uses =>
        FIELD_DELIMITER => NONE,         -- Changed from = to =>
        EMPTY_FIELD_AS_NULL => FALSE,    -- Changed from = to =>
        SKIP_HEADER => 0,                -- Changed from = to =>
        TRIM_SPACE => FALSE,             -- Changed from = to =>
        NULL_IF => ('NONE', 'NULL')      -- Changed from = to => (adjust NULL_IF list as needed)
    )
);

SELECT $1
FROM '@"SYNTHEA"."SYNTHEA"."SYNTHEA"/syntheav5.yaml' -- Or @SYNTHEA.SYNTHEA.SYNTHEA/syntheav5.yaml
(
    TYPE => CSV,
    FIELD_DELIMITER => NONE,
    EMPTY_FIELD_AS_NULL => FALSE,
    SKIP_HEADER => 0,
    TRIM_SPACE => FALSE
);