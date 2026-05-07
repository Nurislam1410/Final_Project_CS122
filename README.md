# TripSafe (CS122 final)

**Title:** TripSafe — crash risk and causes from California collision data  
**Authors:** Nurislam Saliev, Syed Zoraiz Sabeel  

The app pulls crash and party datasets from the California open data portal (CCRS), saves a trimmed copy under `data/raw/`, and builds simple stats and charts (saved under `static/plots/`). You pick a dataset in the browser, wait for the download to finish, then filter by city on the results page if you want.

---

## What to install

Python 3.10+ is fine. From the project folder:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If you’d rather install by hand: `flask`, `requests`, `beautifulsoup4`, `pandas`, `numpy`, `matplotlib`, `tqdm`.

---

## How to run it

1. Open a terminal and `cd` into this repo (`Final_Project_CS122`).
2. Activate the venv if you made one (`source venv/bin/activate`).
3. Start the app:

   ```bash
   python3 app.py
   ```

4. In your browser go to **http://127.0.0.1:5000/** (Flask’s default with `debug=True`).

5. On the home page, choose crashes or parties and hit the button. First load hits the live catalog and can take a bit; big CSVs download with a progress bar in the terminal.
6. When you land on the results page, use the city filter and submit to narrow rows. Charts refresh from whatever file you picked.

You’ll need Wi‑Fi for scraping and downloads. After a file is saved locally, reloading results for that same filename is quicker because the scraper skips re-downloading if the file’s already there and non-empty.

---

## Repo layout (short)

- `app.py` — Flask routes  
- `src/scraper.py` — catalog + download  
- `src/analysis.py` — pandas / matplotlib  
- `templates/` — HTML  
- `data/raw/` — downloaded CSVs (created when you use the app)  
- `static/plots/` — PNGs the analysis step writes  
