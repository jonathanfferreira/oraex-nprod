#!/usr/bin/env python3
"""
ORAEX - Gerador de Relatório HTML
---------------------------------
Gera um dashboard visual standalone (sem dependências externas)
mostrando o status consolidado de todos os checks.

Uso:
    python generate_report.py --user system --dsn localhost:1521/orcl
    
Output:
    oraex_report_YYYYMMDD_HHMMSS.html
"""

import cx_Oracle
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class ReportGenerator:
    def __init__(self, username: str, password: str, dsn: str):
        self.username = username
        self.password = password
        self.dsn = dsn
        self.connection = None
        self.results: Dict[str, Dict] = {}
    
    def connect(self):
        try:
            self.connection = cx_Oracle.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
                encoding="UTF-8"
            )
        except cx_Oracle.Error as e:
            self.results['connection'] = {'status': 'CRITICAL', 'message': str(e)}
            return False
        return True
    
    def check_database_info(self):
        """Coleta informações básicas do banco."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT name, db_unique_name, open_mode, database_role FROM v$database")
            row = cursor.fetchone()
            self.results['database'] = {
                'status': 'OK',
                'name': row[0],
                'unique_name': row[1],
                'open_mode': row[2],
                'role': row[3]
            }
        except Exception as e:
            self.results['database'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def check_instance_info(self):
        """Coleta informações da instância."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT instance_name, host_name, version, status, 
                       to_char(startup_time, 'DD/MM/YYYY HH24:MI') 
                FROM v$instance
            """)
            row = cursor.fetchone()
            self.results['instance'] = {
                'status': 'OK' if row[3] == 'OPEN' else 'WARNING',
                'name': row[0],
                'host': row[1],
                'version': row[2],
                'db_status': row[3],
                'startup': row[4]
            }
        except Exception as e:
            self.results['instance'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def check_tablespaces(self):
        """Verifica ocupação de tablespaces."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT 
                    df.tablespace_name,
                    ROUND(df.bytes/1024/1024) total_mb,
                    ROUND((df.bytes - NVL(fs.bytes,0))/1024/1024) used_mb,
                    ROUND(((df.bytes - NVL(fs.bytes,0)) / df.bytes) * 100, 1) pct_used
                FROM 
                    (SELECT tablespace_name, SUM(bytes) bytes FROM dba_data_files GROUP BY tablespace_name) df
                LEFT JOIN 
                    (SELECT tablespace_name, SUM(bytes) bytes FROM dba_free_space GROUP BY tablespace_name) fs
                ON df.tablespace_name = fs.tablespace_name
                ORDER BY pct_used DESC
            """)
            tbs_list = []
            critical = False
            warning = False
            for row in cursor.fetchall():
                pct = row[3] or 0
                status = 'OK'
                if pct >= 95:
                    status = 'CRITICAL'
                    critical = True
                elif pct >= 85:
                    status = 'WARNING'
                    warning = True
                tbs_list.append({
                    'name': row[0],
                    'total_mb': row[1],
                    'used_mb': row[2],
                    'pct_used': pct,
                    'status': status
                })
            
            overall = 'CRITICAL' if critical else ('WARNING' if warning else 'OK')
            self.results['tablespaces'] = {'status': overall, 'items': tbs_list}
        except Exception as e:
            self.results['tablespaces'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def check_blocking_sessions(self):
        """Verifica sessões bloqueadoras."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM v$session WHERE blocking_session IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            self.results['blocking'] = {
                'status': 'CRITICAL' if count > 0 else 'OK',
                'count': count
            }
        except Exception as e:
            self.results['blocking'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def check_rman_backup(self):
        """Verifica último backup RMAN."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT 
                    MAX(CASE WHEN operation = 'BACKUP' AND object_type = 'DB FULL' THEN start_time END) last_full,
                    MAX(CASE WHEN operation = 'BACKUP' AND object_type = 'ARCHIVELOG' THEN start_time END) last_arch
                FROM v$rman_status
                WHERE status = 'COMPLETED'
            """)
            row = cursor.fetchone()
            last_full = row[0]
            last_arch = row[1]
            
            status = 'OK'
            if last_full is None:
                status = 'WARNING'
            elif (datetime.now() - last_full).days > 1:
                status = 'CRITICAL'
            
            self.results['rman'] = {
                'status': status,
                'last_full': str(last_full) if last_full else 'N/A',
                'last_arch': str(last_arch) if last_arch else 'N/A'
            }
        except Exception as e:
            self.results['rman'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def check_compliance(self):
        """Verifica compliance com Book DBA."""
        cursor = self.connection.cursor()
        checks = []
        try:
            # Force Logging
            cursor.execute("SELECT force_logging FROM v$database")
            fl = cursor.fetchone()[0]
            checks.append({'name': 'FORCE_LOGGING', 'value': fl, 'expected': 'YES', 'ok': fl == 'YES'})
            
            # Recyclebin
            cursor.execute("SELECT value FROM v$parameter WHERE name = 'recyclebin'")
            rb = cursor.fetchone()[0]
            checks.append({'name': 'RECYCLEBIN', 'value': rb, 'expected': 'off', 'ok': rb.lower() == 'off'})
            
            # SPFILE
            cursor.execute("SELECT value FROM v$parameter WHERE name = 'spfile'")
            sp = cursor.fetchone()[0]
            checks.append({'name': 'SPFILE', 'value': 'Configurado' if sp else 'NÃO', 'expected': 'Configurado', 'ok': bool(sp)})
            
            all_ok = all(c['ok'] for c in checks)
            self.results['compliance'] = {'status': 'OK' if all_ok else 'WARNING', 'checks': checks}
        except Exception as e:
            self.results['compliance'] = {'status': 'ERROR', 'message': str(e)}
        finally:
            cursor.close()

    def run_all_checks(self):
        """Executa todas as verificações."""
        if not self.connect():
            return
        
        self.check_database_info()
        self.check_instance_info()
        self.check_tablespaces()
        self.check_blocking_sessions()
        self.check_rman_backup()
        self.check_compliance()

    def generate_html(self) -> str:
        """Gera o HTML do relatório."""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Determinar status geral
        statuses = [v.get('status', 'OK') for v in self.results.values()]
        if 'CRITICAL' in statuses:
            overall = 'CRITICAL'
            overall_color = '#dc3545'
            overall_emoji = '🔴'
        elif 'WARNING' in statuses:
            overall = 'WARNING'
            overall_color = '#ffc107'
            overall_emoji = '🟡'
        elif 'ERROR' in statuses:
            overall = 'ERROR'
            overall_color = '#6c757d'
            overall_emoji = '⚫'
        else:
            overall = 'OK'
            overall_color = '#28a745'
            overall_emoji = '🟢'

        # CSS inline para ser standalone
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ORAEX Report - {timestamp}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee; 
            min-height: 100vh; 
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            text-align: center; 
            padding: 30px; 
            background: rgba(255,255,255,0.05); 
            border-radius: 15px; 
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .status-badge {{
            display: inline-block;
            padding: 10px 30px;
            border-radius: 50px;
            font-size: 1.2em;
            font-weight: bold;
            background: {overall_color};
            color: white;
            margin-top: 15px;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .card-header h3 {{ font-size: 1.2em; }}
        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .badge-ok {{ background: #28a745; }}
        .badge-warning {{ background: #ffc107; color: #000; }}
        .badge-critical {{ background: #dc3545; }}
        .badge-error {{ background: #6c757d; }}
        .info-row {{ 
            display: flex; 
            justify-content: space-between; 
            padding: 8px 0; 
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .info-label {{ color: #aaa; }}
        .info-value {{ font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #aaa; font-weight: normal; }}
        .progress-bar {{
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ ORAEX Automation Report</h1>
            <p>Gerado em: {timestamp}</p>
            <div class="status-badge">{overall_emoji} Status Geral: {overall}</div>
        </div>
        
        <div class="grid">
"""
        # Card: Database Info
        db = self.results.get('database', {})
        inst = self.results.get('instance', {})
        html += f"""
            <div class="card">
                <div class="card-header">
                    <h3>📊 Informações do Banco</h3>
                    <span class="badge badge-{db.get('status', 'error').lower()}">{db.get('status', 'ERROR')}</span>
                </div>
                <div class="info-row"><span class="info-label">Database</span><span class="info-value">{db.get('name', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Unique Name</span><span class="info-value">{db.get('unique_name', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Open Mode</span><span class="info-value">{db.get('open_mode', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Role</span><span class="info-value">{db.get('role', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Host</span><span class="info-value">{inst.get('host', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Versão</span><span class="info-value">{inst.get('version', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Startup</span><span class="info-value">{inst.get('startup', 'N/A')}</span></div>
            </div>
"""
        # Card: RMAN Backup
        rman = self.results.get('rman', {})
        html += f"""
            <div class="card">
                <div class="card-header">
                    <h3>💾 Backup RMAN</h3>
                    <span class="badge badge-{rman.get('status', 'error').lower()}">{rman.get('status', 'ERROR')}</span>
                </div>
                <div class="info-row"><span class="info-label">Último Full</span><span class="info-value">{rman.get('last_full', 'N/A')}</span></div>
                <div class="info-row"><span class="info-label">Último Archivelog</span><span class="info-value">{rman.get('last_arch', 'N/A')}</span></div>
            </div>
"""
        # Card: Blocking Sessions
        blocking = self.results.get('blocking', {})
        html += f"""
            <div class="card">
                <div class="card-header">
                    <h3>🔒 Sessões Bloqueadas</h3>
                    <span class="badge badge-{blocking.get('status', 'error').lower()}">{blocking.get('status', 'ERROR')}</span>
                </div>
                <div class="info-row"><span class="info-label">Bloqueios Ativos</span><span class="info-value">{blocking.get('count', 'N/A')}</span></div>
            </div>
"""
        # Card: Compliance
        compliance = self.results.get('compliance', {})
        checks_html = ""
        for c in compliance.get('checks', []):
            icon = '✅' if c['ok'] else '❌'
            checks_html += f"<div class='info-row'><span class='info-label'>{c['name']}</span><span class='info-value'>{icon} {c['value']}</span></div>"
        
        html += f"""
            <div class="card">
                <div class="card-header">
                    <h3>📋 Compliance (Book DBA)</h3>
                    <span class="badge badge-{compliance.get('status', 'error').lower()}">{compliance.get('status', 'ERROR')}</span>
                </div>
                {checks_html}
            </div>
"""
        # Card: Tablespaces (expandido)
        tbs = self.results.get('tablespaces', {})
        tbs_html = "<table><tr><th>Tablespace</th><th>Usado</th><th>%</th></tr>"
        for t in tbs.get('items', [])[:10]:  # Top 10
            pct = t['pct_used']
            color = '#28a745' if pct < 85 else ('#ffc107' if pct < 95 else '#dc3545')
            tbs_html += f"""
                <tr>
                    <td>{t['name']}</td>
                    <td>{t['used_mb']} / {t['total_mb']} MB</td>
                    <td>
                        <div class="progress-bar"><div class="progress-fill" style="width:{pct}%; background:{color};"></div></div>
                        {pct}%
                    </td>
                </tr>
            """
        tbs_html += "</table>"
        
        html += f"""
            <div class="card" style="grid-column: span 2;">
                <div class="card-header">
                    <h3>📁 Tablespaces (Top 10)</h3>
                    <span class="badge badge-{tbs.get('status', 'error').lower()}">{tbs.get('status', 'ERROR')}</span>
                </div>
                {tbs_html}
            </div>
"""
        # Footer
        html += """
        </div>
        <div class="footer">
            <p>Gerado por ORAEX Automation Suite | Getnet DBA Team</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def save_report(self):
        """Salva o relatório em arquivo."""
        self.run_all_checks()
        html = self.generate_html()
        
        filename = f"oraex_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Relatório gerado: {filename}")
        return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ORAEX - Gerador de Relatório HTML')
    parser.add_argument('--user', help='Usuário do Banco', default='system')
    parser.add_argument('--password', help='Senha do Banco', default='oracle')
    parser.add_argument('--dsn', help='Connection String (IP:Port/Service)', default='localhost:1521/orcl')
    
    args = parser.parse_args()
    
    generator = ReportGenerator(args.user, args.password, args.dsn)
    generator.save_report()
