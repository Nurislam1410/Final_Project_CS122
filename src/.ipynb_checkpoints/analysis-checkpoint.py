import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # before pyplot, headless png saves
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOT_DIR = os.path.join(BASE_DIR, "static", "plots")

CRASH_ANALYSIS_COLS = ['Crash Date Time', 'City Name', 'NumberKilled', 'NumberInjured']
PARTY_ANALYSIS_COLS = ['City Name', 'Primary Collision Factor Violation', 'At Fault']

def ensure_plot_dir():
    os.makedirs(PLOT_DIR, exist_ok=True)

def load_and_filter(filename, city_filter=None):
    path = os.path.join(BASE_DIR, "data", "raw", filename)
    if not os.path.exists(path):
        return None 
    
    # scraper writes normal csv; low_memory=False handles mixed dtypes
    df = pd.read_csv(path, low_memory=False)
    
    df.columns = df.columns.str.strip()
    
    if city_filter and 'City Name' in df.columns:
        df = df[df['City Name'].str.contains(city_filter, case=False, na=False)] 
    
    return df

def perform_crash_analysis(df):
    #string to num conversion for issues
    df['NumberKilled'] = pd.to_numeric(df['NumberKilled'], errors='coerce').fillna(0)
    df['NumberInjured'] = pd.to_numeric(df['NumberInjured'], errors='coerce').fillna(0)

    #severity score
    def get_severity(row):
        if row['NumberKilled'] > 0: return 4
        if row['NumberInjured'] > 1: return 3
        if row['NumberInjured'] == 1: return 2
        return 1
    
    df['Severity'] = df.apply(get_severity, axis=1)
    
    severity_array = df['Severity'].values
    stats = {
        "mean_severity": round(np.mean(severity_array), 2),
        "std_dev": round(np.std(severity_array), 2),
        "total_incidents": len(df),
        "total_killed": int(np.sum(df['NumberKilled']))
    }
    
    #daily crash counts + linear fit
    df['Date'] = pd.to_datetime(df['Crash Date Time'], errors='coerce').dt.date
    daily = df.groupby('Date').size()
    
    x = np.arange(len(daily))
    y = daily.values
    
    if len(x) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        trendline = slope * x + intercept
    else:
        slope, trendline = 0, y

    ensure_plot_dir()
    plt.figure(figsize=(10, 4))
    plt.scatter(x, y, alpha=0.5, label="Daily Counts", color='blue')
    plt.plot(x, trendline, color='red', linewidth=2, label=f"Trend (Slope: {slope:.2f})")
    plt.title("Accident Frequency Trend (Descriptive Analysis)")
    plt.xlabel("Timeline (Days)")
    plt.ylabel("Number of Crashes")
    plt.legend()
    
    plot_path = os.path.join(PLOT_DIR, "crash_trend.png")
    plt.savefig(plot_path)
    plt.close()
    
    return stats, "crash_trend.png"

def perform_party_analysis(df):
    violation_col = 'Primary Collision Factor Violation'
    if violation_col not in df.columns:
        if 'MovementPrecCollDescription' in df.columns:
            violation_col = 'MovementPrecCollDescription'
        elif 'Inattention' in df.columns:
            violation_col = 'Inattention'
            
    at_fault_col = 'At Fault'
    if 'IsAtFault' in df.columns:
        at_fault_col = 'IsAtFault'
    
    if violation_col in df.columns:
        top_violations = df[violation_col].value_counts().head(5)
    else:
        top_violations = pd.Series({"Data Unavailable": 0})
    
    fault_summary = "N/A"
    if at_fault_col in df.columns:
        fault_pct = (df[at_fault_col].astype(str).str.upper().isin(['Y', '1', 'TRUE'])).mean() * 100
        fault_summary = f"{fault_pct:.1f}% At Fault"
        
    stats = {
        "total_parties": len(df),
        "top_violation": top_violations.index[0] if not top_violations.empty else "N/A",
        "fault_percentage": fault_summary
    }
    
    ensure_plot_dir()
    plt.figure(figsize=(10, 4))
    top_violations.plot(kind='bar', color='orange', edgecolor='black')
    plt.title("Top 5 Behavioral Risk Factors")
    plt.ylabel("Frequency")
    plt.xlabel("Violation Type")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plot_path = os.path.join(PLOT_DIR, "current_plot.png")
    plt.savefig(plot_path)
    plt.close()
    
    return stats, "current_plot.png"
