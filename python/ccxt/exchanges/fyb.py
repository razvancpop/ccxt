

class fyb (Exchange):


    def describe(self):
        return self.deep_extend(super.describe(), {
            'rateLimit': 1500,
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'tickerdetailed',
                        'orderbook',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'test',
                        'getaccinfo',
                        'getpendingorders',
                        'getorderhistory',
                        'cancelpendingorder',
                        'placeorder',
                        'withdraw',
                    ],
                },
            },
        })

    def fetch_balance(self, params={}):
        balance = self.privatePostGetaccinfo()
        btc = float(balance['btcBal'])
        symbol = self.symbols[0]
        quote = self.markets[symbol]['quote']
        lowercase = quote.lower() + 'Bal'
        fiat = float(balance[lowercase])
        crypto = {
            'free': btc,
            'used': 0.0,
            'total': btc,
        }
        result = {'BTC': crypto}
        result[quote] = {
            'free': fiat,
            'used': 0.0,
            'total': fiat,
        }
        result['info'] = balance
        return self.parse_balance(result)

    def fetch_order_book(self, symbol, params={}):
        orderbook = self.publicGetOrderbook(params)
        return self.parse_order_book(orderbook)

    def fetch_ticker(self, symbol, params={}):
        ticker = self.publicGetTickerdetailed(params)
        timestamp = self.milliseconds()
        last = None
        volume = None
        if 'last' in ticker:
            last = float(ticker['last'])
        if 'vol' in ticker:
            volume = float(ticker['vol'])
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': None,
            'low': None,
            'bid': float(ticker['bid']),
            'ask': float(ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': last,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': volume,
            'info': ticker,
        }

    def parse_trade(self, trade, market):
        timestamp = int(trade['date']) * 1000
        return {
            'info': trade,
            'id': str(trade['tid']),
            'order': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': None,
            'price': float(trade['price']),
            'amount': float(trade['amount']),
        }

    def fetch_trades(self, symbol, params={}):
        market = self.market(symbol)
        response = self.publicGetTrades(params)
        return self.parse_trades(response, market)

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        response = self.privatePostPlaceorder(self.extend({
            'qty': amount,
            'price': price,
            'type': side[0].upper()
        }, params))
        return {
            'info': response,
            'id': response['pending_oid'],
        }

    def cancel_order(self, id, symbol=None, params={}):
        return self.privatePostCancelpendingorder({'orderNo': id})

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + path
        if api == 'public':
            url += '.json'
        else:
            nonce = self.nonce()
            body = self.urlencode(self.extend({'timestamp': nonce}, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'key': self.apiKey,
                'sig': self.hmac(self.encode(body), self.encode(self.secret), hashlib.sha1)
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        if api == 'private':
            if 'error' in response:
                if response['error']:
                    raise ExchangeError(self.id + ' ' + self.json(response))
        return response
