import requests
import urllib3
from config import settings

# Disable InsecureRequestWarning if connecting to an F5 with a self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class F5Client:
    def __init__(self, host: str, username: str = settings.F5_USER, password: str = settings.F5_PASS):
        self.host = host
        self.base_url = f"https://{self.host}/mgmt/tm"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = False 
        self.session.headers.update({"Content-Type": "application/json"})

    def get_device_info(self):
        """Mock behavior if F5_HOST is not real, or real API call"""
        if not self.host or self.host == "mock":
            return {"status": "success", "message": "Mock: Device info retrieved successfully. version: 15.1.x"}
        try:
            response = self.session.get(f"{self.base_url}/cm/device")
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_waf_rule_change(self, details: dict):
        if not self.host or self.host == "mock":
            return {"status": "success", "message": f"Mock: WAF rule {details.get('action', 'updated')} successfully."}
        # Dummy real endpoint
        try:
            payload = {"name": details.get("rule_name"), "action": details.get("action")}
            response = self.session.post(f"{self.base_url}/asm/policies", json=payload)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_certificate_update(self, details: dict):
        if not self.host or self.host == "mock":
            return {"status": "success", "message": "Mock: Certificate applied successfully."}
        try:
            payload = {"command": "install", "name": details.get("cert_name")}
            response = self.session.post(f"{self.base_url}/sys/crypto/cert", json=payload)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def execute_f5_request(target_ip: str, request_type: str, details_json: dict) -> dict:
    """Wrapper function to instantiate client and call appropriate method."""
    client = F5Client(host=target_ip)
    
    if request_type == "info_query":
        return client.get_device_info()
    elif request_type == "waf_rule":
        return client.execute_waf_rule_change(details_json)
    elif request_type == "certificate":
        return client.execute_certificate_update(details_json)
    else:
        return {"status": "error", "message": "Unknown request type"}
