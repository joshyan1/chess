from flask import Flask, request
import requests
from redislite import Redis
import msgpack

app = Flask(__name__) 
redis = Redis("chess.db") #creates redis database

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
        cache = msgpack.unpack(redis.get(f'{site}:{username}')) #unpacks data from binary to string
        print(cache)
        return cache

    print(f'database doesnt have {site}:{username}')

    #pulls from site
    if site == 'chess':
        data = requests.get(f"https://api.chess.com/pub/player/{username}")
    elif site == 'lichess':
        data = requests.get(f"https://lichess.org/api/user/{username}")
    else:
        raise Exception("site not accepted")

    #validation
    data.raise_for_status() 
    data2 = msgpack.packb(data.json()) #packs data to binary

    redis.set(f'{site}:{username}', data2) #adds to database
    return msgpack.unpackb(data2) #unpacks

    '''
    website: search 'username'

    get data from lichess, chess.com, uscf, etc.

    return: lichess acc, chess.com acc, uscf acc

    user selects accounts
    '''