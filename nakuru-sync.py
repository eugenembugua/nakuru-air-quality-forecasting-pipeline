# Importing the dependencies
import pandas as pd
import requests
import numpy as np
import joblib
import json
import psycopg2
from psycopg2.extras import Json
import datetime

# Reading the secrets file
try:
    with open("secrets.json", "r") as f:
        secrets = json.load(f)
except FileNotFoundError:
    print("Error: secrets.json file missing.")
    exit()
    
# Grab credentials from secrets file
openaq_key = secrets.get("openaq-api-key")

def sync_latest_nakuru_readings():
    # Configuration
    location_id = secrets.get("location_id")
    url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    headers = {"X-API-Key": openaq_key} 

    conn = None
    try:
        # 1. Connect to the Database
        conn = psycopg2.connect(
            host=secrets.get("db_host"),
            dbname=secrets.get("db_name"),
            user=secrets.get("db_user"),
            password=secrets.get("db_password"),
            port="5432"
        )
        cur = conn.cursor()

        # 2. Ensure table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS nakuru_air_quality_readings (
            id SERIAL PRIMARY KEY,
            location_id INT,
            captured_at_utc TIMESTAMP UNIQUE,
            pm25_value NUMERIC,
            raw_json JSONB
        );
        """
        cur.execute(create_table_query)
        conn.commit()

        # 3. Fetch data from OpenAQ API
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        # 4. FILTER & SORT LOGIC
        # Filter for only PM2.5 sensors at this location
        pm25_options = [r for r in results if r.get('parameter', {}).get('name') == "pm25"]

        if pm25_options:
            # Sort by UTC time descending (Newest first)
            pm25_options.sort(key=lambda x: x['datetime']['utc'], reverse=True)
            
            # Pick the absolute latest reading
            pm25_record = pm25_options[0]
            
            val = pm25_record['value']
            ts = pm25_record['datetime']['utc']
            s_id = pm25_record['sensorsId']

            # 5. UPSERT into Postgres
            insert_query = """
                INSERT INTO nakuru_air_quality_readings (location_id, captured_at_utc, pm25_value, raw_json)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (captured_at_utc) DO NOTHING;
            """
            cur.execute(insert_query, (
                location_id, 
                ts, 
                val, 
                Json(results)
            ))
            conn.commit()
            print(f"--- SYNC SUCCESSFUL ---")
            print(f"Latest PM2.5: {val} µg/m³")
            print(f"Timestamp:    {ts}")
            print(f"Sensor ID:    {s_id}")
            print(f"-----------------------")
        else:
            print("No current PM2.5 data found from API response.")

    except Exception as e:
        print(f"Error syncing data: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

# The Execution Block (Triggered by runsync.bat)
if __name__ == "__main__":
    sync_latest_nakuru_readings()