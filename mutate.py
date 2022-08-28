from unittest.mock import patch
from flask import Flask, request, jsonify
from os import environ
from logger import get_logger
import incluster_config, base64, jsonpatch, copy, json,random


webhook = Flask(__name__)

#logger = get_logger()

@webhook.route('/mutate', methods=['POST'])
def mutate():
    spec = request.json["request"]["object"]
    modified_spec = copy.deepcopy(spec)

    try:
        modified_spec["metadata"]["labels"]["example.com/new-label"] = str(
            random.randint(1, 1000)
        )
    except KeyError:
        pass
    patch = jsonpatch.JsonPatch.from_diff(spec, modified_spec)
    return jsonify(
        {
            "response": {
                "allowed": True,
                "uid": request.json["request"]["uid"],
                "patch": base64.b64encode(str(patch).encode()).decode(),
                "patchtype": "JSONPatch",
            }
        }
    )

if __name__ == '__main__':
    webhook.run(host='0.0.0.0', port=5000)