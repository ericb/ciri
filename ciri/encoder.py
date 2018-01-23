import json


class JSONEncoder(object):
    
    def __init__(self):
        self.encoder = json.JSONEncoder(check_circular=False)

    def encode(self, data, schema):
        return json.dumps(data)
