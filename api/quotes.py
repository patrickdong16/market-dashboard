from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import urllib.error
import concurrent.futures


def fetch_symbol(symbol):
    """Fetch current price for a single symbol using v8 chart API."""
    encoded = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=5d&interval=1d&includePrePost=false"

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())

        result = data.get('chart', {}).get('result', [])
        if not result:
            return symbol, None

        meta = result[0].get('meta', {})
        price = meta.get('regularMarketPrice', 0)
        prev_close = meta.get('chartPreviousClose', 0)

        change_pct = 0
        if price and prev_close and prev_close != 0:
            change_pct = ((price - prev_close) / prev_close) * 100

        # Build sparkline from recent closes
        closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
        sparkline = [c for c in closes if c is not None][-5:] if closes else []
        if len(sparkline) < 5 and price:
            # Pad with interpolated values
            base = price * 0.998
            sparkline = [round(base + (price - base) * (i / 4), 4) for i in range(5)]

        return symbol, {
            'price': price or 0,
            'change_pct': round(change_pct, 4),
            'prev_close': prev_close or 0,
            'sparkline': [round(s, 4) for s in sparkline]
        }
    except Exception:
        return symbol, None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            symbols = params.get('symbols', [''])[0]

            if not symbols:
                self._respond(400, {'error': 'Missing symbols parameter'})
                return

            symbols_list = [s.strip() for s in symbols.split(',') if s.strip()]

            # Fetch all symbols in parallel
            result = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(fetch_symbol, s): s for s in symbols_list}
                for future in concurrent.futures.as_completed(futures, timeout=9):
                    try:
                        sym, data = future.result()
                        if data:
                            result[sym] = data
                    except Exception:
                        pass

            self._respond(200, result)

        except Exception as e:
            self._respond(500, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _respond(self, code, data):
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 's-maxage=15')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
