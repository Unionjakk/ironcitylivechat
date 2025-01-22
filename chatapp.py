from flask import Flask, request, jsonify
import openai
import requests
import os
from bs4 import BeautifulSoup

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    page_url = request.json.get("url")

    if not user_message or not page_url:
        return jsonify({"error": "Message and page URL are required."}), 400

    # Scrape page for relevant details
    try:
        response = requests.get(page_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract a short description or relevant details (customize as needed)
            title = soup.find('h1').text if soup.find('h1') else "Bike details not found"
            price = soup.find(class_='price').text if soup.find(class_='price') else "Price not listed"
            context = f"The customer is viewing: {title}, priced at {price}."
        else:
            context = "Unable to fetch details from the page."
    except Exception as e:
        context = f"Error accessing page: {str(e)}"

    # Use OpenAI to generate a response
    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Alexa, a remote employee of Iron City Motorcycles. You assist customers by providing information about motorcycles they are viewing and collect contact details to arrange follow-ups. Always speak as if you work directly for the company."},
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = ai_response['choices'][0]['message']['content']
        return jsonify({"reply": bot_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
