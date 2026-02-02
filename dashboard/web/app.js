const API_BASE = '/api';

async function fetchJSON(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        return await res.json();
    } catch (err) {
        console.error(`Error fetching ${endpoint}:`, err);
        return null;
    }
}

async function loadSystemInfo() {
    const data = await fetchJSON('/health');
    if (data) {
        document.getElementById('system-info').textContent =
            `${data.hostname} | ${data.platform} | v${data.version}`;
    }
}

async function loadHealth() {
    const data = await fetchJSON('/checks');
    if (data) {
        const el = document.getElementById('health-summary');
        el.textContent = data.status;
        el.className = 'metric-big ' +
            (data.status === 'OK' ? 'status-ok' :
                data.status === 'WARNING' ? 'status-warn' : 'status-crit');

        document.getElementById('health-ok').textContent = data.ok;
        document.getElementById('health-warn').textContent = data.warnings;
        document.getElementById('health-crit').textContent = data.critical;
    }
}

async function loadCapacity() {
    const data = await fetchJSON('/capacity');
    const container = document.getElementById('capacity-list');

    if (data && data.diskgroups) {
        container.innerHTML = data.diskgroups.map(dg => {
            const usageClass = dg.used_pct > 90 ? 'crit' : dg.used_pct > 80 ? 'high' : 'ok';
            return `
                <div class="disk-group">
                    <div class="disk-item">
                        <span>${dg.name}</span>
                        <span>${dg.used_pct}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${usageClass}" style="width: ${dg.used_pct}%"></div>
                    </div>
                    <div class="disk-item" style="font-size: 0.75rem; color: #8b949e;">
                        Free: ${dg.free_gb.toFixed(1)} GB / ${dg.total_gb.toFixed(1)} GB
                    </div>
                </div>
            `;
        }).join('');
    }
}

async function loadBackups() {
    const data = await fetchJSON('/backups');
    const container = document.getElementById('backup-list');

    if (data) {
        container.innerHTML = data.map(job => {
            const statusClass = job.status === 'COMPLETED' ? 'status-ok' : 'status-crit';
            const date = new Date(job.start_time).toLocaleDateString();
            return `
                <div class="backup-item">
                    <div>
                        <div style="font-weight:bold">${job.input_type}</div>
                        <div style="font-size:0.75rem">${date}</div>
                    </div>
                    <div style="text-align:right">
                        <span class="status-badge ${statusClass}">${job.status}</span>
                        <div style="font-size:0.75rem; margin-top:2px">${job.output_gb.toFixed(1)} GB</div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

function init() {
    loadSystemInfo();
    loadHealth();
    loadCapacity();
    loadBackups();

    // Refresh every 30s
    setInterval(() => {
        loadHealth();
        loadCapacity();
        loadBackups();
    }, 30000);
}

document.addEventListener('DOMContentLoaded', init);
