"""
Simulador de Alerta do Alertmanager
------------------------------------
Este script envia um payload fake para o webhook_receiver.py
para testar o fluxo de self-healing sem precisar do Prometheus.

Uso:
    python test_alert_simulator.py --runbook tablespace
    python test_alert_simulator.py --runbook archive
    python test_alert_simulator.py --runbook listener
"""
import requests
import json
import sys

WEBHOOK_URL = "http://localhost:5001/alert"

def simulate_alert(runbook_name: str, alert_name: str = None):
    """Envia um alerta fake para o webhook receiver."""
    
    if not alert_name:
        alert_name = {
            "tablespace": "TablespaceUsageWarning",
            "archive": "FRAUsageWarning",
            "listener": "ListenerDown"
        }.get(runbook_name, f"Test{runbook_name.title()}Alert")
    
    payload = {
        "receiver": "self-healing-receiver",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": alert_name,
                    "runbook": runbook_name,
                    "severity": "warning",
                    "database": "orcl",
                    "instance": "oracle-rac-node1"
                },
                "annotations": {
                    "summary": f"Test alert for {runbook_name} runbook",
                    "description": f"This is a simulated alert to test the {runbook_name} self-healing runbook."
                }
            }
        ],
        "groupLabels": {
            "alertname": alert_name
        },
        "commonLabels": {
            "alertname": alert_name,
            "runbook": runbook_name
        }
    }
    
    print(f"\n{'='*60}")
    print(f"🔔 SIMULANDO ALERTA: {alert_name}")
    print(f"📋 Runbook: {runbook_name}")
    print(f"🎯 Enviando para: {WEBHOOK_URL}")
    print(f"{'='*60}\n")
    
    print("Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n{'='*60}")
        print(f"📥 RESPOSTA DO WEBHOOK")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Alerta processado com sucesso!")
        else:
            print("\n❌ Erro ao processar alerta!")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao webhook receiver!")
        print("   Verifique se o webhook_receiver.py está rodando:")
        print("   python webhook_receiver.py")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simula alertas do Alertmanager")
    parser.add_argument("--runbook", required=True, 
                        choices=["tablespace", "archive", "listener"],
                        help="Runbook a ser acionado")
    parser.add_argument("--alert-name", help="Nome customizado do alerta")
    
    args = parser.parse_args()
    simulate_alert(args.runbook, args.alert_name)
