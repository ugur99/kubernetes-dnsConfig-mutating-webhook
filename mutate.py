from unittest.mock import patch
from flask import Flask, request, jsonify
from os import environ
from logger import get_logger
import incluster_config, base64, jsonpatch, copy, json


webhook = Flask(__name__)

logger = get_logger()


@webhook.route('/mutate', methods=['POST'])
def mutatating_webhook():
  try:
    request_json = json.loads(request.data.decode('utf-8'))
  except Exception as e:
    print(str(e))

  response = {
    "apiVersion": "admission.k8s.io/v1",
    "kind": "AdmissionReview",
    "response": {
      "uid": request_json['request']['uid'],
      "allowed": True,
    }
  }

  patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"1\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"


  #patch = """
  #   [
  #     {
  #       "op": "add",
  #       "path": "/spec/dnsConfig",
  #       "value": {
  #         "nameservers": [
  #           "169.254.25.10"
  #         ],
  #         "options": [
  #           {
  #             "name": "timeout",
  #             "value": "1"
  #           },
  #           {
  #             "name": "ndots",
  #             "value": "1"
  #           },
  #           {
  #             "name": "attempts",
  #             "value": "1"
  #           }
  #         ],
  #         "searches": [
  #           "svc.cluster.local"
  #         ]
  #       }
  #     },
  #     {
  #       "op": "replace",
  #       "path": "/spec/dnsPolicy",
  #       "value": "None"
  #     }
  #   ]
  #   """
  patch_bytes = patch.encode('ascii')
  patch_base64_bytes = base64.b64encode(patch_bytes)
  patch_base64 = patch_base64_bytes.decode('ascii')

  response['response']['patch'] = patch_base64
  response['response']['patchType'] = "JSONPatch"

  return json.dumps(response), 200, {'ContentType':'application/json-patch+json'} 

if __name__ == '__main__':
    webhook.run(host='0.0.0.0', port=5000)