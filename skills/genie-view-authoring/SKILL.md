# SKILL: Genie View Authoring

Apply when generating SQL views consumed by a Databricks Genie agent.

## Hard rules
1. **No `SELECT *`** — every column listed explicitly.
2. **Every column has a `COMMENT`** in business English (Genie uses these as glossary).
3. **Every view has a `COMMENT`** including 1-2 example natural-language questions.
4. **Deterministic `ORDER BY`** — Genie sample previews must be reproducible.
5. Use **business-friendly aliases** (`avg_value` → "Average Median Home Value (USD 100k)").
6. Views live in `gold` (or `business_metrics`) — never expose `bronze` / `silver` to Genie.
7. Numeric KPIs include the **unit** in the comment (USD, miles, %, count).

## Pattern
```sql
CREATE OR REPLACE VIEW kpi_testing.gold.vw_taxi_demand_heatmap
COMMENT 'Trip demand by city, weekday, hour.
Sample questions: "Which hour has the highest demand in NYC?"
                  "Compare weekend vs weekday demand in London."'
AS
SELECT
  city_tag        AS city,
  pickup_weekday  AS weekday_num,
  pickup_hour     AS hour_of_day,
  trip_count,
  avg_distance,
  total_passengers
FROM kpi_testing.gold.gold_global_taxi_demand
ORDER BY city, pickup_weekday, pickup_hour;

ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN city            COMMENT 'City code (NYC or LONDON).';
ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN weekday_num     COMMENT 'Day of week (0=Monday ... 6=Sunday).';
ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN hour_of_day     COMMENT 'Hour of day in local time (0-23).';
ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN trip_count      COMMENT 'Number of taxi trips in the bucket (count).';
ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN avg_distance    COMMENT 'Average trip distance (miles for NYC, km for London).';
ALTER VIEW kpi_testing.gold.vw_taxi_demand_heatmap
  ALTER COLUMN total_passengers COMMENT 'Total passengers carried in the bucket.';
```

## Forbidden
- Joins inside Genie views unless a documented stable key exists.
- Subqueries deeper than 1 level — push complexity to a gold table.
- Time-zone-naive comments — say "UTC" or "local" explicitly.
