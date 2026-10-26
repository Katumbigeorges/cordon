-- Cordon scenario threat intelligence sources.
-- Run through scripts/onboard.py after reviewing the endpoint and license notes.
-- This is intentionally not executed automatically: it creates Zetaris objects.
-- Sources: CISA KEV (public domain feed) and FIRST EPSS API.

CREATE LIGHTNING DATABASE THREAT_REST DESCRIBE BY "Cordon threat intelligence REST sources";
CREATE SCHEMASTORE CONTAINER threat;

CREATE LIGHTNING REST TABLE kev_raw FROM THREAT_REST REQUEST(
    endpoint "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
    User-Agent "zetaris dev@zetaris.com"
) BODY ();

CREATE SCHEMASTORE VIEW kev WITH CONTAINER threat AS
SELECT
    vulnerability.cveID AS cve,
    vulnerability.dateAdded,
    vulnerability.dueDate AS kev_due_date,
    vulnerability.knownRansomwareCampaignUse
FROM threat_rest.kev_raw
LATERAL VIEW explode(vulnerabilities) AS vulnerability;

CREATE LIGHTNING REST TABLE epss_log4shell_raw FROM THREAT_REST REQUEST(
    endpoint "https://api.first.org/data/v1/epss?cve=CVE-2021-44228",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
    User-Agent "zetaris dev@zetaris.com"
) BODY ();

CREATE LIGHTNING REST TABLE epss_pharmacy_raw FROM THREAT_REST REQUEST(
    endpoint "https://api.first.org/data/v1/epss?cve=CVE-2024-99999",
    method "get",
    response_type "json",
    http_encoding "URLENCODED"
) HEADER (
    User-Agent "zetaris dev@zetaris.com"
) BODY ();

CREATE SCHEMASTORE VIEW epss WITH CONTAINER threat AS
SELECT row.cve, row.epss, row.percentile AS epss_percentile
FROM threat_rest.epss_log4shell_raw
LATERAL VIEW explode(data) AS row
UNION ALL
SELECT row.cve, row.epss, row.percentile AS epss_percentile
FROM threat_rest.epss_pharmacy_raw
LATERAL VIEW explode(data) AS row;
