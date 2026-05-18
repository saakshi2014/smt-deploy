// kpi_dashboard.js — KPI Dashboard JavaScript
// Handles: fetch KPIs, render progress bars,
//          team KPI comparison, custom KPI input,
//          deactivate custom KPI columns

// ── KPI DEFINITIONS ───────────────────────────────────────────────────────────
const KPI_DEFINITIONS = {
    // Lead Measures
    outreachCount: {
        label:    "Outreach Count",
        desc:     "Connection requests sent",
        type:     "lead",
        unit:     "requests",
        icon:     "bi-send",
        color:    "#1565C0"
    },
    connectionRate: {
        label:    "Connection Rate",
        desc:     "% of requests accepted",
        type:     "lead",
        unit:     "%",
        icon:     "bi-people",
        color:    "#6A1B9A"
    },
    initialMessageCount: {
        label:    "Initial Messages",
        desc:     "First messages sent",
        type:     "lead",
        unit:     "messages",
        icon:     "bi-chat-dots",
        color:    "#00695C"
    },
    replyRate: {
        label:    "Reply Rate",
        desc:     "% of messages that got a reply",
        type:     "lead",
        unit:     "%",
        icon:     "bi-reply",
        color:    "#E65100"
    },
    meetingConversionRate: {
        label:    "Meeting Conversion",
        desc:     "% of replies that became meetings",
        type:     "lead",
        unit:     "%",
        icon:     "bi-arrow-repeat",
        color:    "#283593"
    },

    // Lag Measures
    meetingsScheduled: {
        label:    "Meetings Scheduled",
        desc:     "Total meetings booked",
        type:     "lag",
        unit:     "meetings",
        icon:     "bi-calendar-check",
        color:    "#1B5E20"
    },
    meetingsCompleted: {
        label:    "Meetings Completed",
        desc:     "Total meetings held",
        type:     "lag",
        unit:     "meetings",
        icon:     "bi-check-circle",
        color:    "#1E8449"
    },
    interestedLeads: {
        label:    "Interested Leads",
        desc:     "Leads ready for meeting",
        type:     "lag",
        unit:     "leads",
        icon:     "bi-star",
        color:    "#558B2F"
    },
    warmLeadsNurtured: {
        label:    "Warm Leads Nurtured",
        desc:     "Warm leads moved to interested/meeting",
        type:     "lag",
        unit:     "leads",
        icon:     "bi-fire",
        color:    "#F57F17"
    },
};


// ── GLOBAL STATE ──────────────────────────────────────────────────────────────
let currentKpiData = null;
let currentPeriod = 'monthly';
let customColumns = [];


// ── FETCH AND RENDER MY KPIs ──────────────────────────────────────────────────
async function fetchMyKpis(period = 'monthly') {
    currentPeriod = period;

    try {
        showKpiLoading(true);

        const response = await fetch(`/api/kpi/me?period=${period}`);
        const data = await response.json();

        if (response.ok) {
            currentKpiData = data;
            renderKpiDashboard(data);
        } else {
            showKpiError(data.error || 'Failed to load KPIs');
        }

    } catch (error) {
        showKpiError('Network error. Please refresh.');
        console.error('Error fetching KPIs:', error);

    } finally {
        showKpiLoading(false);
    }
}


// ── RENDER FULL KPI DASHBOARD ─────────────────────────────────────────────────
function renderKpiDashboard(data) {
    const container = document.getElementById('kpiDashboardContent');
    if (!container) return;

    const leadMeasures = data.leadMeasures || {};
    const lagMeasures = data.lagMeasures || {};
    const targets = data.targets || {};

    const leadHtml = buildKpiSection(
        'Lead Measures',
        'bi-activity',
        '#1565C0',
        'Activity-based KPIs — things you control directly',
        [
            'outreachCount',
            'connectionRate',
            'initialMessageCount',
            'replyRate',
            'meetingConversionRate'
        ],
        { ...leadMeasures },
        targets
    );

    const lagHtml = buildKpiSection(
        'Lag Measures',
        'bi-graph-up-arrow',
        '#1E8449',
        'Outcome-based KPIs — results from your activities',
        [
            'meetingsScheduled',
            'meetingsCompleted',
            'interestedLeads',
            'warmLeadsNurtured'
        ],
        { ...lagMeasures },
        targets
    );

    container.innerHTML = `
        <div class="row g-3">
            <div class="col-12">
                <div class="d-flex gap-2 mb-3">

                    <button class="btn btn-sm
                        ${currentPeriod === 'monthly'
                            ? 'btn-primary'
                            : 'btn-outline-primary'}"
                        onclick="fetchMyKpis('monthly')">
                        This Month
                    </button>

                    <button class="btn btn-sm
                        ${currentPeriod === 'weekly'
                            ? 'btn-primary'
                            : 'btn-outline-primary'}"
                        onclick="fetchMyKpis('weekly')">
                        This Week
                    </button>

                </div>
            </div>

            <div class="col-12">${leadHtml}</div>
            <div class="col-12">${lagHtml}</div>
        </div>`;
}


