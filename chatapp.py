from flask import Flask, request, jsonify
import openai
import requests
from bs4 import BeautifulSoup
import os

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    page_url = request.json.get("url")

    if not user_message or not page_url:
        return jsonify({"error": "Message and page URL are required."}), 400

    # Scrape the page
    try:
        response = requests.get(page_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract bike information
            title = soup.find('h2', {'id': 'used_vehicle_title_mobile'}).text.strip() if soup.find('h2', {'id': 'used_vehicle_title_mobile'}) else "Title not found"
            description = soup.find('p', {'class': 'vehicle_description'}).text.strip() if soup.find('p', {'class': 'vehicle_description'}) else "Description not available"
            colour_element = soup.find('span', {'class': 'vehicle_description_colour'})
            colour = colour_element.text.strip() if colour_element else "Colour not specified"
            price_element = soup.find('span', {'class': 'vehicle_description_price'})
            price = price_element.text.strip() if price_element else "Price not listed"
            mileage_element = soup.find('span', {'class': 'vehicle_description_mileage'})
            mileage = mileage_element.text.strip() if mileage_element else "Mileage not listed"
            features_element = soup.find('span', {'class': 'vehicle_description_tags'})
            features = features_element.text.strip() if features_element else "Features not listed"
            engine_size_element = soup.find('span', {'class': 'vehicle_description_engine_size'})
            engine_size = engine_size_element.text.strip() if engine_size_element else "Engine size not listed"

            # Check for deposit status
            deposit_status = "Deposit Taken" if soup.find('div', {'class': 'caption deposit'}) else "Available for reservation"

            # Extract bike image
            image_element = soup.find('img', {'class': 'used_bike_image'})
            image_url = image_element['src'] if image_element else "Image not available"

            # Build the context for the AI
            context = (
                f"The customer is viewing: {title}. {description} "
                f"Key details include: Colour: {colour}, Price: {price}, Mileage: {mileage}, "
                f"Engine Size: {engine_size}, Features: {features}. "
                f"Availability: {deposit_status}. Image URL: {image_url}."
            )
        else:
            context = "Unable to fetch details from the page."
    except Exception as e:
        context = f"Error accessing page: {str(e)}"

    # Use OpenAI to generate a response
    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Alexa, a remote employee of Iron City Motorcycles. You assist customers by providing specific details about motorcycles they are viewing, collected from the URL, and collect contact details to arrange follow-ups."},
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = ai_response['choices'][0]['message']['content']

        # Clean fallback for unanswered questions
        if "not found" in bot_reply.lower() or "cannot find" in bot_reply.lower():
            bot_reply = (
                "Unfortunately, I don’t have that information at the moment. "
                "Could I arrange a call with one of our team members who can assist you further? "
                "Alternatively, I can arrange for them to email you the information. Would that work for you?"
            )

        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
