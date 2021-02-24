from datetime import datetime
import json
import pickle

def load_json(path, **kwargs):
    print(kwargs.items())
    with open(path, 'r') as f:
        return json.load(f, **kwargs)

def save_json(x, path, indent=True, **kwargs):
    with open(path, 'w') as f:
        if indent:
            json.dump(x, f, indent='\t', **kwargs)
        else:
            json.dump(x, f, **kwargs)
    print("Saved to", path)

def json_serialize_datetime(o):
    if isinstance(o, datetime):
        return o.isoformat()

def load_pickle(path):
    print("Unpickling from", path)
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(x, path):
    print("Pickling to", path)
    with open(path, 'wb') as f:
        return pickle.dump(x, f)
