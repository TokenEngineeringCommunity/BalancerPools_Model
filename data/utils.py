from decimal import Decimal
from datetime import datetime
import json
import pickle

def load_json(path, **kwargs):
    with open(path, 'r') as f:
        return json.load(f, **kwargs)

def save_json(x, path, indent=True, **kwargs):
    with open(path, 'w') as f:
        if indent:
            json.dump(x, f, indent='\t', **kwargs)
        else:
            json.dump(x, f, **kwargs)
    print("Saved to", path)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(f'{obj.normalize():f}')  # using normalize() gets rid of trailing 0s, using ':f' prevents scientific notation
        return super().encode(obj)

def load_pickle(path):
    print("Unpickling from", path)
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(x, path):
    print("Pickling to", path)
    with open(path, 'wb') as f:
        return pickle.dump(x, f)
