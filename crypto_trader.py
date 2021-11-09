import sys
import http.client
import urllib
import json
import hashlib
import hmac
import time
import logging
import threading

from bot import Bot

secret_key = 'S-f5fb1840951f16f40737d4e01f4b8975a51e1124'
public_key = 'K-f76caad05d749c91d2e3ec89020cbef7443c9ebd'

class ExmoAPI:
    def __init__(self, API_KEY, API_SECRET, API_URL = 'api.exmo.com', API_VERSION = 'v1.1'):
        self.API_URL = API_URL
        self.API_VERSION = API_VERSION
        self.API_KEY = API_KEY
        self.API_SECRET = bytes(API_SECRET, encoding='utf-8')

    def sha512(self, data):
        H = hmac.new(key = self.API_SECRET, digestmod = hashlib.sha512)
        H.update(data.encode('utf-8'))
        return H.hexdigest()

    def api_query(self, api_method, params = {}):
        params['nonce'] = int(round(time.time() * 1000))
        params =  urllib.parse.urlencode(params)

        sign = self.sha512(params)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Key": self.API_KEY,
            "Sign": sign
        }
        conn = http.client.HTTPSConnection(self.API_URL)
        conn.request("POST", "/" + self.API_VERSION + "/" + api_method, params, headers)
        response = conn.getresponse().read()

        conn.close()

        try:
            obj = json.loads(response.decode('utf-8'))
            if 'error' in obj and obj['error']:
                print(obj['error'])
                raise sys.exit()
            return obj
        except json.decoder.JSONDecodeError:
            print('Error while parsing response:', response)
            raise sys.exit()



# cur2_min_quantity = 

# print(ExmoAPI_instance.api_query('user_open_orders'))
# print(ExmoAPI_instance.api_query('currency'))


# for pair in pair_list:
#     print(pair)

# ticker = ExmoAPI_instance.api_query('ticker')
# print(ticker)

# ticker = ExmoAPI_instance.api_query('pair_settings')
# print(ticker)

if __name__ == '__main__':
    logging.basicConfig(filename='bot.log', filemode='a', format='%(asctime)s, %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)
    logging.info('Running Crypto Trader')

    ExmoAPI_instance = ExmoAPI(public_key, secret_key)
    user_info = ExmoAPI_instance.api_query('user_info')
    user_uid = user_info['uid']
    server_date = user_info['server_date']

    logging.info('Init API')
    currency_sell = 'RUB'
    currency_buy = 'BTC'

    bot = Bot(ExmoAPI_instance, currency_buy, currency_sell)
    logging.info('Create Crypto bot')

    while True:
        bot.trade()
        time.sleep(5)
