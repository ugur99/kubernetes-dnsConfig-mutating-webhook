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
    #logger.debug("Request is: " + req )
  except Exception as e:
    print(str(e))

  uid = request_json['request']['uid']
  namespace = request_json["request"]["namespace"]
  spec = request_json["request"].get("object")
  pod_generate_name = spec["metadata"]["generateName"]
  pod_owner_object_name = spec["metadata"]["ownerReferences"][0]["name"]
  pod_owner_object_kind = spec["metadata"]["ownerReferences"][0]["kind"]

  if namespace in list:
    logger.debug("Namespace " + namespace + " is not restricted. | " + " Owner Object is: " + pod_owner_object_name + " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name is: " + pod_generate_name + " | " + " Request UID is: " + uid + " | NOT MUTATED AND DEPLOYED " )
    logger.info("Namespace: " + namespace +  "Owner Object is: " + pod_owner_object_name + " | NOT MUTATED AND DEPLOYED ")
    return default_response(uid)
  else:
    if (spec["spec"]["dnsPolicy"] is None) or (spec["spec"]["dnsPolicy"] == "ClusterFirst"):
      logger.debug("Namespace " + namespace + " is restricted. | " + " Owner Object is: " + pod_owner_object_name + " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name is: " + pod_generate_name + " | " + " Request UID is: " + uid + " | MUTATED AND DEPLOYED " )
      logger.info("Namespace: " + namespace +  " | Owner Object is: " + pod_owner_object_name + " | MUTATED AND DEPLOYED ")
      patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"2\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\",\"ns.svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"
      return mutatation_response(True, uid, patch)
    else:
      logger.info("Namespace: " + namespace +  " | Owner Object is: " + pod_owner_object_name + " | DNS policy is " + spec["spec"]["dnsPolicy"] + " | NOT MUTATED AND DEPLOYED ")
      logger.debug("Namespace " + namespace + " is not restricted. | " + "Owner Object is: " + pod_owner_object_name + " | DNS policy is " + spec["spec"]["dnsPolicy"] +  " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name is: " + pod_generate_name + " | " + " Request UID is: " + uid + " | NOT MUTATED AND DEPLOYED " )
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