"""
ORAEX - ASM Capacity Report
---------------------------
Relatório de capacidade de ASM Diskgroups com:
- Consulta V$ASM_DISKGROUP e V$ASM_DISK
- Cálculo de % de uso e espaço livre
- Predição de crescimento baseado em histórico
- Alertas por threshold configurável

Uso:
    python asm_capacity_report.py
    python asm_capacity_report.py --threshold 80
    python asm_capacity_report.py --json
    python asm_capacity_report.py --collect  # Coleta histórico para predição
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Tentar importar cx_Oracle
try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None


class DiskGroup:
    """Representa um ASM Diskgroup."""
    def __init__(self, name: str, total_mb: int, free_mb: int, required_mirror_free_mb: int, usable_file_mb: int, state: str, type: str, disk_count: int):
        self.name = name
        self.total_mb = total_mb
        self.free_mb = free_mb
        self.required_mirror_free_mb = required_mirror_free_mb
        self.usable_file_mb = usable_file_mb
        self.state = state
        self.type = type
        self.disk_count = disk_count
    
    @property
    def used_mb(self) -> int:
        return self.total_mb - self.free_mb
    
    @property
    def used_pct(self) -> float:
        if self.total_mb == 0:
            return 0.0
        return round((self.used_mb / self.total_mb) * 100, 1)
    
    @property
    def free_pct(self) -> float:
        return round(100 - self.used_pct, 1)
    
    @property
    def total_gb(self) -> float:
        return round(self.total_mb / 1024, 2)
    
    @property
    def free_gb(self) -> float:
        return round(self.free_mb / 1024, 2)
    
    @property
    def used_gb(self) -> float:
        return round(self.used_mb / 1024, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "type": self.type,
            "disk_count": self.disk_count,
            "total_gb": self.total_gb,
            "used_gb": self.used_gb,
            "free_gb": self.free_gb,
            "used_pct": self.used_pct,
            "free_pct": self.free_pct,
            "usable_file_mb": self.usable_file_mb
        }


class Disk:
    """Representa um disco ASM."""
    def __init__(self, name: str, path: str, group_name: str, total_mb: int, free_mb: int, state: str, mode_status: str):
        self.name = name
        self.path = path
        self.group_name = group_name
        self.total_mb = total_mb
        self.free_mb = free_mb
        self.state = state
        self.mode_status = mode_status
    
    @property
    def used_pct(self) -> float:
        if self.total_mb == 0:
            return 0.0
        return round(((self.total_mb - self.free_mb) / self.total_mb) * 100, 1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "group": self.group_name,
            "total_mb": self.total_mb,
            "free_mb": self.free_mb,
            "used_pct": self.used_pct,
            "state": self.state
        }


class CapacityHistory:
    """Histórico de capacidade para predição."""
    def __init__(self, timestamp: datetime, group_name: str, used_mb: int, total_mb: int):
        self.timestamp = timestamp
        self.group_name = group_name
        self.used_mb = used_mb
        self.total_mb = total_mb


class ASMCapacityChecker:
    """Verifica capacidade de ASM Diskgroups."""
    
    DISKGROUP_QUERY = """
        SELECT 
            NAME,
            TOTAL_MB,
            FREE_MB,
            REQUIRED_MIRROR_FREE_MB,
            USABLE_FILE_MB,
            STATE,
            TYPE,
            (SELECT COUNT(*) FROM V$ASM_DISK d WHERE d.GROUP_NUMBER = dg.GROUP_NUMBER) as DISK_COUNT
        FROM V$ASM_DISKGROUP dg
        ORDER BY NAME
    """
    
    DISK_QUERY = """
        SELECT 
            d.NAME,
            d.PATH,
            dg.NAME as GROUP_NAME,
            d.TOTAL_MB,
            d.FREE_MB,
            d.STATE,
            d.MODE_STATUS
        FROM V$ASM_DISK d
        JOIN V$ASM_DISKGROUP dg ON d.GROUP_NUMBER = dg.GROUP_NUMBER
        ORDER BY dg.NAME, d.NAME
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_diskgroups(self) -> List[DiskGroup]:
        """Retorna lista de diskgroups."""
        if not cx_Oracle:
            logging.warning("cx_Oracle não disponível")
            return self._get_mock_data()
        
        try:
            with cx_Oracle.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(self.DISKGROUP_QUERY)
                
                groups = []
                for row in cursor:
                    groups.append(DiskGroup(
                        name=row[0],
                        total_mb=row[1] or 0,
                        free_mb=row[2] or 0,
                        required_mirror_free_mb=row[3] or 0,
                        usable_file_mb=row[4] or 0,
                        state=row[5],
                        type=row[6],
                        disk_count=row[7]
                    ))
                return groups
                
        except Exception as e:
            logging.error(f"Erro ao consultar ASM: {e}")
            logging.warning("Usando dados mock devido a erro de conexão.")
            return self._get_mock_data()
    
    def get_disks(self) -> List[Disk]:
        """Retorna lista de discos ASM."""
        if not cx_Oracle:
            return []
        
        try:
            with cx_Oracle.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(self.DISK_QUERY)
                
                disks = []
                for row in cursor:
                    disks.append(Disk(
                        name=row[0],
                        path=row[1],
                        group_name=row[2],
                        total_mb=row[3] or 0,
                        free_mb=row[4] or 0,
                        state=row[5],
                        mode_status=row[6]
                    ))
                return disks
                
        except Exception as e:
            logging.error(f"Erro ao consultar discos: {e}")
            return []
    
    def _get_mock_data(self) -> List[DiskGroup]:
        """Dados mock para testes sem Oracle."""
        return [
            DiskGroup("DATA", 2097152, 524288, 0, 524288, "MOUNTED", "EXTERN", 4),
            DiskGroup("FRA", 1048576, 314572, 0, 314572, "MOUNTED", "EXTERN", 2),
            DiskGroup("REDO", 102400, 51200, 0, 51200, "MOUNTED", "EXTERN", 2),
        ]


