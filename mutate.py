from unittest.mock import patch
from flask import Flask, request
from logger import get_logger
import incluster_config, base64, json, os
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException


webhook = Flask(__name__)

logger = get_logger()

properties = open("properties.yaml", "r")
data = properties.read()
list = data.split("\n")
properties.close()

api_instance = client.CoreV1Api(client.ApiClient(incluster_config.load_incluster_config()))

try: 
    api_response = api_instance.read_namespaced_config_map("cluster-info","kube-system")
    for key,value in api_response.data.items():
        if key == "cluster":
            cluster_name = value
        else:
            pass
except ApiException as e:
    print("Exception when calling CoreV1Api->list_namespaced_config_map: %s\n" % e)

if cluster_name is None:
  exit(1)
else:
  logger.info("clusterDomain was set to: " + cluster_name)
try:
  os.environ["NDOTS"]
except KeyError:
  logger.warning("NDOTS was not set, default value is '2'")
  ndots = "2"
else:
  ndots = os.environ["NDOTS"]
  logger.info("NDOTS was set to: " + ndots)
try:
  os.environ["TIMEOUT"]
except KeyError:
  logger.warning("TIMEOUT was not set, default value is '1'")
  timeout = "1"
else:
  timeout = os.environ["TIMEOUT"]
  logger.info("TIMEOUT was set to: " + timeout)
try:
  os.environ["ATTEMTPS"]
except KeyError:
  logger.warning("ATTEMTPS was not set, default value is '1'")
  attempts = "1"
else:
  attempts = os.environ["ATTEMTPS"]
  logger.info("ATTEMTPS was set to: " + attempts)
try:
  os.environ["NODELOCALDNS_IP"]
  nodelocaldns_ip = os.environ["NODELOCALDNS_IP"]
  logger.info("NODELOCALDNS_IP was set to: " + nodelocaldns_ip)
except KeyError:
  logger.error("Please set NODELOCALDNS_IP...")
  exit(1)


patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"NODELOCALDNS_IP_VALUE\"], \"options\": [{\"name\": \"timeout\", \"value\":  \"TIMEOUT_VALUE\"}, {\"name\": \"ndots\", \"value\": \"NDOTS_VALUE\"}, {\"name\": \"attempts\", \"value\": \"ATTEMPTS_VALUE\"}], \"searches\": [\"svc.CLUSTERDOMAIN_VALUE\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"

char_to_replace = {'TIMEOUT_VALUE': timeout, 'NDOTS_VALUE': ndots, 'ATTEMPTS_VALUE': attempts, 'NODELOCALDNS_IP_VALUE': nodelocaldns_ip, 'CLUSTERDOMAIN_VALUE': cluster_name}
for key, value in char_to_replace.items():
    patch = patch.replace(key,value)
    #logger.debug("Patch is: " + patch)


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
  
  try:
    pod_generate_name = spec["metadata"]["generateName"]
  except KeyError:
    try:
      pod_generate_name = spec["metadata"]["name"]
      logger.info("Request UID: " + uid + " does not have pod generate name; setting metadata.name as a pod_generate_name")
      logger.debug("Request: " + req)
    except:
      logger.info("Request UID: " + uid + "  does not have pod_generate_name..")
      logger.debug("Request: " + req)
      pod_generate_name = ""
  try:
    pod_owner_object_name = spec["metadata"]["ownerReferences"][0]["name"]
  except KeyError:
    try:
      pod_owner_object_name = spec["metadata"]["name"]
      logger.info("Request UID: " + uid + " does not have pod generate name; setting metadata.name as a pod_owner_object_name")
      logger.debug("Request: " + req)
    except:
      logger.info("Request UID: " + uid + "  does not have pod_owner_object_name..")
      logger.debug("Request: " + req)
      pod_owner_object_name = ""
  try:
    pod_owner_object_kind = spec["metadata"]["ownerReferences"][0]["kind"]
  except KeyError:
    try:
      pod_owner_object_kind = spec["metadata"]["name"]
      logger.info("Request UID: " + uid + " does not have pod generate name; setting metadata.name as a pod_owner_object_name")
      logger.debug("Request: " + req)
    except:
      logger.info("Request UID: " + uid + "  does not have pod_owner_object_kind..")
      logger.debug("Request: " + req)  
      pod_owner_object_kind = ""


  if namespace in list:
    logger.debug("Namespace " + namespace + " is not restricted. | " + " Owner Object: " + pod_owner_object_name + " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name: " + pod_generate_name + " | " + " Request UID: " + uid + " | NOT MUTATED AND DEPLOYED " )
    logger.info("Namespace: " + namespace +  " | Owner Object: " + pod_owner_object_name + " | NOT MUTATED AND DEPLOYED ")
    return default_response(uid)
  else:
    if (spec["spec"]["dnsPolicy"] is None) or (spec["spec"]["dnsPolicy"] == "ClusterFirst"):
      logger.debug("Namespace " + namespace + " is restricted. | " + " Owner Object: " + pod_owner_object_name + " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name: " + pod_generate_name + " | " + " Request UID: " + uid + " | MUTATED AND DEPLOYED " )
      logger.info("Namespace: " + namespace +  " | Owner Object: " + pod_owner_object_name + " | MUTATED AND DEPLOYED ")
      return mutatation_response(True, uid, patch)
    else:
      logger.info("Namespace: " + namespace +  " | Owner Object: " + pod_owner_object_name + " | DNS Policy: " + spec["spec"]["dnsPolicy"] + " | NOT MUTATED AND DEPLOYED ")
      logger.debug("Namespace " + namespace + " is not restricted. | " + "Owner Object: " + pod_owner_object_name + " | DNS Policy " + spec["spec"]["dnsPolicy"] +  " | Owner Object Kind: " + pod_owner_object_kind  + " | Pod Generate Name: " + pod_generate_name + " | " + " Request UID: " + uid + " | NOT MUTATED AND DEPLOYED " )
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