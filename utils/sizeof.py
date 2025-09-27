import json

def get_size_kb(json_data):
    """
    Calculates size of a JSON object in KB
    """
    return len(json.dumps(json_data).encode('utf-8')) / 1024.0