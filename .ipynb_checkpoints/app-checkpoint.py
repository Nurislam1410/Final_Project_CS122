from flask import Flask, render_template, request, redirect, url_for
import os
from src.scraper import scrape_web_catalog, process_and_save
from src.analysis import load_and_filter, perform_crash_analysis, perform_party_analysis

app = Flask(__name__)

@app.route('/')
def index():
    web_files = scrape_web_catalog()
    return render_template('index.html', datasets=web_files)

@app.route('/process', methods=['POST'])
def process():
    dataset_info = request.form.get('dataset')
    url, filename = dataset_info.split('|') # url|filename in dropdown value
    
    process_and_save(url, filename)
    
    return redirect(url_for('results', filename=filename))

@app.route('/results')
def results():
    filename = request.args.get('filename')
    city_query = request.args.get('city', '')
    
    is_crash_file = filename.startswith('crash')
    
    df = load_and_filter(filename, city_filter=city_query)
    
    if df is None or df.empty:
        error_msg = f"No data found for city: '{city_query}' in {filename}."
        return render_template('results.html', error=error_msg, filename=filename, city=city_query)
        
    if is_crash_file:
        stats, plot_img = perform_crash_analysis(df)
    else:
        stats, plot_img = perform_party_analysis(df)
        
    return render_template('results.html', 
                           stats=stats, 
                           plot_img=plot_img, 
                           filename=filename, 
                           city=city_query,
                           is_crash=is_crash_file)

if __name__ == '__main__':
    app.run(debug=True)
