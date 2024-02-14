import json
from pathlib import Path

credit_store_items = json.loads(
    (Path(__file__).parent / 'credit_store.json').read_text('utf-8'))
