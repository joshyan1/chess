from flask import Flask, request
import requests
from redislite import Redis
import msgpack
import time

app = Flask(__name__) 
redis = Redis("chess.db") #creates redis database

class Chesscom:
    def __init__(self, username):
        self.username = username

    def profile(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}")
        response.raise_for_status()

        return response.json()    

    def stats(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}/stats")
        response.raise_for_status()

        return response.json()    
    
    def games(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}/games/archives")
        response.raise_for_status()

        games = []

        for archive in response.json().get('archives'):
            response2 = requests.get(archive)
            response2.raise_for_status()
            games.extend(response2.json().get("games"))

        return games

class Lichess:
    def __init__(self, username):
        self.username = username

    def profile(self):
        response = requests.get(f"https://lichess.org/api/user/{self.username}")
        response.raise_for_status()

        return response.json()    

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/search", methods=["GET"])
def search():

    #sets username to query data or default (thebigjoshua)
    #uses query parameters (localhost:5000?username=thebigjoshua&site=chess)
    username = request.args.get('username', 'thebigjoshua')
    site = request.args.get('site', 'chess')

    #check if account exists
    if redis.exists(f'{site}:{username}'):
        print(username)
        print(site)
        cache = msgpack.unpackb(redis.get(f'{site}:{username}')) #unpacks data from binary to string
        print(cache)
        #return cache

    print(f'database doesnt have {site}:{username}')

    #pulls from site
    if site == 'chess':
        user = Chesscom(username)
    elif site == 'lichess':
        user = Lichess(username)
    else:
        raise Exception("site not accepted")

    #validation 
    profile = user.profile()
    games = user.games()
    stats = user.stats()

    #adds packed profile to databse
    redis.set(f'{site}:{username}', msgpack.packb(profile)) 
    for game in games:
        print(game.keys())
        print(type(game.get("end_time")))
        redis.zadd(f'{site}:{username}:games', {msgpack.packb(game):float(game.get("end_time"))})
    redis.set(f'{site}:{username}:stats', msgpack.packb(stats))

    return msgpack.unpackb(redis.zrange(f'{site}:{username}:games', "0", time.time(), byscore=True)[0])
 

    '''
    website: search 'username'

    get data from lichess, chess.com, uscf, etc.

    return: lichess acc, chess.com acc, uscf acc

    user selects accounts
    '''