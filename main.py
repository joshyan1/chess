from flask import Flask, request
import requests
from redislite import Redis
import msgpack
import time

app = Flask(__name__) 
redis = Redis("chess.db") #creates redis database

#classes for abstraction business --> look below at function calls, pretty easier
#class for chess.com profiles
class Chesscom:
    def __init__(self, username):
        self.username = username

    #gets profile
    def profile(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}")
        response.raise_for_status()

        return response.json()    

    #gets stats
    def stats(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}/stats")
        response.raise_for_status()

        return response.json()    
    
    #gets list of urls to monthly archives of games and adds individual games to list
    def games(self):
        response = requests.get(f"https://api.chess.com/pub/player/{self.username}/games/archives")
        response.raise_for_status()

        #creates list
        games = []

        for archive in response.json().get('archives'):

            #uses monthly archive url to get list of games
            response2 = requests.get(archive)
            response2.raise_for_status()
            #adds eaech game to list
            games.extend(response2.json().get("games"))

        return games

#class for lichess profiles
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

    #disregard for now
    print(f'database doesnt have {site}:{username}')

    #pulls from site
    if site == 'chess':
        user = Chesscom(username)
    elif site == 'lichess':
        user = Lichess(username)
    else:
        raise Exception("site not accepted")

    #pulls data 
    profile = user.profile()
    games = user.games()
    stats = user.stats()

    #adds packed profile to databse
    redis.set(f'{site}:{username}', msgpack.packb(profile)) 

    #runs through list of games
    for game in games:
        #print(game.keys())
        #print(type(game.get("end_time")))

        #adds each game to redis database's sorted list
        #first paramater is database name
        #second parameter is dict: (key:score)
            #key is game data, score is timestamp of end time so we can find games by time
        redis.zadd(f'{site}:{username}:games', {msgpack.packb(game):float(game.get("end_time"))})

    #adds packed stats to database
    redis.set(f'{site}:{username}:stats', msgpack.packb(stats))

    #just returns first game in games database to site
    return msgpack.unpackb(redis.zrange(f'{site}:{username}:games', "0", time.time(), byscore=True)[0])
 

    '''
    website: search 'username'

    get data from lichess, chess.com, uscf, etc.

    return: lichess acc, chess.com acc, uscf acc

    user selects accounts
    '''