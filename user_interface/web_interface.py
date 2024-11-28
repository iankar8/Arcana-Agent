import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import asyncio
from manager.agent_manager import AgentManager
from knowledge_base.knowledge_base import KnowledgeBase

app = Flask(__name__)
CORS(app)  # Enable CORS

# Initialize the manager and knowledge base
knowledge_base = KnowledgeBase()
manager = AgentManager()
manager.knowledge_base = knowledge_base

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['message']
    response = asyncio.run(manager.handle_user_request(user_input))
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
