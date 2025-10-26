from flask import Flask, request, jsonify, send_from_directory
import os
import pandas as pd
from flask_cors import CORS

app = Flask('labelling_app')
DATASET_PATH = r'D:\LLM\techblog-summarize\data\all_crawled_data\DATA-all_crawled_articles_with_md_20251024_165234.csv'
df = pd.read_csv(DATASET_PATH)
# If 'summary' column does not exist, create it
if 'summary' not in df.columns:
    df['summary'] = None
print(f'Server started.')

# Allow CORS for all domains
cors = CORS(app)

@app.route('/labelling/next')
def get_next_labelling_task():
    # Return the next row that needs labelling
    mask = (
        df['markdown'].notna()
        & df['markdown'].astype(str).str.strip().ne('')
        & (df['summary'].isna() | df['summary'].astype(str).str.strip().eq(''))
    )
    candidate = df[mask].head(1)

    # Total number of rows needing labelling
    total_to_label = mask.sum()
    # Total number of rows where markdown is present
    total_with_markdown = df['markdown'].notna().sum()

    if candidate.empty:
        return '', 204
    return jsonify({"data": candidate.iloc[0].to_dict(), "total_to_label": int(total_to_label), "total_with_markdown": int(total_with_markdown)})


@app.route('/labelling/submit', methods=['POST'])
def submit_labelling_task():
    # Get the url and summary in body
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return 'Missing or invalid JSON body', 400
    url = data.get('url')
    summary = data.get('summary')

    if url is None or summary is None:
        return 'Missing url or summary', 400

    if url not in df['link'].values:
        return 'URL not found', 404

    df.loc[df['link'] == url, 'summary'] = summary
    df.to_csv(DATASET_PATH, index=False)
    return 'Summary submitted successfully', 200


@app.route('/data')
def get_data_page():
    page_size = 20
    page_number = request.args.get('page', default=1, type=int)
    if page_number is None or page_number < 1:
        page_number = 1
    start_idx = (page_number - 1) * page_size
    end_idx = start_idx + page_size
    page_data = df.iloc[start_idx:end_idx]
    return jsonify(page_data.to_dict(orient='records'))


# Serve the labelling UI (labelling/index.html) from the labelling folder
@app.route('/labelling/')
@app.route('/labelling/<path:filename>')
def serve_labelling(filename: str = 'index.html'):
    static_dir = os.path.join(os.path.dirname(__file__), 'labelling')
    return send_from_directory(static_dir, filename)