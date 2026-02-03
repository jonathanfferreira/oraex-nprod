"""
ORAEX - Alerting System
-----------------------
Sistema de alertas para notificação de eventos críticos.
Suporta múltiplos provedores: Slack, Email, PagerDuty, Console.

Uso:
    from automacao.utils.alerting import AlertManager, SlackAlert
    
    manager = AlertManager()
    manager.add_provider(SlackAlert())
    manager.send_alert("CRITICAL", "Database down!", {"db": "orcl"})
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AlertProvider(ABC):
    """Interface base para provedores de alerta."""
    
    @abstractmethod
    def send(self, severity: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envia um alerta.
        
        Args:
            severity: Nível do alerta (OK, WARNING, CRITICAL, ERROR)
            message: Mensagem principal
            details: Detalhes adicionais (opcional)
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do provedor."""
        pass


class ConsoleAlert(AlertProvider):
    """Alerta via console (stdout/stderr). Sempre disponível."""
    
    @property
    def name(self) -> str:
        return "Console"
    
    def send(self, severity: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output = f"[{timestamp}] [{severity}] {message}"
        
        if details:
            output += f" | Details: {details}"
        
        if severity in ("CRITICAL", "ERROR"):
            logging.error(output)
        elif severity == "WARNING":
            logging.warning(output)
        else:
            logging.info(output)
        
        return True


class SlackAlert(AlertProvider):
    """Alerta via Slack Webhook."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Args:
            webhook_url: URL do webhook Slack. Se não fornecido, usa SLACK_WEBHOOK_URL env.
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    
    @property
    def name(self) -> str:
        return "Slack"
    
    def send(self, severity: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        if not self.webhook_url:
            logging.warning("SLACK_WEBHOOK_URL não configurado. Alerta não enviado.")
            return False
        
        if not HAS_REQUESTS:
            logging.warning("Módulo 'requests' não instalado. Alerta Slack não enviado.")
            return False
        
        # Mapear severidade para emoji e cor
        emoji_map = {
            "OK": ":white_check_mark:",
            "WARNING": ":warning:",
            "CRITICAL": ":rotating_light:",
            "ERROR": ":x:"
        }
        color_map = {
            "OK": "#36a64f",
            "WARNING": "#f2c744",
            "CRITICAL": "#ff0000",
            "ERROR": "#8b0000"
        }
        
        emoji = emoji_map.get(severity, ":question:")
        color = color_map.get(severity, "#808080")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"{emoji} ORAEX Alert: {severity}",
                "text": message,
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in (details or {}).items()
                ],
                "footer": "ORAEX Monitoring",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Erro ao enviar alerta Slack: {e}")
            return False


class EmailAlert(AlertProvider):
    """Alerta via Email SMTP."""
    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        sender: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.smtp_server = smtp_server or os.environ.get("SMTP_SERVER")
        self.smtp_port = int(os.environ.get("SMTP_PORT", smtp_port))
        self.sender = sender or os.environ.get("ALERT_EMAIL_SENDER")
        self.recipients = recipients or os.environ.get("ALERT_EMAIL_RECIPIENTS", "").split(",")
        self.username = username or os.environ.get("SMTP_USERNAME")
        self.password = password or os.environ.get("SMTP_PASSWORD")
    
    @property
    def name(self) -> str:
        return "Email"
    
    def send(self, severity: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        if not self.smtp_server or not self.recipients:
            logging.warning("Configuração SMTP incompleta. Alerta não enviado.")
            return False
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender or "oraex@localhost"
            msg["To"] = ", ".join(self.recipients)
            msg["Subject"] = f"[ORAEX {severity}] {message[:50]}..."
            
            body = f"""
ORAEX Alert System
==================

Severity: {severity}
Message: {message}
Timestamp: {datetime.now().isoformat()}

Details:
{self._format_details(details)}

--
ORAEX Monitoring System
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar email: {e}")
            return False
    
    def _format_details(self, details: Optional[Dict[str, Any]]) -> str:
        if not details:
            return "N/A"
        return "\n".join(f"  - {k}: {v}" for k, v in details.items())


class AlertManager:
    """Gerenciador central de alertas. Coordena múltiplos providers."""
    
    def __init__(self):
        self.providers: List[AlertProvider] = []
        self._always_console = True
    
    def add_provider(self, provider: AlertProvider) -> "AlertManager":
        """Adiciona um provedor de alertas. Retorna self para chaining."""
        self.providers.append(provider)
        return self
    
    def send_alert(
        self, 
        severity: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Envia alerta para todos os providers configurados.
        
        Returns:
            Dict com nome do provider e status de envio
        """
        results = {}
        
        # Sempre logar no console
        if self._always_console:
            console = ConsoleAlert()
            results[console.name] = console.send(severity, message, details)
        
        # Enviar para providers adicionais
        for provider in self.providers:
            try:
                results[provider.name] = provider.send(severity, message, details)
            except Exception as e:
                logging.error(f"Erro em provider {provider.name}: {e}")
                results[provider.name] = False
        
        return results
    
    @classmethod
    def from_env(cls) -> "AlertManager":
        """
        Cria AlertManager configurado via variáveis de ambiente.
        
        Environment Variables:
            SLACK_WEBHOOK_URL: URL do webhook Slack (opcional)
            SMTP_SERVER: Servidor SMTP (opcional)
            ALERT_EMAIL_RECIPIENTS: Destinatários separados por vírgula (opcional)
        """
        manager = cls()
        
        # Auto-configurar Slack se webhook disponível
        if os.environ.get("SLACK_WEBHOOK_URL"):
            manager.add_provider(SlackAlert())
        
        # Auto-configurar Email se SMTP disponível
        if os.environ.get("SMTP_SERVER"):
            manager.add_provider(EmailAlert())
        
        return manager


# Instância singleton para uso fácil
_default_manager: Optional[AlertManager] = None

def get_alert_manager() -> AlertManager:
    """Retorna o AlertManager singleton."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AlertManager.from_env()
    return _default_manager


def send_alert(severity: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """Função de conveniência para enviar alertas."""
    return get_alert_manager().send_alert(severity, message, details)
