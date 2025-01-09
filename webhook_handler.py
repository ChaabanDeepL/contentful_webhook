from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the secrets
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
CONTENTFUL_ACCESS_TOKEN = os.getenv("CONTENTFUL_ACCESS_TOKEN")

app = Flask(__name__)

# DeepL API Settings
DEEPL_URL = "https://api.deepl.com/v2/translate"

# Contentful API Settings
CONTENTFUL_SPACE_ID = "mpe1lux01xqs"
CONTENTFUL_ENVIRONMENT = "master"


@app.route("/contentful-webhook", methods=["POST"])
def contentful_webhook():
    payload = request.json
    entry_id = payload.get("sys", {}).get("id")
    fields = payload.get("fields", {})

    # Extract fields to translate (example: "title" and "body")
    title = fields.get("title", {}).get("en-US", "")
    body = fields.get("body", {}).get("en-US", "")

    # Translate the fields
    if title or body:
        translations = {}
        if title:
            translations["title"] = translate_text(title, target_lang="FR")
        if body:
            translations["body"] = translate_text(body, target_lang="FR")

        # Update Contentful with translations
        update_contentful_entry(entry_id, translations, locale="fr")

    return jsonify({"status": "success"}), 200

def translate_text(text, target_lang):
    headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
    data = {"text": text, "target_lang": target_lang}
    response = requests.post(DEEPL_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        print(f"DeepL API error: {response.json()}")
        return text

def update_contentful_entry(entry_id, translations, locale):
    url = f"https://api.contentful.com/spaces/{CONTENTFUL_SPACE_ID}/environments/{CONTENTFUL_ENVIRONMENT}/entries/{entry_id}"
    headers = {
        "Authorization": f"Bearer {CONTENTFUL_ACCESS_TOKEN}",
        "Content-Type": "application/vnd.contentful.management.v1+json"
    }

    # Construct the updated fields
    fields = {key: {locale: value} for key, value in translations.items()}
    data = {"fields": fields}

    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Contentful entry updated successfully.")
    else:
        print(f"Contentful API error: {response.json()}")

# Run the server
if __name__ == "__main__":
    app.run(port=5000)
