from unittest.mock import patch
from flask import Flask, request, jsonify
from os import environ
from logger import get_logger
import incluster_config, base64, jsonpatch, copy, json


webhook = Flask(__name__)

logger = get_logger()

properties = open("properties.yaml", "r")
data = properties.read()
list = data.split("\n")
properties.close()


@webhook.route('/mutate', methods=['POST'])
def mutatating_webhook():

  try:
    request_json = request.get_json()

    req = json.dumps(request_json)
    print("Request is: " + req )

  except Exception as e:
    print(str(e))

  uid = request_json['request']['uid']
  namespace = request_json["request"]["namespace"]
  spec = request_json["request"].get("object")
  #pod_name = spec["metadata"]["name"]

  if namespace in list:
    logger.info("Namespace " + namespace + " is not retricted. ")
    #logger.info("Namespace " + namespace + " is not retricted. " + pod_name + " is deployed...")
    #logger.debug("Namespace: " + namespace + " Pod: " + pod_name + " Request UID is: " + uid)
    return default_response(uid)
  else:
    if (spec["spec"]["dnsPolicy"] is None) or (spec["spec"]["dnsPolicy"] == "ClusterFirst"):
      logger.info("DNS Mutation Webhhok is applying ...")
      #logger.info("DNS Mutation Webhhok is applying to " + pod_name + " ...")
      # #logger.debug("Namespace: " + namespace + " Pod: " + pod_name + " Request UID is: " + uid)
      patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"2\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\",\"ns.svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"
      return mutatation_response(True, uid, patch)
    else:
      logger.info("DNS policy is " + spec["spec"]["dnsPolicy"] + " and skipping mutation webhook.")
      return default_response(uid)



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


def default_response(uid):
   
   response = {
     "apiVersion": "admission.k8s.io/v1",
     "kind": "AdmissionReview",
     "response": {
       "uid": uid,
       "allowed": True
     }
   }

   return json.dumps(response), 200, {'ContentType':'application/json-patch+json'}


if __name__ == '__main__':
    webhook.run(host='0.0.0.0', port=5000)