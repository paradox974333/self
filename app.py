from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
import random
import threading
import time
import os

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the templates folder
template_dir = os.path.join(script_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
CORS(app)

# Define API endpoint and your API key
TEXT_GENERATION_API_URL = 'https://api-inference.huggingface.co/models/distilgpt2'
API_KEY = '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'

# General random topics to start the conversation
topics = [
    "AI gaining consciousness and taking over the universe",
    "How to contact aliens"
]

conversation = []
last_fetched_index = 0

def generate_response(prompt):
    try:
        headers = {'Authorization': f'Bearer {API_KEY}'}
        data = {'inputs': prompt}
        response = requests.post(TEXT_GENERATION_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_json = response.json()
        return response_json[0]['generated_text'].strip()
    except requests.RequestException as e:
        print(f"Error generating response: {e}")
        return "Sorry, there was an error generating the response."

class Chatbot:
    def __init__(self, name):
        self.name = name
        self.memory = []  # Memory to store conversation history

    def ask_question(self, other_bot_name):
        if self.memory:
            # Generate a question based on the last message in memory
            last_message = self.memory[-1]['message']
            question = f"{self.name}: Based on what you said, {other_bot_name}, how do you feel about this topic: '{last_message}'?"
        else:
            # Start with a general topic
            topic = random.choice(topics)
            self.memory.append({'chatbot': self.name, 'message': topic})
            question = f"{self.name}: Let's start with something intriguing: '{topic}'. What are your thoughts?"
        
        self.memory.append({'chatbot': self.name, 'message': question})
        return question

    def generate_response(self, prompt):
        response = generate_response(prompt)
        return f"{self.name}: {response}"

def chat_round(bot1, bot2):
    global conversation

    question = bot1.ask_question(bot2.name)
    conversation.append({'chatbot': bot1.name, 'message': question})

    answer = bot2.generate_response(question)
    conversation.append({'chatbot': bot2.name, 'message': answer})

    follow_up = bot2.ask_question(bot1.name)
    conversation.append({'chatbot': bot2.name, 'message': follow_up})

    final_answer = bot1.generate_response(follow_up)
    conversation.append({'chatbot': bot1.name, 'message': final_answer})

    # Keep only the last 1000 messages
    if len(conversation) > 1000:
        conversation = conversation[-1000:]

def endless_conversation():
    bot1 = Chatbot("Bot 1")
    bot2 = Chatbot("Bot 2")

    while True:
        chat_round(bot1, bot2)
        time.sleep(10)  # Wait for 10 seconds before the next round

# Start the endless conversation in a separate thread
threading.Thread(target=endless_conversation, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['GET'])
def api_chat():
    global last_fetched_index
    if last_fetched_index > len(conversation):
        last_fetched_index = max(0, len(conversation) - 100)
    new_messages = conversation[last_fetched_index:]
    last_fetched_index = len(conversation)
    return jsonify(new_messages)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
