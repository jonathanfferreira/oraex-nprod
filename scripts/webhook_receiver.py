"""
Webhook Receiver para Alertmanager
----------------------------------
Servidor HTTP que recebe alertas do Prometheus Alertmanager
e aciona o runner.py correspondente.

Payload esperado:
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
import hmac
import hashlib
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

# Paths - Em Docker, o app roda em /app. Fora do Docker, subir um nível.
ORAEX_HOME = os.environ.get("ORAEX_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER_PATH = os.path.join(ORAEX_HOME, "automacao", "runbooks", "runner.py")

# Segurança - HMAC shared secret (opcional, mas recomendado em prod)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Timeout máximo para execução de runbooks (5 minutos)
RUNBOOK_TIMEOUT = int(os.environ.get("RUNBOOK_TIMEOUT", "300"))

# Runbooks permitidos (whitelist para evitar execução arbitrária)
ALLOWED_RUNBOOKS = {"tablespace", "listener", "archive"}


def verify_signature(payload: bytes, signature: str) -> bool:
    """Valida HMAC-SHA256 signature do request."""
    if not WEBHOOK_SECRET:
        return True  # Se não configurado, aceita tudo (lab mode)
    if not signature:
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.route('/alert', methods=['POST'])
def receive_alert():
    try:
        # Validar signature se WEBHOOK_SECRET estiver configurado
        if WEBHOOK_SECRET:
            signature = request.headers.get('X-Webhook-Signature', '')
            if not verify_signature(request.data, signature):
                logger.warning("Request com signature invalida rejeitado")
                return jsonify({"error": "Invalid signature"}), 401

        data = request.json
        logger.info(f"Alerta recebido: {data}")

        alerts = data.get('alerts', [])
        executed_runbooks = []

        for alert in alerts:
            status = alert.get('status')
            labels = alert.get('labels', {})
            alert_name = labels.get('alertname')
            runbook_target = labels.get('runbook')

            if status == 'firing' and runbook_target:
                # Validar runbook contra whitelist
                if runbook_target not in ALLOWED_RUNBOOKS:
                    logger.warning(f"Runbook '{runbook_target}' nao esta na whitelist")
                    executed_runbooks.append({
                        "alert": alert_name,
                        "runbook": runbook_target,
                        "success": False,
                        "error": "Runbook not in whitelist"
                    })
                    continue

                logger.info(f"Alerta Disparado: {alert_name} -> Runbook: {runbook_target}")

                # Verificar que runner existe
                if not os.path.exists(RUNNER_PATH):
                    logger.error(f"Runner nao encontrado: {RUNNER_PATH}")
                    executed_runbooks.append({
                        "alert": alert_name,
                        "runbook": runbook_target,
                        "success": False,
                        "error": f"Runner not found at {RUNNER_PATH}"
                    })
                    continue

                cmd = [sys.executable, RUNNER_PATH, "--runbook", runbook_target]
                logger.info(f"Executando: {' '.join(cmd)}")

                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True,
                        timeout=RUNBOOK_TIMEOUT
                    )
                    logger.info(f"Output: {result.stdout}")
                    if result.returncode != 0:
                        logger.error(f"Erro: {result.stderr}")

                    executed_runbooks.append({
                        "alert": alert_name,
                        "runbook": runbook_target,
                        "success": result.returncode == 0
                    })
                except subprocess.TimeoutExpired:
                    logger.error(f"Runbook {runbook_target} timeout ({RUNBOOK_TIMEOUT}s)")
                    executed_runbooks.append({
                        "alert": alert_name,
                        "runbook": runbook_target,
                        "success": False,
                        "error": f"Timeout after {RUNBOOK_TIMEOUT}s"
                    })

            elif status == 'resolved':
                logger.info(f"Alerta resolvido: {alert_name}")

        return jsonify({"status": "processed", "actions": executed_runbooks}), 200

    except Exception as e:
        logger.error(f"Erro processando webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    runner_exists = os.path.exists(RUNNER_PATH)
    return jsonify({
        "status": "up",
        "runner_path": RUNNER_PATH,
        "runner_exists": runner_exists
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get("WEBHOOK_PORT", os.environ.get("PORT", 5001)))
    app.run(host='0.0.0.0', port=port)
