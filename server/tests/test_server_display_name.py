import json
import re
import sys
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from server import ApiHandler


class ServerDisplayNameTests(unittest.TestCase):
    def test_sdkareas_display_name_only(self):
        listener = ThreadingHTTPServer(('127.0.0.1', 0), ApiHandler)
        thread = threading.Thread(target=listener.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{listener.server_port}/sdkareas', timeout=3) as response:
                data = json.load(response)
            self.assertEqual(data['error'], 0)
            self.assertEqual(data['sysfuncflags'], {})
            self.assertEqual(len(data['areas']), 1)
            area = data['areas'][0]
            labels = json.loads(area.pop('name'))
            self.assertEqual(set(labels), {'Portuguese', 'English'})
            for label in labels.values():
                self.assertEqual(label, '<size=18>Hunter Roulette Community</size>')
                self.assertEqual(re.sub(r'</?size(?:=18)?>', '', label), 'Hunter Roulette Community')
            self.assertEqual(area, {'id': 1, 'start': 0, 'state': 4})
        finally:
            listener.shutdown()
            listener.server_close()
            thread.join(timeout=3)