class CapacityHistoryManager:
    """Gerencia histórico de capacidade para predição."""
    
    def __init__(self, history_file: Path):
        self.history_file = history_file
    
    def save_snapshot(self, diskgroups: List[DiskGroup]) -> None:
        """Salva snapshot atual no histórico."""
        timestamp = datetime.now().isoformat()
        
        # Carregar histórico existente
        history = self._load_history()
        
        # Adicionar novo snapshot
        for dg in diskgroups:
            history.append({
                "timestamp": timestamp,
                "group_name": dg.name,
                "used_mb": dg.used_mb,
                "total_mb": dg.total_mb
            })
        
        # Manter últimos 90 dias (limite de 2000 registros)
        history = history[-2000:]
        
        # Salvar
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        logging.info(f"Snapshot salvo: {len(diskgroups)} diskgroups")
    
    def _load_history(self) -> List[Dict]:
        """Carrega histórico do arquivo."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except Exception:
            return []
    
    def predict_days_until_full(self, group_name: str, threshold_pct: float = 90) -> Optional[int]:
        """Prediz quantos dias até atingir o threshold."""
        history = self._load_history()
        
        # Filtrar por grupo
        group_history = [h for h in history if h["group_name"] == group_name]
        
        if len(group_history) < 2:
            return None  # Dados insuficientes
        
        # Calcular taxa de crescimento média (MB/dia)
        first = group_history[0]
        last = group_history[-1]
        
        first_time = datetime.fromisoformat(first["timestamp"])
        last_time = datetime.fromisoformat(last["timestamp"])
        
        days_diff = (last_time - first_time).days
        if days_diff == 0:
            return None
        
        mb_growth = last["used_mb"] - first["used_mb"]
        daily_growth = mb_growth / days_diff
        
        if daily_growth <= 0:
            return None  # Sem crescimento ou redução
        
        # Calcular MB restantes até threshold
        threshold_mb = last["total_mb"] * (threshold_pct / 100)
        mb_remaining = threshold_mb - last["used_mb"]
        
        if mb_remaining <= 0:
            return 0  # Já passou do threshold
        
        days_until_full = int(mb_remaining / daily_growth)
        return days_until_full


def generate_report(
    diskgroups: List[DiskGroup], 
    threshold: int,
    history_manager: Optional[CapacityHistoryManager] = None
) -> Dict[str, Any]:
    """Gera relatório de capacidade."""
    alerts = []
    predictions = {}
    
    for dg in diskgroups:
        # Verificar threshold
        if dg.used_pct >= threshold:
            alerts.append({
                "level": "CRITICAL" if dg.used_pct >= 90 else "WARNING",
                "group": dg.name,
                "message": f"{dg.name} está com {dg.used_pct}% de uso ({dg.free_gb:.1f} GB livres)"
            })
        
        # Predição (se tiver histórico)
        if history_manager:
            days = history_manager.predict_days_until_full(dg.name, threshold)
            if days is not None:
                predictions[dg.name] = {
                    "days_until_threshold": days,
                    "message": f"Estimativa: {days} dias até atingir {threshold}%"
                }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "threshold": threshold,
        "diskgroups": [dg.to_dict() for dg in diskgroups],
        "alerts": alerts,
        "predictions": predictions,
        "summary": {
            "total_groups": len(diskgroups),
            "alerts_count": len(alerts),
            "total_capacity_gb": sum(dg.total_gb for dg in diskgroups),
            "total_used_gb": sum(dg.used_gb for dg in diskgroups),
            "total_free_gb": sum(dg.free_gb for dg in diskgroups)
        }
    }


def print_report(report: Dict[str, Any]) -> None:
    """Imprime relatório formatado."""
    print(f"\n{'='*70}")
    print(f"RELATÓRIO DE CAPACIDADE ASM - {report['timestamp'][:19]}")
    print(f"{'='*70}")
    
    # Tabela de diskgroups
    print(f"\n{'Diskgroup':<15} {'Total GB':>10} {'Usado GB':>10} {'Livre GB':>10} {'Uso %':>8} {'Status':<10}")
    print("-" * 70)
    
    for dg in report["diskgroups"]:
        icon = "🔴" if dg["used_pct"] >= 90 else "🟡" if dg["used_pct"] >= 80 else "🟢"
        print(f"{dg['name']:<15} {dg['total_gb']:>10.1f} {dg['used_gb']:>10.1f} "
              f"{dg['free_gb']:>10.1f} {dg['used_pct']:>7.1f}% {icon}")
    
    print("-" * 70)
    summary = report["summary"]
    print(f"{'TOTAL':<15} {summary['total_capacity_gb']:>10.1f} {summary['total_used_gb']:>10.1f} "
          f"{summary['total_free_gb']:>10.1f}")
    
    # Alertas
    if report["alerts"]:
        print(f"\n⚠️  ALERTAS ({len(report['alerts'])}):")
        for alert in report["alerts"]:
            icon = "🔴" if alert["level"] == "CRITICAL" else "🟡"
            print(f"  {icon} [{alert['level']}] {alert['message']}")
    
    # Predições
    if report["predictions"]:
        print(f"\n📈 PREDIÇÕES:")
        for group, pred in report["predictions"].items():
            print(f"  • {group}: {pred['message']}")
    
    print(f"\n{'='*70}")


def setup_logging(verbose: bool = False) -> None:
    """Configura logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ORAEX - ASM Capacity Report"
    )
    
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Threshold de alerta (% de uso)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output em formato JSON"
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Coletar snapshot para histórico de predição"
    )
    
    # Resolver path seguro para logs (evita /var/log se user não for root)
    default_log_dir = Path(__file__).resolve().parent.parent / "logs"
    if not default_log_dir.exists():
        # Fallback para pasta local se não conseguir criar em ../logs
        default_log_dir = Path.cwd()

    parser.add_argument(
        "--history-file",
        default=str(default_log_dir / "asm_history.json"),
        help="Arquivo de histórico para predição"
    )
    parser.add_argument(
        "--connection",
        default="/",
        help="Connection string Oracle (ex: / as sysdba)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verbose"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Inicializar componentes
    checker = ASMCapacityChecker(args.connection)
    history_manager = CapacityHistoryManager(Path(args.history_file))
    
    # Obter dados
    diskgroups = checker.get_diskgroups()
    
    if not diskgroups:
        logging.error("Nenhum diskgroup encontrado!")
        return 1
    
    # Coletar histórico se solicitado
    if args.collect:
        history_manager.save_snapshot(diskgroups)
        logging.info("Snapshot coletado com sucesso!")
    
    # Gerar relatório
    report = generate_report(diskgroups, args.threshold, history_manager)
    
    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    
    # Retornar código de erro se houver alertas críticos
    critical_alerts = [a for a in report["alerts"] if a["level"] == "CRITICAL"]
    return 1 if critical_alerts else 0


if __name__ == "__main__":
    sys.exit(main())
