import json
from subprocess import Popen, PIPE
from twindb_infrastructure import log

CLOUDFLARE_EMAIL = ""
CLOUDFLARE_AUTH_KEY = ""


def cf_api_call(url, method="GET", data=None):

    cmd = ["curl", "--silent", "-X", method,
           "https://api.cloudflare.com/client/v4%s" % url,
           "-H", "X-Auth-Email: %s" % CLOUDFLARE_EMAIL,
           "-H", "X-Auth-Key: %s" % CLOUDFLARE_AUTH_KEY,
           "-H", "Content-Type: application/json"
           ]
    if data:
        cmd.append("--data")
        cmd.append(data)
    try:
        log.debug("Executing: %r" % cmd)
        cf_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        cout, cerr = cf_process.communicate()

        if cf_process.returncode != 0:
            log.error(cerr)
            return None

        try:
            log.debug(cout)
            return json.loads(cout)

        except ValueError as err:
            log.error(err)
            log.error(cerr)
            return None

    except OSError as err:
        log.error(err)
        return None


def get_zone_id(domain_name):

    response = cf_api_call("/zones?name=%s" % domain_name)
    zone_id = response["result"][0]["id"]

    return zone_id


def get_record_id(domain_name, zone_id):

    url = "/zones/%s/dns_records?name=%s" % (zone_id, domain_name)

    response = cf_api_call(url)
    record_id = response["result"][0]["id"]

    return record_id


def update_dns_record(name, zone, ip, record_type="A", ttl=1):

    zone_id = get_zone_id(zone)

    record_id = get_record_id(name, zone_id)

    url = "/zones/%s/dns_records/%s" % (zone_id, record_id)
    data = {
        "id": record_id,
        "name": name,
        "content": ip,
        "type": record_type,
        "ttl": ttl
    }

    response = cf_api_call(url, method="PUT", data=json.dumps(data))

    if not response["success"]:
        for error in response["errors"]:
            log.error("Error(%d): %s" % (error["code"], error["message"]))

    return bool(response["success"])


def create_dns_record(name, zone, content, data=None, record_type="A", ttl=1):

    zone_id = get_zone_id(zone)

    url = "/zones/%s/dns_records" % zone_id
    request = {
        "name": name,
        "content": content,
        "type": record_type,
        "ttl": ttl
    }

    if data:
        request["data"] = data

    response = cf_api_call(url, method="POST", data=json.dumps(request))

    if not response["success"]:
        for error in response["errors"]:
            log.error("Error(%d): %s" % (error["code"], error["message"]))

    return bool(response["success"])


def delete_dns_record(name, zone):

    zone_id = get_zone_id(zone)
    record_id = get_record_id(name, zone_id)

    url = "/zones/%s/dns_records/%s" % (zone_id, record_id)

    response = cf_api_call(url, method="DELETE")

    if not response["success"]:
        for error in response["errors"]:
            log.error("Error(%d): %s" % (error["code"], error["message"]))

    return bool(response["success"])
