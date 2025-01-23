from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Route to fetch settings.json
@app.route('/settings.json', methods=['GET'])
def get_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            return jsonify(settings)
    except Exception as e:
        return jsonify({'error': f"Failed to fetch settings: {str(e)}"}), 500

# Route to save updated settings.json
@app.route('/settings.json', methods=['POST'])
def update_settings():
    try:
        new_settings = request.json
        with open('settings.json', 'w') as f:
            json.dump(new_settings, f, indent=4)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': f"Failed to update settings: {str(e)}"}), 500

# Route for chat functionality
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get("message", "")
        url = data.get("url", "")
        
        # Debugging log
        print(f"Received message: {message}, URL: {url}")

        # Scrape URL logic (simplified, include your actual scraping implementation here)
        # This is just a placeholder; ensure this works accurately with your scraping library
        scraped_data = {
            "color": "Vivid Black",  # Example; replace with scraped data
            "mileage": "804 miles",
            "deposit_status": "Deposit Taken" if "deposit" in url.lower() else "Available",
        }

        # Construct a reply based on scraped data
        reply = f"The bike is a {scraped_data['color']} Harley-Davidson. Mileage: {scraped_data['mileage']}."
        if scraped_data["deposit_status"] == "Deposit Taken":
            reply += " However, it seems a deposit has already been placed on this bike."
        else:
            reply += " The bike is currently available."

        # Debugging log
        print(f"Constructed reply: {reply}")

        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by Render or default to 5000
    app.run(host='0.0.0.0', port=port)
