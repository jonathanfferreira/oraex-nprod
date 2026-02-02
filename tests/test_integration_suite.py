import unittest
import sys
import os
import json
import logging
from unittest.mock import MagicMock, patch
from io import StringIO

# Ajusta path para importar módulos da raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automacao.diagnosticos import oracle_healthcheck
from automacao.monitoramento import check_tablespaces

class TestIntegrationSuite(unittest.TestCase):
    """
    Testes de Integração simulando o fluxo completo de monitoramento.
    Valida: Credentials (ENV) -> Lógica de Negócio -> Logging (JSON) -> Output.
    """

    def setUp(self):
        # Configura Variáveis de Ambiente para o Teste
        self.env_patcher = patch.dict(os.environ, {
            "ORACLE_USER": "integration_user",
            "ORACLE_PASSWORD": "secret_password",
            "ORACLE_DSN": "integration_host/service"
        })
        self.env_patcher.start()

        # Mock Global do cx_Oracle
        self.oracle_patcher = patch("cx_Oracle.connect")
        self.mock_connect = self.oracle_patcher.start()
        
        # Configura Mock de Conexão e Cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Captura de Logs/Stdout
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        logging.getLogger().addHandler(self.handler)

    def tearDown(self):
        self.env_patcher.stop()
        self.oracle_patcher.stop()
        logging.getLogger().removeHandler(self.handler)

    def test_healthcheck_flow_json(self):
        """Testa fluxo completo do Healthcheck com saída JSON."""
        print("\n[Integration] Testando Oracle Healthcheck (JSON Flow)...")
        
        # Simulação inteligente de respostas do Banco baseada na Query SQL
        def side_effect_execute(sql, params=None):
            self.current_sql = sql.strip().upper()
        self.mock_cursor.execute.side_effect = side_effect_execute

        def side_effect_fetchall():
            # RMAN: Retorna 1 backup com sucesso
            if "V$RMAN_STATUS" in self.current_sql:
                return [("2023-01-01", "BACKUP", "DB FULL", "COMPLETED", 5000)]
            # Blocking Sessions: Vazio (Ninguém bloqueando)
            if "BLOCKING_SESSION" in self.current_sql:
                return []
            # TDE: TDE Configurado e Aberto
            if "V$ENCRYPTION_WALLET" in self.current_sql:
                return [("FILE", "OPEN", "AUTOLOGIN")]
            # ASH: Vazio
            if "V$ACTIVE_SESSION_HISTORY" in self.current_sql:
                return []
            
            # --- COMPLIANCE (Scalar Queries via fetchall) ---
            if "FORCE_LOGGING" in self.current_sql:
                return [("YES",)]
            if "RECYCLEBIN" in self.current_sql:
                return [("OFF",)]
            if "SPFILE" in self.current_sql:
                return [("/u01/app/oracle/dbs/spfileorcl.ora",)]
                
            return []

        self.mock_cursor.fetchall.side_effect = side_effect_fetchall
        # fetchone não é usado pelo BaseChecker, mas por segurança deixamos None
        self.mock_cursor.fetchone.return_value = None
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ["oracle_healthcheck.py", "--json"]):
            # Captura stdout para validar JSON final
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    oracle_healthcheck.main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
                
                output = fake_out.getvalue()
                try:
                    data = json.loads(output)
                    self.assertIn("summary", data)
                    # Agora esperamos 5 OKs reais
                    self.assertEqual(data["summary"]["ok"], 5, f"Esperado 5 OKs, obtido: {data['summary']}")
                    print("✅ JSON Output Validado (Todos Checkers OK)")
                except json.JSONDecodeError:
                    self.fail(f"Output não é JSON válido: {output}")

    def test_tablespace_flow_json_logging(self):
        """Testa monitoramento de Tablespaces com Logging JSON."""
        print("\n[Integration] Testando Monitoramento Tablespaces (JSON Logs)...")
        
        # Simula dados de tablespace (1 Crítica)
        # Retorno da query otimizada: (name, total, used, free, pct, sample_file)
        self.mock_cursor.fetchall.return_value = [
            ("USERS", 1000, 950, 50, 95.0, "/u01/users01.dbf"), # Crítica
            ("SYSTEM", 2000, 1000, 1000, 50.0, "/u01/system01.dbf") # OK
        ]

        # Mock sys.argv passando --json (ativa logs JSON)
        with patch.object(sys, 'argv', ["check_tablespaces.py", "--json", "--threshold", "80"]):
            # Captura stderr (onde vão os logs)
            with patch('sys.stderr', new=StringIO()) as fake_stderr:
                try:
                    check_tablespaces.main()
                except SystemExit as e:
                    self.assertEqual(e.code, 2) # Code 2 = Critical
                
                logs = fake_stderr.getvalue()
                # Valida se logs estão em JSON
                found_json_log = False
                for line in logs.splitlines():
                    try:
                        log_entry = json.loads(line)
                        if "USERS" in log_entry.get("message", "") and "95.0%" in log_entry.get("message", ""):
                            found_json_log = True
                            print(f"✅ Log JSON Encontrado: {line}")
                    except json.JSONDecodeError:
                        pass
                
                self.assertTrue(found_json_log, "Não encontrou log JSON da tablespace crítica")

if __name__ == "__main__":
    unittest.main()