// ── BUILD KPI SECTION ─────────────────────────────────────────────────────────
function buildKpiSection(
    title,
    icon,
    color,
    subtitle,
    kpiKeys,
    values,
    targets
) {

    const cards = kpiKeys.map(key => {

        const def = KPI_DEFINITIONS[key] || {};

        const actual =
            values[key] !== undefined ? values[key] : 0;

        const target =
            targets[key] !== undefined ? targets[key] : 0;

        const pct = target > 0
            ? Math.min(Math.round((actual / target) * 100), 100)
            : 0;

        const barColor =
            pct >= 100 ? '#1E8449'
            : pct >= 70 ? '#9A7D0A'
            : '#922B21';

        const unit =
            def.unit === '%' ? '%' : ` ${def.unit || ''}`;

        const display =
            def.unit === '%'
                ? `${actual}%`
                : `${actual}${unit}`;

        const targetDisplay =
            def.unit === '%'
                ? `${target}%`
                : `${target}${unit}`;

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card border-0 shadow-sm h-100">

                    <div class="card-body">

                        <div class="d-flex align-items-center
                                    justify-content-between mb-2">

                            <div class="d-flex align-items-center gap-2">

                                <i class="bi ${def.icon || 'bi-graph-up'}"
                                   style="color:${def.color || color};
                                          font-size:1.1rem;"></i>

                                <span class="fw-semibold small">
                                    ${def.label || key}
                                </span>

                            </div>

                            <span class="badge rounded-pill"
                                  style="background:${barColor}20;
                                         color:${barColor};
                                         font-size:0.7rem;">

                                ${pct}%

                            </span>

                        </div>

                        <div class="text-muted"
                             style="font-size:0.72rem;">

                            ${def.desc || ''}

                        </div>

                        <div class="mt-2 mb-1 d-flex
                                    justify-content-between
                                    align-items-end">

                            <span class="fw-bold fs-5"
                                  style="color:${def.color || color};">

                                ${display}

                            </span>

                            <span class="text-muted small">

                                Target: ${targetDisplay}

                            </span>

                        </div>

                        <div class="progress" style="height:6px;">

                            <div class="progress-bar"
                                 style="width:${pct}%;
                                        background:${barColor};">
                            </div>

                        </div>

                    </div>
                </div>
            </div>`;
    }).join('');

    return `
        <div class="card border-0 shadow-sm">

            <div class="card-header bg-white border-bottom py-2">

                <div class="d-flex align-items-center gap-2">

                    <i class="bi ${icon}"
                       style="color:${color};
                              font-size:1.1rem;"></i>

                    <div>

                        <span class="fw-bold"
                              style="color:${color};">

                            ${title}

                        </span>

                        <span class="text-muted small ms-2">

                            ${subtitle}

                        </span>

                    </div>
                </div>
            </div>

            <div class="card-body">

                <div class="row g-2">
                    ${cards}
                </div>

            </div>
        </div>`;
}


// ── TEAM KPI COMPARISON (M1) ──────────────────────────────────────────────────
async function fetchTeamKpis(period = 'monthly') {

    const container = document.getElementById('teamKpiContent');
    if (!container) return;

    try {

        container.innerHTML = `
            <div class="text-center py-4">

                <div class="spinner-border text-primary"></div>

                <p class="mt-2 text-muted">
                    Loading team KPIs...
                </p>

            </div>`;

        const response = await fetch(`/api/kpi/team?period=${period}`);
        const data = await response.json();

        if (!response.ok) {
            container.innerHTML =
                `<p class="text-danger">${data.error}</p>`;
            return;
        }

        if (data.teamKpis.length === 0) {
            container.innerHTML =
                '<p class="text-muted text-center py-4">No team members.</p>';
            return;
        }

        const kpiKeys = [
            'outreachCount',
            'connectionRate',
            'initialMessageCount',
            'replyRate',
            'meetingConversionRate',
            'meetingsScheduled',
            'meetingsCompleted',
            'interestedLeads'
        ];

        const headerCells = kpiKeys.map(key => {
            const def = KPI_DEFINITIONS[key] || {};

            return `
                <th class="text-center small"
                    style="min-width:80px;">

                    ${def.label || key}

                </th>`;
        }).join('');

        const rows = data.teamKpis.map(member => {

            const allValues = {
                ...member.leadMeasures,
                ...member.lagMeasures
            };

            const targets = member.targets || {};

            const cells = kpiKeys.map(key => {

                const val =
                    allValues[key] !== undefined
                        ? allValues[key]
                        : 0;

                const target =
                    targets[key] !== undefined
                        ? targets[key]
                        : 1;

                const pct = target > 0
                    ? Math.min(
                        Math.round((val / target) * 100),
                        100
                    )
                    : 0;

                const color =
                    pct >= 100 ? '#1E8449'
                    : pct >= 70 ? '#9A7D0A'
                    : '#922B21';

                const def = KPI_DEFINITIONS[key] || {};

                const display =
                    def.unit === '%'
                        ? `${val}%`
                        : val;

                return `
                    <td class="text-center">

                        <div class="fw-semibold small"
                             style="color:${color};">

                            ${display}

                        </div>

                        <div class="progress mt-1"
                             style="height:3px;">

                            <div class="progress-bar"
                                 style="width:${pct}%;
                                        background:${color};">
                            </div>

                        </div>

                    </td>`;
            }).join('');

            return `
                <tr>

                    <td class="fw-semibold small">

                        <i class="bi bi-person me-1 text-muted"></i>

                        ${escapeHtml(member.employeeName || '—')}

                    </td>

                    ${cells}

                </tr>`;
        }).join('');

        container.innerHTML = `
            <div class="d-flex gap-2 mb-3">

                <button class="btn btn-sm
                    ${period === 'monthly'
                        ? 'btn-primary'
                        : 'btn-outline-primary'}"
                    onclick="fetchTeamKpis('monthly')">

                    This Month

                </button>

                <button class="btn btn-sm
                    ${period === 'weekly'
                        ? 'btn-primary'
                        : 'btn-outline-primary'}"
                    onclick="fetchTeamKpis('weekly')">

                    This Week

                </button>

            </div>

            <div class="table-responsive">

                <table class="table table-hover shadow-sm mb-0">

                    <thead class="table-light">

                        <tr>
                            <th>Employee</th>
                            ${headerCells}
                        </tr>

                    </thead>

                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>`;

    } catch (error) {

        container.innerHTML =
            '<p class="text-danger text-center">Network error.</p>';
    }
}


// ── FETCH CUSTOM KPI COLUMNS ──────────────────────────────────────────────────
async function fetchCustomKpiColumns() {

    const container = document.getElementById('customKpiContent');
    if (!container) return;

    try {

        const response = await fetch('/api/kpi/custom-columns');
        const data = await response.json();

        if (!response.ok || data.columns.length === 0) {

            container.innerHTML = `
                <p class="text-muted text-center py-3">

                    <i class="bi bi-info-circle me-2"></i>

                    No custom KPIs have been created by your manager yet.

                </p>`;

            return;
        }

        customColumns = data.columns;

        container.innerHTML = `
            <div class="row g-3">

                ${data.columns.map(col => `

                    <div class="col-md-4">

                        <div class="card border-0 shadow-sm">

                            <div class="card-body">

                                <label class="form-label fw-semibold">

                                    ${escapeHtml(col.columnName)}

                                </label>

                                <div class="text-muted small mb-2">

                                    ${escapeHtml(col.description || '')}

                                </div>

                                <div class="input-group">

                                    <input type="${
                                        col.dataType === 'text'
                                            ? 'text'
                                            : 'number'
                                    }"
                                        id="custom_${col.columnId}"
                                        class="form-control form-control-sm"
                                        placeholder="Enter value...">

                                    ${col.dataType === 'percentage'
                                        ? '<span class="input-group-text">%</span>'
                                        : ''}

                                    <button class="btn btn-sm btn-primary"
                                            onclick="submitCustomKpi(
                                                '${col.columnId}')">

                                        Save

                                    </button>

                                </div>
                            </div>
                        </div>
                    </div>

                `).join('')}

            </div>`;

    } catch (error) {

        console.error('Error fetching custom columns:', error);
    }
}


// ── M1 CUSTOM KPI COLUMN MANAGEMENT ───────────────────────────────────────────
async function fetchM1CustomKpiColumns() {

    const container = document.getElementById('m1CustomKpiColumns');
    if (!container) return;

    try {

const response = await fetch('/api/kpi/custom-columns/all');        const data = await response.json();

        if (!response.ok) {
            container.innerHTML =
                `<p class="text-danger">${data.error}</p>`;
            return;
        }

        if (data.columns.length === 0) {

            container.innerHTML = `
                <div class="text-center text-muted py-4">

                    <i class="bi bi-table fs-3"></i>

                    <p class="mt-2 mb-0">
                        No custom KPI columns created yet.
                    </p>

                </div>`;

            return;
        }

        const rows = data.columns.map(col => `

            <tr>

                <td class="fw-semibold small">
                    ${escapeHtml(col.columnName)}
                </td>

                <td class="small">
                    ${escapeHtml(col.dataType)}
                </td>

                <td class="small text-muted">
                                    ${col.description || '—'}
                                </td>
                               ${data.columns.map(col => `
                            <tr style="${!col.isActive
                                ? 'opacity:0.6; background:#fafafa;'
                                : ''}">
                                <td class="fw-semibold small">
                                    ${col.columnName}
                                    ${!col.isActive
                                        ? '<span class="badge bg-secondary ms-1" style="font-size:0.65rem;">Inactive</span>'
                                        : ''}
                                </td>
                                <td class="small text-muted">
                                    ${col.dataType}
                                </td>
                                <td>
                                    ${col.hasData
                                        ? '<span class="badge bg-success">Yes</span>'
                                        : '<span class="badge bg-secondary">No</span>'}
                                </td>
                                <td class="small text-muted">
                                    ${col.description || '—'}
                                </td>
                                <td>
                                    ${col.isActive
                                        ? `<button
                                                class="btn btn-sm btn-outline-warning py-0 px-2"
                                                onclick="deactivateKpiColumn('${col.columnId}', '${col.columnName.replace(/'/g, "\\'")}')"
                                                title="Deactivate — data preserved">
                                                <i class="bi bi-eye-slash"></i>
                                           </button>`
                                        : `<button
                                                class="btn btn-sm btn-outline-success py-0 px-2"
                                                onclick="reactivateKpiColumn('${col.columnId}', '${col.columnName.replace(/'/g, "\\'")}')"
                                                title="Reactivate">
                                                <i class="bi bi-eye"></i>
                                           </button>`
                                    }
                                </td>
                            </tr>`).join('')}
                <td>
                    <button class="btn btn-sm
                        btn-outline-warning py-0 px-2"
                        onclick="deactivateKpiColumn(
                            '${col.columnId}',
                            '${col.columnName}')"
                        title="Deactivate column">

                        <i class="bi bi-eye-slash"></i>

                    </button>
                </td>

            </tr>

        `).join('');

        container.innerHTML = `

            <div class="table-responsive">

                <table class="table table-hover align-middle">

                    <thead class="table-light">

                       <tr>
                            <th>Column Name</th>
                            <th>Type</th>
                            <th>Has Data</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>

                    </thead>

                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>
        `;

    } catch (error) {

        container.innerHTML =
            '<p class="text-danger">Network error.</p>';
    }
}


// ── SUBMIT CUSTOM KPI ENTRY ───────────────────────────────────────────────────
async function submitCustomKpi(columnId) {

    const input = document.getElementById(`custom_${columnId}`);

    if (!input) return;

    const value = input.value.trim();

    if (!value) {
        alert('Please enter a value.');
        return;
    }

    try {

        const today =
            new Date().toISOString().split('T')[0];

        const response = await fetch(
            `/api/kpi/custom-columns/${columnId}/entry`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    value,
                    entryDate: today
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            input.value = '';

            showKpiToast('KPI value saved!', 'success');

        } else {

            showKpiToast(
                data.error || 'Failed to save.',
                'danger'
            );
        }

    } catch (error) {

        showKpiToast('Network error.', 'danger');
    }
}


// ── DEACTIVATE KPI COLUMN ─────────────────────────────────────────────────────
async function deactivateKpiColumn(columnId, columnName) {

    if (!confirm(
        `Deactivate "${columnName}"?\n\n` +
        `Historical data is preserved. ` +
        `The column will be hidden from employees.`
    )) return;

    try {

        const response = await fetch(
            `/api/kpi/custom-columns/${columnId}/deactivate`,
            {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        const data = await response.json();

        if (response.ok) {

            fetchM1CustomKpiColumns();

            showKpiToast(
                'Column deactivated. Data preserved.',
                'warning'
            );

        } else {

            alert(data.error || 'Failed to deactivate.');
        }

    } catch (error) {

        alert('Network error.');
    }
}


// ── UTILITIES ─────────────────────────────────────────────────────────────────
function escapeHtml(str) {

    if (!str) return '';

    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}


function showKpiLoading(show) {

    const loading =
        document.getElementById('kpiLoading');

    const content =
        document.getElementById('kpiDashboardContent');

    if (loading)
        loading.classList.toggle('d-none', !show);

    if (content)
        content.classList.toggle('d-none', show);
}


function showKpiError(message) {

    const container =
        document.getElementById('kpiDashboardContent');

    if (container) {

        container.innerHTML = `
            <div class="alert alert-danger">

                <i class="bi bi-exclamation-triangle me-2"></i>

                ${message}

            </div>`;
    }
}


function showKpiToast(message, type='success') {

    const toast =
        document.getElementById('kpiToast');

    if (!toast) return;

    toast.querySelector('.toast-body').textContent =
        message;

    toast.className =
        `toast align-items-center text-white bg-${type} border-0`;

    new bootstrap.Toast(
        toast,
        { delay: 3000 }
    ).show();
}


// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

    if (document.getElementById('kpiDashboardContent')) {
        fetchMyKpis('monthly');
    }

    if (document.getElementById('customKpiContent')) {
        fetchCustomKpiColumns();
    }

    if (document.getElementById('m1CustomKpiColumns')) {
        fetchM1CustomKpiColumns();
    }

    // ── DEACTIVATE / REACTIVATE CUSTOM KPI COLUMN ─────────────────────────────────

async function deactivateKpiColumn(columnId, columnName) {
    const confirmed = confirm(
        `Deactivate "${columnName}"?\n\n` +
        `✅ All historical data will be preserved.\n` +
        `✅ The column will be hidden from employees.\n` +
        `✅ You can reactivate it later.\n\n` +
        `SRS Compliance: Custom KPI columns are never deleted.`
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `/api/kpi/custom-columns/${columnId}/deactivate`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
            // Refresh the column list
            fetchM1CustomKpiColumns();
            showKpiToast(
                `Column deactivated. ${
                    data.dataPreserved
                        ? data.entryCount + ' entries preserved.'
                        : 'No data was entered.'
                }`,
                'warning'
            );
        } else {
            alert(data.error || 'Failed to deactivate column.');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}


async function reactivateKpiColumn(columnId, columnName) {
    if (!confirm(`Reactivate "${columnName}"?`)) return;

    try {
        const response = await fetch(
            `/api/kpi/custom-columns/${columnId}/reactivate`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
            fetchM1CustomKpiColumns();
            showKpiToast('Column reactivated!', 'success');
        } else {
            alert(data.error || 'Failed to reactivate.');
        }
    } catch (error) {
        alert('Network error.');
    }
}
});