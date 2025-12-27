@echo off
:: 1. Navigate to your project folder
cd /d "C:\Users\user\Documents\AIR-QUALITY-IN-NAKURU"

:: 2. Ensure the Docker Postgres container is running
echo Starting Docker Postgres Container (nakuru-db)...
docker start nakuru-db

:: 3. Activate the conda environment
call "C:\Users\user\anaconda3\Scripts\activate.bat" "C:\Users\user\anaconda3\envs\nakuru-env"

:loop
cls
echo ==================================================
echo NAKURU AIR QUALITY PIPELINE: %DATE% %TIME%
echo ==================================================

:: 4. Run Sync (Fetch new data)
echo [STEP 1/2] Syncing latest sensor data from OpenAQ...
python nakuru-sync.py

:: 5. Run Audit (Check data quality and prep for model)
echo [STEP 2/2] Running Statistical Audit (ADF Test + Seasonality)...
python data_audit.py

echo.
echo SUCCESS: Pipeline cycle finished. 
echo Next update in 30 minutes. Press Ctrl+C to stop.
echo ==================================================

:: 6. Wait for 30 minutes (1800 seconds)
timeout /t 1800 /nobreak
goto loop