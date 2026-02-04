"""
Webhook Receiver para Alertmanager
----------------------------------
Servidor HTTP leve que recebe alertas do Prometheus Alertmanager
e aciona o runner.py correspondente.

Payload esperado (exemplo simplificado):
{
  "alerts": [
    {
      "labels": {
         "alertname": "TablespaceFull",
         "runbook": "tablespace"
      },
      "status": "firing"
    }
  ]
}
"""
import logging
import subprocess
import sys
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WebhookReceiver")

ORAEX_HOME = os.path.dirname(os.path.abspath(__file__))
RUNNER_PATH = os.path.join(ORAEX_HOME, "automacao", "runbooks", "runner.py")

@app.route('/alert', methods=['POST'])
def receive_alert():
    try:
        data = request.json
        logger.info(f"Monitorando alerta: {data}")
        
        alerts = data.get('alerts', [])
        executed_runbooks = []
        
        for alert in alerts:
            status = alert.get('status')
            labels = alert.get('labels', {})
            alert_name = labels.get('alertname')
            runbook_target = labels.get('runbook') # Label customizada no Prometheus
            
            if status == 'firing' and runbook_target:
                logger.info(f"🔔 Alerta Disparado: {alert_name} -> Runbook: {runbook_target}")
                
                # Executar o runner
                cmd = [sys.executable, RUNNER_PATH, "--runbook", runbook_target]
                
                # Exemplo: passar argumentos extras se vierem nas annotations
                # if 'ssh_host' in labels: ...
                
                logger.info(f"Executando: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                logger.info(f"Output: {result.stdout}")
                if result.returncode != 0:
                    logger.error(f"Erro: {result.stderr}")
                
                executed_runbooks.append({
                    "alert": alert_name,
                    "runbook": runbook_target,
                    "success": result.returncode == 0
                })
        
        return jsonify({"status": "processed", "actions": executed_runbooks}), 200

    except Exception as e:
        logger.error(f"Erro processando webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "up"}), 200

if __name__ == '__main__':
    # Em produção, usar waitress ou gunicorn
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
