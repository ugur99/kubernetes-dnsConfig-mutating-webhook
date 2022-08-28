from unittest.mock import patch
from flask import Flask, request, jsonify
from os import environ
from logger import get_logger
import incluster_config, base64, jsonpatch, copy


webhook = Flask(__name__)

logger = get_logger()

#webhook.config['ndots'] = environ.get('ndots')
#webhook.config['timeout'] = environ.get('timeout')
#webhook.config['attempts'] = environ.get('attempts')


#if "ndots" not in environ:
#    logger.error("Required environment variable 'ndots' isn't set. Exiting...")
#    exit(1)
#if "timeout" not in environ:
#    logger.error("Required environment variable 'timeout' isn't set. Exiting...")
#    exit(1)
#if "attempts" not in environ:
#    logger.error("Required environment variable 'attempts' isn't set. Exiting...")
#    exit(1)

@webhook.route('/mutate', methods=['POST'])
def mutatating_webhook():
    request_info = request.get_json()
    #logger.info("Requst is: " , request_info)
    spec = request_info["request"].get("object")
    uid = request_info["request"].get("uid")
    #namespace = request_info["request"]["namespace"]


    try:
      spec["spec"]["dnsPolicy"]
    except KeyError:
      logger.warning("dnsPolicy is not defined.")
      patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"1\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"
    else:
      patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"1\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"

    #if spec["spec"]["dnsPolicy"] == "ClusterFirst" and namespace == "default":
        #modified_spec = copy.deepcopy(spec)
        #try:
        #    modified_spec["spec"]["dnsPolicy"] = "None"
        #    modified_spec["spec"]["dnsConfig"]["options"][0]["name"] = "ndots"
        #    modified_spec["spec"]["dnsConfig"]["options"][1]["name"] = "timeout"
        #    modified_spec["spec"]["dnsConfig"]["options"][2]["name"] = "attempts"
        #    modified_spec["spec"]["dnsConfig"]["options"][0]["value"] = "2"
        #    modified_spec["spec"]["dnsConfig"]["options"][1]["value"] = "1"
        #    modified_spec["spec"]["dnsConfig"]["options"][2]["value"] = "1"
        #    modified_spec["spec"]["dnsConfig"]["nameservers"][0] = "169.254.25.19"
        #    modified_spec["spec"]["dnsConfig"]["searches"][0] = "svc.cluster.local"
        #    modified_spec["spec"]["dnsConfig"]["searches"][1] = "ns.svc.cluster.local"
        #except KeyError:
        #    pass
#
        #patch = jsonpatch.JsonPatch.from_diff(spec, modified_spec)
        #patch = "[{\"op\": \"add\", \"path\": \"/spec/dnsConfig\", \"value\": {\"nameservers\": [\"169.254.25.10\"], \"options\": [{\"name\": \"timeout\", \"value\": \"1\"}, {\"name\": \"ndots\", \"value\": \"1\"}, {\"name\": \"attempts\", \"value\": \"1\"}], \"searches\": [\"svc.cluster.local\"]}}, {\"op\": \"replace\", \"path\": \"/spec/dnsPolicy\", \"value\": \"None\"}]"
        
    #elif namespace != "default":
        #print("Namespace is: " + namespace)
    #else:
        #print("Uups we have a problem #1")

    return mutatation_response(True, uid, f"Clsuter-wide DNS policy was applied!",patch)



def mutatation_response(allowed, uid, message, patch):
    return jsonify({"apiVersion": "admission.k8s.io/v1",
                    "kind": "AdmissionReview",
                    "response":
                        {"allowed": allowed,
                         "uid": uid,
                         "status": {"message": message},
                         "patch": base64.b64encode(str(patch).encode()).decode(),
                         "patchtype": "JSONPatch",
                         }
                    })


if __name__ == '__main__':
    webhook.run(host='0.0.0.0', port=5000)