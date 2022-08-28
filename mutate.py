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
    #request_json = json.loads(request.data.decode('utf-8'))
    request_json = request.get_json()
  except Exception as e:
    print(str(e))

  uid = request_json['request']['uid']

  patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"2\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\",\"ns.svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"

  return mutatation_response(True, uid, patch)



def mutatation_response(allowed, uid, patch):
   
   response = {
     "apiVersion": "admission.k8s.io/v1",
     "kind": "AdmissionReview",
     "response": {
       "uid": uid,
       "allowed": allowed,
       "patch": base64.b64encode(patch.encode('ascii')).decode('ascii'),
       "patchType": "JSONPatch"
     }
   }

   return json.dumps(response), 200, {'ContentType':'application/json-patch+json'}



if __name__ == '__main__':
    webhook.run(host='0.0.0.0', port=5000)