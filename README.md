# Nakuru Air Quality: End-to-End Forecasting Pipeline
> **A Data Engineering & Time-Series Project**

## Project Overview
This repository contains a full-stack data pipeline designed to collect, process, and forecast air quality (PM2.5) for **Nakuru, Kenya**. The project integrates cloud storage, high-performance analytical querying, and real-time data auditing to provide a continuous dataset for 2025 forecasting.

## System Architecture
The pipeline follows a multi-stage process to ensure data integrity:

Historical Extraction: Data is pulled from Amazon S3 storage.
Analytical Querying: DuckDB is used to perform high-speed SQL queries on the S3 dataset for initial exploration.
Real-Time Ingestion: Latest sensor readings are fetched via the OpenAQ API.
Data Merging: Historical and real-time data are unified and loaded into a PostgreSQL database (running in Docker).
Statistical Audit: Automated ADF Tests validate data stationarity for the time-series model.Visualization: A Streamlit dashboard displays the final forecasts and sensor trends.

## Tech Stack
Cloud: Amazon S3
Databases: DuckDB (Analysis), PostgreSQL (Production/Docker)
Modeling: Time Series Forecasting
Frontend: Streamlit
Automation: Windows Batch Scripting
Environment: Conda (nakuru-env)

## Prerequisites:
Before running the pipeline, ensure you have:
Docker Desktop: Installed and running (for the Postgres container).
Conda/Anaconda: To manage the Python environment.
Access: Valid API keys for OpenAQ and AWS CLI configured for S3 access.

### How to Run the Project
1. Setup EnvironmentThis project uses a lean requirements.txt generated via pipreqs . --force.

pip install -r requirements.txt

2. Start the Automation
The entire backend process—starting the database, activating the environment, syncing data, and auditing—is handled by a single orchestrator.
Run the automated loop

run-sync.bat

Note: This script refreshes data every 30 minutes. Press Ctrl + C to stop.

3. Launch the DashboardTo see the interactive forecast and live data

streamlit run app.py

Key File Descriptions:

1. run-sync.bat: The "Orchestrator." Manages Docker and runs the 30-minute data refresh cycle.

2. nakuru-sync.py: Merges S3 historical data with OpenAQ API live feeds.

3. data_audit.py: Statistical validation script (ADF & Seasonality tests).

4. app.py: Streamlit UI code for data visualization.

5. requirements.txt: Minimalist dependency list.

Data Dictionary:

PM2.5 Fine particulate matter (<2.5 µm)

ADF Test Augmented Dickey-Fuller Test
