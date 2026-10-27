-- Register PostgreSQL data source for hospital data
-- Run this in Zetaris SQL Editor BEFORE running the Cordon application

-- Step 1: Create Lightning database for hospital data
CREATE LIGHTNING DATABASE IF NOT EXISTS hospital;

-- Step 2: Register PostgreSQL data source
-- Note: Replace connection details with your actual Postgres configuration
-- The Cordon docker-compose.yml runs Postgres on host.docker.internal:5432

REGISTER OR REPLACE DATASOURCE POSTGRES hospital_db
OPTIONS(
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Step 3: Create tables in Lightning database that map to Postgres tables
-- These make the Postgres tables queryable through Zetaris

-- Assets table
CREATE OR REPLACE TABLE hospital.assets
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.assets',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Firewall rules table
CREATE OR REPLACE TABLE hospital.firewall_rules
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.firewall_rules',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Credentials map table
CREATE OR REPLACE TABLE hospital.credentials_map
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.credentials_map',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Scan findings table
CREATE OR REPLACE TABLE hospital.scan_findings
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.scan_findings',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Telemetry table
CREATE OR REPLACE TABLE hospital.telemetry
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.telemetry',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Risk acceptances table
CREATE OR REPLACE TABLE hospital.risk_acceptances
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:postgresql://host.docker.internal:5432/cordon',
  dbtable 'public.risk_acceptances',
  driver 'org.postgresql.Driver',
  user 'zetaris',
  password 'zt-metastore-6f2a9c41d0b7'
);

-- Verify registration
SHOW TABLES IN hospital;
