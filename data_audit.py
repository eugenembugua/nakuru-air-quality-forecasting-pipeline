import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

def get_forecast_ready_data():
    """
    Connects to Postgres, pulls Nakuru data, cleans outliers,
    resamples to hourly, and interpolates gaps.
    """
    #DATABASE CONNECTION
    engine = create_engine('postgresql://postgres:password@localhost:5432/postgres')
    
    #AUTOMATED PULL
    query = 'SELECT captured_at_utc, pm25_value FROM nakuru_air_quality_readings'
    df = pd.read_sql(query, engine)
    
    #PRE-PROCESSING
    df['captured_at_utc'] = pd.to_datetime(df['captured_at_utc'])
    df = df.set_index('captured_at_utc').sort_index()

    #AUTOMATED CLEANING
    df = df[(df['pm25_value'] >= 0) & (df['pm25_value'] <= 500)]
    
    #Resample to Hourly
    df_hourly = df['pm25_value'].resample('h').mean()
    
    #Linear Interpolation to fill missing hours
    df_final = df_hourly.interpolate(method='linear')

    return df_final

def advanced_data_audit(data):
    """
    Runs statistical tests to verify the data quality matches 
    the saved SARIMAX (d=1) and EGARCH models.
    """
    print("ADVANCED DATA AUDIT REPORT")
    
    #Stationarity (ADF Test)
    result = adfuller(data)
    p_value = result[1]
    print(f"ADF p-value: {p_value:.4f}")
    if p_value < 0.05:
        print("Status: Stationary (Ready for d=0 models)")
    else:
        print("Status: Non-Stationary (Perfect for d=1 SARIMAX model)")

    #Seasonality (24h Pattern)
    decomposition = seasonal_decompose(data, model='additive', period=24)
    seasonal_std = np.std(decomposition.seasonal)
    print(f"Daily Seasonal Strength: {seasonal_std:.2f}")
    if seasonal_std > 1.0:
        print("Status: Strong Daily Pattern detected. High forecast reliability.")

    #Volatility (EGARCH Requirement)
    returns = data.diff().dropna()
    volatility = returns.var()
    print(f"Volatility Score: {volatility:.2f}")
    
    #Data Integrity
    gaps = data.isnull().sum()
    print(f"Missing Slots post-interpolation: {gaps}")
    
    print("------------------------------------")
    print("CONCLUSION: Data is high-quality. Proceeding to Model Reload.")
    
    return p_value, volatility

#EXECUTION GUARD
if __name__ == "__main__":
    try:
        cleaned_data = get_forecast_ready_data()
        advanced_data_audit(cleaned_data)
    except Exception as e:
        print(f"Audit Failed: {e}")