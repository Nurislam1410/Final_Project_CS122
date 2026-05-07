import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import glob
from urllib.parse import urljoin
from tqdm import tqdm

CCRS_PAGE_URL = "https://data.ca.gov/dataset/ccrs"
HEADERS = {"User-Agent": "CS122-TripSafe-App/1.0"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
CATALOG_DIR = os.path.join(BASE_DIR, "data", "catalog")

ESSENTIAL_COLUMNS = [
    #for crash data
    'Collision Id', 'Crash Date Time', 'City Name', 'County Code',
    'NumberInjured', 'NumberKilled', 'Weather 1', 'Road Condition 1',
    'LightingDescription', 'Latitude', 'Longitude', 'IsFreeway',
    
    #for party data
    'Party Number', 'Party Type', 'At Fault', 
    'Primary Collision Factor Violation', 'Vehicle Type', 'Party Sex', 'Party Age',
    
    #different party format for issues
    'CollisionId', 'PartyNumber', 'PartyType', 'IsAtFault', 
    'MovementPrecCollDescription', 'GenderDescription', 'StatedAge', 'Inattention'
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
    seen_urls = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(CCRS_PAGE_URL, a["href"])
        text = a.get_text(strip=True).lower()
    
        if ".csv" in href.lower() and any(k in href.lower() for k in ["crashes", "parties"]):
            if href in seen_urls:
                continue
            seen_urls.add(href)
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
    
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"File {filename} already exists and is valid. Loading local copy.")
        return dest_path

    if os.path.exists(dest_path):
        os.remove(dest_path)

    print(f"Downloading new data: {filename}")

    temp_path = dest_path + ".tmp"
    with requests.get(url, headers=HEADERS, stream=True) as resp:
        resp.raise_for_status()
        
        total_size = int(resp.headers.get('content-length', 0))
        
        with open(temp_path, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

    print("\nPruning and formatting data (this takes a few seconds)...")
    
    #delimiter detector for bunch of different formats, due ot some wierd government data
    with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
        first_line = f.readline()
        #detects based on majority
        delim = '\t' if first_line.count('\t') > first_line.count(',') else ','
        delim_name = 'TAB' if delim == '\t' else 'COMMA'
        print(f"Detected Delimiter: {delim_name}")
    
    df = pd.read_csv(temp_path, sep=delim, low_memory=False, on_bad_lines='skip')
    df.columns = df.columns.str.replace(',', '').str.strip() # clean headers
    
    # prune essential columns
    available_cols = [c for c in ESSENTIAL_COLUMNS if c in df.columns]
    
    if not available_cols:
        print("\n" + "="*40)
        print("DEBUG - ACTUAL COLUMNS FOUND:")
        print(list(df.columns)[:30])
        print("="*40 + "\n")
        os.remove(temp_path)
        raise ValueError("Critical Error: Could not find any essential columns. Check terminal DEBUG printout.")
        
    df = df[available_cols]
    
    # Save clean copy and delete temp file
    df.to_csv(dest_path, index=False)
    os.remove(temp_path)
    
    return dest_path