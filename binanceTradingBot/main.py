import pickle
import joblib
from datetime import datetime, timedelta
import time
import requests
import pandas as pd
import numpy as np
import os
import ccxt
import traceback

# 追加
import requests

from features import features, calc_features

# 追加


class LineNotify:
    def __init__(self):
        self.line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")
        self.line_notify_api = "https://notify-api.line.me/api/notify"
        self.headers = {
            "Authorization": f"Bearer {self.line_notify_token}"
        }

    def send(self, msg):
        msg = {"message": f" {msg}"}
        requests.post(self.line_notify_api, headers=self.headers, data=msg)

# BinanceのOHLCV情報を取得


def get_binance_ohlcv(market, from_time, interval_sec, limit):
    ohlcv_list = ccxt.binance().fapiPublicGetKlines({
        'symbol': market,
        'startTime': from_time,
        'interval': format_interval_sec(interval_sec),
        'limit': limit
    })

    df = pd.DataFrame(ohlcv_list, columns=['timestamp',
                                           'op',
                                           'hi',
                                           'lo',
                                           'cl',
                                           'volume',
                                           'close_time',
                                           'quote_asset_volume',
                                           'trades',
                                           'taker_buy_base_asset_volume',
                                           'taker_buy_quote_asset_volume',
                                           'ignore', ])[['timestamp', 'op', 'hi', 'lo', 'cl', 'volume']]

    df = df[from_time <= df['timestamp'].astype('int64')]
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index("timestamp", inplace=True)
    df["op"] = df["op"].astype(float)
    df["hi"] = df["hi"].astype(float)
    df["lo"] = df["lo"].astype(float)
    df["cl"] = df["cl"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df.sort_index(inplace=True)
    return df


def format_interval_sec(interval_sec):
    interval_min = interval_sec // 60
    if interval_min < 60:
        return '{}m'.format(interval_min)
    if interval_min < 24 * 60:
        return '{}h'.format(interval_min // 60)
    else:
        return '{}d'.format(interval_min // (24 * 60))


# ポジション情報を取得

def get_binance_position(binance, market):
    poss = binance.fapiPrivateGetPositionRisk()
    positionAmt = 0.0

    market_history = [d.get('symbol') for d in poss]  # 銘柄だけを抽出
    market_index = market_history.index(market)  # 探している銘柄が何番目に存在するか
    print(poss[market_index])

    positionAmt = float(poss[market_index]['positionAmt'])
    positionSide = str(poss[market_index]['positionSide'])

    if positionAmt == 0:
        positionSide = 'NONE'
    elif positionAmt > 0:
        positionSide = 'BUY'
    else:
        positionSide = 'SELL'
    return {'positionSide': positionSide, 'positionAmt': positionAmt}


# Binanceへ注文
def order_binance(exchange, market, order_side, order_size):
    order = exchange.fapiPrivate_post_order(
        {
            "symbol": market,
            "side": order_side,
            "type": "MARKET",
            "quantity": order_size,
            # "price":order_price,
            # "timeInForce": "GTC",
            # "reduce_only": reduce,
        }
    )
    print(order)


# ボット起動
def start(exchange, interval_sec):

    print("binance Bot is started!\n interval:{0}sec".format(interval_sec))

    # 追加
    line_notify = LineNotify()
    line_notify.send("Binance Bot起動")
    line_notify.send("\n{0}分足".format(30))

    while True:

        dt_now = datetime.now()

        # 指定した時間間隔ごとに実行
        if dt_now.minute % 30 == 0:

            try:

                line_notify.send("30分経過")

                # OHLCV情報を取得
                time_now = datetime.now()
                from_time = int(
                    (time_now + timedelta(minutes=- 100000 * interval_sec)).timestamp())
                limit = 200

                # MANAUSDT------------------------------
                market_MANA = 'MANAUSDT'
                df_MANA = get_binance_ohlcv(
                    market_MANA, from_time, interval_sec, limit)

                df_MANA_features = calc_features(df_MANA)
                position_MANA = get_binance_position(exchange, market_MANA)

                print("{0}のポジションサイド:{1}".format(
                    str(market_MANA), str(position_MANA['positionSide'])))
                print("{0}のポジションサイズ:{1}".format(
                    str(market_MANA), str(position_MANA['positionAmt'])))

                # line_notify.send("{0}のポジションサイド:{1}".format(str(market_MANA),str(position_MANA['positionSide'])))
                line_notify.send("{0}のポジションサイズ:{1}".format(
                    str(market_MANA), str(position_MANA['positionAmt'])))

            # 注文処理ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

                order_side = "NONE"

            # エグジットーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

                # MANAUSDT------------------------------
                if (df_MANA_features['sig3'].iloc[-2] > (-7/10)) & (position_MANA["positionSide"] == "BUY"):
                    order_side = "SELL"
                    order_size = abs(position_MANA["positionAmt"])
                    order_binance(exchange, market_MANA,
                                  order_side, order_size)

            # エントリーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

                # MANAUSDT------------------------------
                # ロングエントリー
                if (df_MANA_features['sig3'].iloc[-2] < (-10/10)) & (position_MANA["positionAmt"] < 360):
                    order_side = "BUY"
                    order_size = 120
                    order_binance(exchange, market_MANA,
                                  order_side, order_size)

            except Exception as e:
                print(traceback.format_exc())
                # 追加
                line_notify.send("\n 何らかのエラー")
                pass

        # おまけ（時間アノマリーロジック）
        weekday = datetime.now().weekday()

        if (dt_now.hour == 3) & (dt_now.minute == 45):  # 日本時間で12時45分
            try:
                line_notify.send("午後の12時45分です")

                market_ETH = "ETHUSDT"
                position_ETH = get_binance_position(exchange, market_ETH)
                print("{0}のポジションサイド:{1}".format(
                    str(market_ETH), str(position_ETH['positionSide'])))
                print("{0}のポジションサイズ:{1}".format(
                    str(market_ETH), str(position_ETH['positionAmt'])))
                line_notify.send("{0}のポジションサイド:{1}".format(
                    str(market_ETH), str(position_ETH['positionSide'])))
                line_notify.send("{0}のポジションサイズ:{1}".format(
                    str(market_ETH), str(position_ETH['positionAmt'])))

                # ショートクローズ
                if (position_ETH['positionSide'] == "SELL"):
                    order_side = "BUY"
                    order_size = abs(position_ETH["positionAmt"])
                    order_binance(exchange, market_ETH, order_side, order_size)

                    line_notify.send("ショートクローズ")

                # 月曜日、火曜日、水曜日はロングのエントリーをする
                # ロングエントリー
                if ((weekday == 0) | (weekday == 1) | (weekday == 2)):
                    line_notify.send("ロングエントリー(月/火/水)")
                    order_side = "BUY"
                    order_size = 0.15
                    order_binance(exchange, market_ETH, order_side, order_size)

            except Exception as e:
                print(traceback.format_exc())
                line_notify.send("\n 何らかのエラーが発生")
                pass

        if (dt_now.hour == 0) & (dt_now.minute == 2):  # 日本時間で午前9時2分
            try:
                line_notify.send("午前9時02分です")

                market_ETH = "ETHUSDT"
                position_ETH = get_binance_position(exchange, market_ETH)
                print("{0}のポジションサイド:{1}".format(
                    str(market_ETH), str(position_ETH['positionSide'])))
                print("{0}のポジションサイズ:{1}".format(
                    str(market_ETH), str(position_ETH['positionAmt'])))
                line_notify.send("{0}のポジションサイド:{1}".format(
                    str(market_ETH), str(position_ETH['positionSide'])))
                line_notify.send("{0}のポジションサイズ:{1}".format(
                    str(market_ETH), str(position_ETH['positionAmt'])))

                # 水曜日と土曜日はロングのクローズのみ
                if ((weekday == 2) | (weekday == 5)):
                    line_notify.send("ロングクローズのみ(水/土)")

                    if (position_ETH['positionSide'] == "BUY"):
                        order_side = "SELL"
                        order_size = abs(position_ETH["positionAmt"])
                        order_binance(exchange, market_ETH,
                                      order_side, order_size)

                # それ以外の曜日はロングのクローズとショートのエントリーも行う
                else:
                    if (position_ETH['positionSide'] == "BUY"):
                        line_notify.send("ロングクローズ")
                        order_side = "SELL"
                        order_size = abs(position_ETH["positionAmt"])
                        order_binance(exchange, market_ETH,
                                      order_side, order_size)
                    line_notify.send("ショートエントリー")
                    order_side = "SELL"
                    order_size = 0.15
                    order_binance(exchange, market_ETH, order_side, order_size)

            except Exception as e:
                print(traceback.format_exc())
                line_notify.send("\n 何らかのエラーが発生")
                pass

        time.sleep(60)
        # time.sleep(1200)


if __name__ == '__main__':

    apiKey = os.getenv("API_KEY")
    secretKey = os.getenv("SECRET_KEY")
    # lot = float(os.getenv("LOT"))
    # max_lot = float(os.getenv("MAX_LOT"))
    interval_sec = int(os.getenv("INTERVAL_SEC"))

    exchange = ccxt.binance({"apiKey": apiKey, "secret": secretKey, "options": {
                            "defaultType": "future"}, "enableRateLimit": True, })
    start(exchange, interval_sec)
