from flask import Flask, request, jsonify
import openai
import requests
from bs4 import BeautifulSoup
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    page_url = request.json.get("url")

    if not user_message or not page_url:
        logging.error("Message or URL missing from the request.")
        return jsonify({"error": "Message and page URL are required."}), 400

    # Scrape page for relevant details
    try:
        logging.info(f"Fetching URL: {page_url}")
        response = requests.get(page_url)
        logging.debug(f"HTTP Status Code: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            logging.debug(f"Fetched HTML content: {soup.prettify()[:500]}")  # Log first 500 characters of HTML

            # Extract bike details
            title = soup.find('h2', id="used_vehicle_title_mobile").text.strip() if soup.find('h2', id="used_vehicle_title_mobile") else "Bike title not found"
            color = soup.find('span', class_="vehicle_description_colour").text.strip() if soup.find('span', class_="vehicle_description_colour") else "Color not listed"
            price = soup.find('span', class_="vehicle_description_price").text.strip() if soup.find('span', class_="vehicle_description_price") else "Price not listed"

            context = f"Title: {title}, Color: {color}, Price: {price}"
            logging.info(f"Extracted details: {context}")
        else:
            context = "Unable to fetch details from the page due to HTTP error."
            logging.error(f"Failed to fetch page. Status code: {response.status_code}")
    except Exception as e:
        context = f"Error accessing page: {str(e)}"
        logging.error(f"Scraping error: {str(e)}")

    # Use OpenAI to generate a response
    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Alexa, a helpful assistant for Iron City Motorcycles. Assist customers by providing information from the webpage they are viewing and arranging follow-ups if needed."},
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = ai_response['choices'][0]['message']['content']
        return jsonify({"reply": bot_reply})

    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# RESTORED: Correct if __name__ block
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by Render or default to 5000
    app.run(host='0.0.0.0', port=port)
