# Zetaris Registration SQL Scripts

These SQL scripts register hospital data and threat intelligence sources in Zetaris Lightning.

## Prerequisites

1. **Zetaris running:** Confirm at http://localhost:3000
2. **PostgreSQL running:** Confirm with `docker ps` (should show postgres container)
3. **API Key created:** In Zetaris GUI → Settings → API Keys

## Registration Steps

### 1. Verify Zetaris Connection

```bash
# Test Zetaris REST API
curl -H "Authorization: Bearer $ZETARIS_API_KEY" \
     -H "X-Org-ID: 1" \
     http://localhost:8888/api/v1.0/datasource/datasources
```

### 2. Register Hospital Data (Postgres)

Open Zetaris SQL Editor (http://localhost:3000) and run:

```sql
-- Copy and paste from: 01_hospital_postgres.sql
```

**Expected Output:**
```
Tables in hospital:
- assets
- firewall_rules
- credentials_map
- scan_findings
- telemetry
- risk_acceptances
```

**Verify:**
```sql
SELECT COUNT(*) FROM hospital.assets;
-- Should return: 28 (if data is seeded)
```

### 3. Register Threat Intelligence

Run in SQL Editor:

```sql
-- Copy and paste from: 02_threat_rest.sql
```

**Note:** This uses the Postgres fallback approach. REST API registration may need adjustments based on CISA/FIRST API availability.

### 4. Test Queries

```sql
-- Test hospital data
SELECT * FROM hospital.assets WHERE internet_facing = true LIMIT 5;

-- Test join between hospital and threat data
SELECT 
    s.asset_id,
    s.cve,
    k.kev,
    e.epss
FROM hospital.scan_findings s
LEFT JOIN threat.kev k ON s.cve = k.cve
LEFT JOIN threat.epss e ON s.cve = e.cve
WHERE k.kev = true
LIMIT 10;
```

## Troubleshooting

### Error: "cannot reach host.docker.internal"

**On Linux:** Replace `host.docker.internal` with `172.17.0.1` (Docker bridge IP)

**On Mac/Windows:** Should work as-is

### Error: "authentication failed"

Check PostgreSQL credentials in docker-compose.yml:
```yaml
POSTGRES_USER=zetaris
POSTGRES_PASSWORD=zt-metastore-6f2a9c41d0b7
```

### Error: "database 'cordon' does not exist"

Seed the database:
```bash
cd cordon
make seed  # Or: python data_gen/generate.py
```

### Error: "table already exists"

Use `CREATE OR REPLACE TABLE` or drop first:
```sql
DROP TABLE IF EXISTS hospital.assets;
```

## Fallback Mode

If Zetaris registration fails, the application falls back to sample data automatically.

Check `logs/full-solution-test.jsonl` for:
```json
{
  "zetaris": {
    "live": false,
    "hospital_data_via_zetaris": false
  }
}
```

## Integration Status

After registration, update `.env`:
```bash
ZETARIS_LIVE=true
```

Then run:
```bash
python run_full_solution.py
```

Check for:
```
Live Zetaris: True
hospital_data_via_zetaris: true
```

## Reference

- **Zetaris Docs:** Check participant setup guide
- **Postgres Connection:** jdbc:postgresql://host.docker.internal:5432/cordon
- **Zetaris REST API:** http://localhost:8888/api/v1.0
- **Zetaris UI:** http://localhost:3000
