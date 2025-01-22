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

# Memory for customer name
customer_name = None

@app.route('/chat', methods=['POST'])
def chat():
    global customer_name  # Use a global variable to track the customer name across interactions

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
            color = soup.find('span', class_="vehicle_description_colour").text.strip() if soup.find('span', class_="vehicle_description_colour") else "Colour not listed"
            price = soup.find('span', class_="vehicle_description_price").text.strip() if soup.find('span', class_="vehicle_description_price") else "Price not listed"
            mileage = soup.find('span', class_="vehicle_description_mileage").text.strip() if soup.find('span', class_="vehicle_description_mileage") else "Mileage not listed"

            # Check for deposit status
            deposit_status = "Deposit Taken" if soup.find('div', class_="caption deposit") else "Available for reservation"

            # Add deposit status to the context
            context = f"Title: {title}, Colour: {color}, Price: {price}, Mileage: {mileage}, Availability: {deposit_status}"
            logging.info(f"Extracted details: {context}")
        else:
            context = "Unable to fetch details from the page due to HTTP error."
            logging.error(f"Failed to fetch page. Status code: {response.status_code}")
    except Exception as e:
        context = f"Error accessing page: {str(e)}"
        logging.error(f"Scraping error: {str(e)}")

    # Handle introductions and dynamic query progression
    try:
        if customer_name is None:
            # Ask for the customer's name
            if "my name is" in user_message.lower():
                name = user_message.split("my name is")[-1].strip()
                if any(word in name.lower() for word in ["swear1", "swear2"]):  # Replace with profanity checks
                    bot_reply = "That's not a proper name. How else can I address you?"
                else:
                    customer_name = name
                    bot_reply = f"Nice to meet you, {customer_name}! How can I assist you further?"
            else:
                bot_reply = "Hi, my name is Alexa, and I work for Iron City Motorcycles. How would you like me to address you?"
        else:
            # Handle regular queries
            ai_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Alexa, a helpful assistant for Iron City Motorcycles. Use UK English and provide concise, professional responses."},
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ]
            )
            bot_reply = ai_response['choices'][0]['message']['content']

        # Include deposit-specific logic in response
        if "Deposit Taken" in context:
            bot_reply += f"\nPlease note, this bike is already reserved. Let me know if you'd like to explore other options."

        return jsonify({"reply": bot_reply})

    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# RESTORED: Correct if __name__ block
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by Render or default to 5000
    app.run(host='0.0.0.0', port=port)
