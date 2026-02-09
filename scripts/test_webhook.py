import requests
import json

payload = {
  "alerts": [
    {
      "status": "firing",
      "labels": {
         "alertname": "TestTablespaceFull",
         "runbook": "tablespace",
         "severity": "critical"
      }
    }
  ]
}

try:
    resp = requests.post("http://localhost:5001/alert", json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Failed: {e}")
