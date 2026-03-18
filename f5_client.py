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
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-F5-Auth-Token": "" # To be populated if needed, though Basic Auth works for many endpoints
        })

    def get_device_info(self):
        """Retrieve basic device information via REST API"""
        if not self.host or self.host == "mock":
            return {"status": "success", "message": "Mock: Device info retrieved successfully. version: 15.1.x"}
        try:
            # Get device info
            response = self.session.get(f"{self.base_url}/cm/device")
            response.raise_for_status()
            devices = response.json().get("items", [])
            
            if not devices:
                return {"status": "error", "message": "No devices found."}

            device = devices[0] # Usually the first is the target device
            info = {
                "hostname": device.get("hostname"),
                "version": device.get("version"),
                "build": device.get("build"),
                "managementIp": device.get("managementIp"),
                "platformId": device.get("platformId")
            }
            return {"status": "success", "data": info}
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_waf_rule_change(self, details: dict):
        """Enable or Disable a WAF policy (ASM)"""
        if not self.host or self.host == "mock":
            return {"status": "success", "message": f"Mock: WAF rule {details.get('action', 'updated')} successfully."}
        
        try:
            policy_name = details.get("rule_name")
            action = details.get("action") # e.g. "enable" or "disable"
            
            # Application Security Manager (ASM) policies endpoint
            # A real implementation might require finding the policy ID first
            policies_url = f"{self.base_url}/asm/policies"
            resp = self.session.get(policies_url, params={"$filter": f"name eq '{policy_name}'"})
            resp.raise_for_status()
            items = resp.json().get("items", [])
            
            if not items:
                return {"status": "error", "message": f"WAF Policy '{policy_name}' not found."}
                
            policy_id = items[0].get("id")
            
            # Apply the action (e.g., set enforcement mode to blocking or transparent)
            enforcement_mode = "blocking" if action.lower() == "enable" else "transparent"
            patch_url = f"{policies_url}/{policy_id}"
            
            patch_payload = {
                "enforcementMode": enforcement_mode
            }
            patch_resp = self.session.patch(patch_url, json=patch_payload)
            patch_resp.raise_for_status()
            
            # ASM metadata needs to be applied after changes
            apply_payload = {
                "policyReference": {
                    "link": f"https://localhost/mgmt/tm/asm/policies/{policy_id}"
                }
            }
            apply_resp = self.session.post(f"{self.base_url}/asm/tasks/apply-policy", json=apply_payload)
            apply_resp.raise_for_status()
            
            return {"status": "success", "message": f"WAF Policy enforcement mode changed to {enforcement_mode} and applied."}
            
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_certificate_update(self, details: dict):
        """Install a certificate and optionally key onto the F5 system."""
        if not self.host or self.host == "mock":
            return {"status": "success", "message": "Mock: Certificate applied successfully."}
        try:
            cert_name = details.get("cert_name") # The name to save the cert as on F5
            cert_content = details.get("cert_content", "dummy-cert-content")
            
            # This uses the sys crypto cert install endpoint
            # Note: The iControl REST implementation usually requires the file to be uploaded to /var/config/rest/downloads first via a different endpoint
            # For simplicity in this script, we'll assume we're doing a direct transaction if supported, or providing a mock real response
            
            payload = {
                "command": "install",
                "name": cert_name,
                "from-local-file": "/var/config/rest/downloads/uploaded_cert.crt" # This would be replaced with actual file logic
            }
            # As a safeguard to not break unknown APIs, we simulate the POST target here unless the user has exactly this file path
            response = self.session.post(f"{self.base_url}/sys/crypto/cert", json=payload)
            
            if response.status_code == 400 and "does not exist" in response.text:
                 # Provide a detailed warning that file upload needs to be built fully
                 return {"status": "error", "message": "Certificate file must be uploaded to the F5 device first before installing."}
                 
            response.raise_for_status()
            return {"status": "success", "data": response.json(), "message": f"Certificate {cert_name} installed."}
            
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
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
