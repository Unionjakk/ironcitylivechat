from flask import Flask, request, jsonify
import openai
import requests
from bs4 import BeautifulSoup
import logging
import os

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = "sk-your-api-key"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Log incoming request
        logging.info("Received request: %s", request.json)
        
        # Extract request data
        user_message = request.json.get("message")
        page_url = request.json.get("url")

        if not user_message or not page_url:
            logging.warning("Missing 'message' or 'url' in the request payload.")
            return jsonify({"error": "Message and page URL are required."}), 400

        # Scrape the page for details
        logging.info("Attempting to scrape URL: %s", page_url)
        try:
            response = requests.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract specific details (example: color, price, etc.)
            bike_color = soup.find(class_="vehicle_description_colour").text if soup.find(class_="vehicle_description_colour") else "Unknown"
            bike_price = soup.find(class_="vehicle_description_price").text if soup.find(class_="vehicle_description_price") else "Not listed"
            
            logging.info("Scraped bike details - Color: %s, Price: %s", bike_color, bike_price)
            
            context = f"The customer is viewing a bike in {bike_color} priced at {bike_price}."
        except Exception as scrape_error:
            logging.error("Error scraping the page: %s", scrape_error)
            context = "Unable to fetch details from the page."

        # Generate response using OpenAI
        logging.info("Sending context and user message to OpenAI API.")
        try:
            ai_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Alexa, an assistant for Iron City Motorcycles. Provide concise, professional responses."},
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ]
            )
            bot_reply = ai_response['choices'][0]['message']['content']
            logging.info("OpenAI response: %s", bot_reply)
            return jsonify({"reply": bot_reply})
        except Exception as ai_error:
            logging.error("Error generating response with OpenAI: %s", ai_error)
            return jsonify({"error": "An error occurred while processing your request."}), 500

    except Exception as general_error:
        logging.critical("Unexpected error: %s", general_error, exc_info=True)
        return jsonify({"error": "Internal server error."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by Render or default to 5000
    app.run(host='0.0.0.0', port=port)
