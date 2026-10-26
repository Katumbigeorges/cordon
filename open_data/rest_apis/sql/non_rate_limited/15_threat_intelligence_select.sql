-- Read-only verification for 15_threat_intelligence_create.sql.
SELECT cve, kev_due_date FROM threat.kev WHERE cve = 'CVE-2021-44228';
SELECT cve, epss, epss_percentile FROM threat.epss WHERE cve IN ('CVE-2021-44228', 'CVE-2024-99999');
