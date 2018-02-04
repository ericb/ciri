import json


class SchemaEncoder(object):

    def encode(self, *args, **kwargs):
        raise NotImplementedError


class JSONEncoder(SchemaEncoder):
    
    def __init__(self):
        self.encoder = json.JSONEncoder(check_circular=False)

    def encode(self, data, schema):
        return json.dumps(data)
