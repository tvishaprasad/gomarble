import logging
from flask import Flask, request, jsonify, render_template
from scraper import extract_reviews
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

@app.route('/')
def home():
    app.logger.info("Home route accessed.")
    return render_template('index.html')

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    url = request.args.get('page')
    if not url:
        app.logger.warning("No 'page' parameter provided in request.")
        return jsonify({"error": "URL parameter 'page' is required."}), 400

    app.logger.info(f"Starting to scrape reviews for URL: {url}")
    try:
        reviews_data = extract_reviews(url, max_pages=10)
        app.logger.info(f"Scraping completed for URL: {url}")
        return jsonify(reviews_data)
    except Exception as e:
        app.logger.error(f"Error occurred while scraping: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.logger.info(f"Starting the Flask application on port {port}...")
    app.run(host='0.0.0.0', port=port)