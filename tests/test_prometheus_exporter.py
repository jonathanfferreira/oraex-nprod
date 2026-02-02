"""
Testes unitários para Prometheus Exporter
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ajusta path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automacao.monitoramento.prometheus_exporter import collect_metrics_mock, HAS_PROM

class TestPrometheusExporter(unittest.TestCase):

    def setUp(self):
        if not HAS_PROM:
            self.skipTest("Prometheus client library not installed")

    @patch('automacao.monitoramento.prometheus_exporter.G_TABLESPACE_USED')
    @patch('automacao.monitoramento.prometheus_exporter.G_ASM_FREE_GB')
    def test_collect_metrics_modifies_gauges(self, mock_asm, mock_tbs):
        # Executa coleta
        collect_metrics_mock()
        
        # Verifica se os gauges foram chamados
        self.assertTrue(mock_tbs.labels.called)
        self.assertTrue(mock_asm.labels.called)

    def test_library_availability(self):
        # Apenas garante que a flag está correta
        self.assertTrue(isinstance(HAS_PROM, bool))

if __name__ == '__main__':
    unittest.main()
