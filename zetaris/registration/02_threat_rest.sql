-- Register external threat intelligence sources as REST tables
-- Run this in Zetaris SQL Editor AFTER registering hospital data

-- Step 1: Create Lightning database for threat intelligence
CREATE LIGHTNING DATABASE IF NOT EXISTS threat;

-- Step 2: Register KEV (CISA Known Exploited Vulnerabilities)
-- Option A: REST API registration (preferred if available)
-- CREATE LIGHTNING REST TABLE threat.kev
-- OPTIONS (
--   url 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
--   format 'json',
--   path 'vulnerabilities'
-- );

-- Option B: Fallback to Postgres copy (if REST not working)
CREATE OR REPLACE TABLE threat.kev
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.kev_data',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Step 3: Register EPSS (Exploit Prediction Scoring System)
-- Option A: REST API registration (preferred if available)
-- CREATE LIGHTNING REST TABLE threat.epss
-- OPTIONS (
--   url 'https://api.first.org/data/v1/epss',
--   format 'json'
-- );

-- Option B: Fallback to Postgres copy (if REST not working)
CREATE OR REPLACE TABLE threat.epss
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.epss_data',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Verify registration
SHOW TABLES IN threat;

-- Test queries
SELECT COUNT(*) as kev_count FROM threat.kev;
SELECT COUNT(*) as epss_count FROM threat.epss;
