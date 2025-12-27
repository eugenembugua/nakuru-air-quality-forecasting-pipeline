import duckdb

def migrate_s3_to_postgres():
    ddb = duckdb.connect("nakuru_air_quality.db")
    
    # 1. Load extensions
    ddb.execute("INSTALL postgres; LOAD postgres;")
    ddb.execute("INSTALL httpfs; LOAD httpfs;")
    
    # 2. Configure S3
    ddb.execute("SET s3_region='us-east-1';")
    ddb.execute("SET s3_access_key_id='';")
    ddb.execute("SET s3_secret_access_key='';")

    # 3. Attach Postgres
    pg_config = "host=localhost port=5432 dbname=postgres user=postgres password=password"
    ddb.execute(f"ATTACH '{pg_config}' AS my_pg_db (TYPE postgres);")

    location_id = 1894637
    year = 2025
    file_path = f"s3://openaq-data-archive/records/csv.gz/locationid={location_id}/year={year}/month=*/location-{location_id}-{year}*.csv.gz"

    print(f"Pulling S3 data and filtering duplicates manually...")
    
    try:
        # We use a 'LEFT JOIN' to only insert rows that don't exist in Postgres yet
        # This bypasses the need for DuckDB to 'see' the UNIQUE index
        ddb.execute(f"""
            INSERT INTO my_pg_db.nakuru_air_quality_readings (location_id, captured_at_utc, pm25_value)
            SELECT 
                s3.location_id, 
                s3.datetime::TIMESTAMP as captured_at_utc, 
                s3.value as pm25_value
            FROM read_csv('{file_path}') AS s3
            LEFT JOIN my_pg_db.nakuru_air_quality_readings AS pg
                   ON s3.datetime::TIMESTAMP = pg.captured_at_utc
            WHERE s3.parameter = 'pm25'
              AND pg.captured_at_utc IS NULL;
        """)
        print("Success! Historical data is now merged.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        ddb.execute("DETACH my_pg_db;")

if __name__ == "__main__":
    migrate_s3_to_postgres()