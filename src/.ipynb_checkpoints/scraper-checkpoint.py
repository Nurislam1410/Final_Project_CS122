import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import os
import re
import glob
from urllib.parse import urljoin

CCRS_PAGE_URL = "https://data.ca.gov/dataset/ccrs"
HEADERS = {"User-Agent": "CS122-TripSafe-App/1.0"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
CATALOG_DIR = os.path.join(BASE_DIR, "data", "catalog")

ESSENTIAL_COLUMNS = [
    'Collision Id', 'Crash Date Time', 'City Name', 'County Code',
    'NumberInjured', 'NumberKilled', 'Weather 1', 'Road Condition 1',
    'LightingDescription', 'Latitude', 'Longitude', 'IsFreeway'
]

def ensure_directories():
    for path in [RAW_DATA_DIR, CATALOG_DIR]:
        os.makedirs(path, exist_ok=True)

def get_local_files():
    ensure_directories()
    search_pattern = os.path.join(RAW_DATA_DIR, "*.csv")
    files = glob.glob(search_pattern)
    return [os.path.basename(f) for f in files]

def scrape_web_catalog():
    response = requests.get(CCRS_PAGE_URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    web_resources = []
    for a in soup.find_all("a", href=True):
        href = urljoin(CCRS_PAGE_URL, a["href"])
        text = a.get_text(strip=True).lower()
    
        if ".csv" in href.lower() and any(k in href.lower() for k in ["crashes", "parties"]):
            match = re.search(r"20\d{2}", f"{text} {href}")
            year = match.group(0) if match else "Unknown"
            file_type = "crashes" if "crashes" in href.lower() else "parties"
            filename = f"{file_type}_{year}.csv"
            
            web_resources.append({
                "display": f"{file_type.title()} Data ({year})",
                "download_url": href,
                "filename": filename
            })
            
    return web_resources

def process_and_save(url, filename):

    ensure_directories()
    dest_path = os.path.join(RAW_DATA_DIR, filename)
    
    existing = glob.glob(dest_path)
    if existing:
        print(f"File {filename} already exists. Loading local copy.")
        return dest_path

    print(f"Downloading new data: {filename}")
    resp = requests.get(url, headers=HEADERS)
    
    raw_data = io.StringIO(resp.text)
    df = pd.read_csv(raw_data, low_memory=False)
    

    df.columns = df.columns.str.strip() 
    df = df[[c for c in ESSENTIAL_COLUMNS if c in df.columns]]
    
    df.to_csv(dest_path, index=False)
    return dest_path