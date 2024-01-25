import json
from pathlib import Path

from .. import __rootdir__

credit_store_items = json.loads(
    Path(f'{__rootdir__}/data/credit_store.json').read_text('utf-8'))

# collection of the obtained ocr error
ocr_error = json.loads(
    Path(f'{__rootdir__}/data/ocr.json').read_text('utf-8'))

key_mapping = json.loads(
    Path(f"{__rootdir__}/data/key_mapping.json").read_text("utf-8"))
