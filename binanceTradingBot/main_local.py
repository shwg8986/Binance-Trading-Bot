import os
from os.path import join, dirname
from dotenv import load_dotenv
import main
import ccxt

#追加
import requests

if __name__  == '__main__':

   dotenv_path = join(dirname(__file__), './env/.env-binance')
   load_dotenv(dotenv_path,verbose=True)

   apiKey = os.getenv("API_KEY")
   secretKey = os.getenv("SECRET_KEY")
   # lot = float(os.getenv("LOT"))
   # max_lot = float(os.getenv("MAX_LOT"))
   interval_sec = int(os.getenv("INTERVAL_SEC"))

   exchange = ccxt.binance({"apiKey":apiKey, "secret":secretKey, "options": {"defaultType": "future"}, "enableRateLimit": True,})
   main.start(exchange, interval_sec)
