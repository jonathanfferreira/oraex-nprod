import requests
import sys

SERVICES = {
    "Automation": "http://localhost:5001/health",
    "Prometheus": "http://localhost:9090/-/healthy",
    "Grafana": "http://localhost:3000/api/health"
}

def check_services():
    failed = False
    print("Checking Docker Services...")
    
    for name, url in SERVICES.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[OK] {name} is UP ({url})")
            else:
                print(f"[FAIL] {name} returned status {response.status_code}")
                failed = True
        except Exception as e:
            print(f"[FAIL] {name} is unreachable: {e}")
            failed = True
            
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    check_services()
