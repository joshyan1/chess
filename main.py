from flask import Flask, request
import requests

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/search", methods=["POST", "GET"])
def search():
    username = request.form.get('username', 'thebigjoshua')
    data = requests.get(f"https://api.chess.com/pub/player/{username}")
    data.raise_for_status()
    
    return data.json()["username"]