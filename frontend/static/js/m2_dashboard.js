// m2_dashboard.js — M2 Manager Organisational Dashboard
// Handles: org summary, team cards, drill-down, all leads table

// ── STAGE COLOURS ─────────────────────────────────────────────────────────────
const STAGE_COLORS = {
    "stage_1_1": { bg: "#E8F5E9", text: "#2E7D32" },
    "stage_1_2": { bg: "#FFEBEE", text: "#C62828" },
    "stage_2":   { bg: "#E3F2FD", text: "#1565C0" },
    "stage_2_1": { bg: "#E8EAF6", text: "#283593" },
    "stage_2_2": { bg: "#FFF3E0", text: "#E65100" },
    "stage_3":   { bg: "#F3E5F5", text: "#6A1B9A" },
    "stage_3_1": { bg: "#FAFAFA", text: "#616161" },
    "stage_4":   { bg: "#E0F7FA", text: "#00695C" },
    "stage_6_1": { bg: "#F9FBE7", text: "#558B2F" },
    "stage_6_2": { bg: "#FFEBEE", text: "#B71C1C" },
    "stage_6_3": { bg: "#FFF8E1", text: "#F57F17" },
    "stage_7":   { bg: "#E8F5E9", text: "#1B5E20" },
    "stage_8":   { bg: "#E0F2F1", text: "#004D40" },
};

// ── GLOBAL STATE ──────────────────────────────────────────────────────────────
let currentView    = 'org';     // 'org' or 'team'
let currentTeamId  = null;
let currentTeamName = '';
let allTeamLeads   = [];


// ── FETCH ORG SUMMARY ─────────────────────────────────────────────────────────
async function fetchOrgSummary() {
    try {
        const response = await fetch('/api/org/summary');
        const data     = await response.json();

        if (response.ok) {
            renderOrgStats(data.orgStats);
            renderTeamCards(data.teamBreakdown);
            renderOrgStageDistribution(data.stageDistribution);
        } else {
            console.error('Failed to fetch org summary:', data.error);
        }
    } catch (error) {
        console.error('Error fetching org summary:', error);
    }
}


// ── RENDER ORG STATS BAR ──────────────────────────────────────────────────────
function renderOrgStats(stats) {
    const el = document.getElementById('orgStatsBar');
    if (!el) return;

    el.innerHTML = `
        <div class="row g-2">
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-primary border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-primary">
                            ${stats.totalLeads}
                        </div>
                        <div class="small text-muted">Total Leads</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-success border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-success">
                            ${stats.activeLeads}
                        </div>
                        <div class="small text-muted">Active</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-info border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-info">
                            ${stats.interestedLeads}
                        </div>
                        <div class="small text-muted">Interested</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-warning border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-warning">
                            ${stats.meetingsScheduled}
                        </div>
                        <div class="small text-muted">Mtg Scheduled</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-success border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-success">
                            ${stats.meetingsCompleted}
                        </div>
                        <div class="small text-muted">Mtg Completed</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-secondary border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-secondary">
                            ${stats.archivedLeads}
                        </div>
                        <div class="small text-muted">Archived</div>
                    </div>
                </div>
            </div>
        </div>`;
}


// ── RENDER TEAM CARDS ─────────────────────────────────────────────────────────
function renderTeamCards(teams) {
    const el = document.getElementById('teamCardsContainer');
    if (!el) return;

    if (teams.length === 0) {
        el.innerHTML = `
            <div class="col-12">
                <p class="text-muted text-center py-4">
                    No teams found in the organisation.
                </p>
            </div>`;
        return;
    }

    el.innerHTML = teams.map(team => {
        const convRate = team.totalLeads > 0
            ? Math.round((team.meetingsCompleted / team.totalLeads) * 100)
            : 0;

        return `
            <div class="col-md-4 col-lg-3">
                <div class="card shadow-sm h-100 team-card"
                     onclick="drillDownToTeam(
                         '${team.teamId}',
                         '${escapeHtml(team.teamName)}')"
                     style="cursor:pointer; transition: transform 0.2s;"
                     onmouseover="this.style.transform='translateY(-3px)'"
                     onmouseout="this.style.transform='translateY(0)'">
                    <div class="card-header bg-primary text-white py-2">
                        <div class="fw-bold">
                            <i class="bi bi-people me-2"></i>
                            ${escapeHtml(team.teamName)}
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row g-2 text-center">
                            <div class="col-6">
                                <div class="fw-bold fs-5 text-primary">
                                    ${team.totalLeads}
                                </div>
                                <div class="small text-muted">Total</div>
                            </div>
                            <div class="col-6">
                                <div class="fw-bold fs-5 text-success">
                                    ${team.activeLeads}
                                </div>
                                <div class="small text-muted">Active</div>
                            </div>
                            <div class="col-6">
                                <div class="fw-bold fs-5 text-warning">
                                    ${team.meetingsScheduled}
                                </div>
                                <div class="small text-muted">Scheduled</div>
                            </div>
                            <div class="col-6">
                                <div class="fw-bold fs-5 text-success">
                                    ${team.meetingsCompleted}
                                </div>
                                <div class="small text-muted">Completed</div>
                            </div>
                        </div>
                        <hr class="my-2">
                        <div class="d-flex justify-content-between
                                    align-items-center">
                            <span class="small text-muted">
                                Conversion Rate
                            </span>
                            <span class="badge bg-${convRate >= 20
                                ? 'success' : convRate >= 10
                                ? 'warning' : 'danger'}">
                                ${convRate}%
                            </span>
                        </div>
                        <div class="progress mt-1" style="height:4px;">
                            <div class="progress-bar bg-success"
                                 style="width:${convRate}%"></div>
                        </div>
                    </div>
                    <div class="card-footer bg-white text-center py-1">
                        <small class="text-primary fw-semibold">
                            Click to drill down
                            <i class="bi bi-arrow-right ms-1"></i>
                        </small>
                    </div>
                </div>
            </div>`;
    }).join('');
}


// ── RENDER ORG STAGE DISTRIBUTION ─────────────────────────────────────────────
function renderOrgStageDistribution(stages) {
    const el = document.getElementById('orgStageDistribution');
    if (!el) return;

    const total = stages.reduce((sum, s) => sum + s.count, 0);

    if (stages.length === 0) {
        el.innerHTML = '<p class="text-muted small text-center py-3">No data.</p>';
        return;
    }

    // Sort by count descending
    stages.sort((a, b) => b.count - a.count);

    el.innerHTML = stages.map(stage => {
        const color = STAGE_COLORS[stage.stageId]
                   || { bg: "#F5F5F5", text: "#616161" };
        const pct   = total > 0
                    ? Math.round((stage.count / total) * 100) : 0;

        return `
            <div class="mb-2">
                <div class="d-flex justify-content-between
                            align-items-center mb-1">
                    <span class="small" style="color:${color.text}">
                        ${escapeHtml(stage.stageName)}
                    </span>
                    <span class="badge"
                          style="background:${color.bg};
                                 color:${color.text};">
                        ${stage.count}
                    </span>
                </div>
                <div class="progress" style="height:5px;">
                    <div class="progress-bar"
                         style="width:${pct}%;
                                background-color:${color.text};">
                    </div>
                </div>
            </div>`;
    }).join('');
}


// ── DRILL DOWN TO TEAM ────────────────────────────────────────────────────────
async function drillDownToTeam(teamId, teamName) {
    currentView     = 'team';
    currentTeamId   = teamId;
    currentTeamName = teamName;

    // Show team view, hide org view
    document.getElementById('orgView').classList.add('d-none');
    document.getElementById('teamView').classList.remove('d-none');

    // Update breadcrumb
    document.getElementById('teamViewTitle').textContent = teamName;

    // Show loading
    showTeamTableLoading(true);

    try {
        const response = await fetch(`/api/org/teams/${teamId}/leads`);
        const data     = await response.json();

        if (response.ok) {
            allTeamLeads = data.leads;
            renderTeamDrillTable(data.leads);
        } else {
            showTeamTableError(data.error || 'Failed to load team leads');
        }
    } catch (error) {
        showTeamTableError('Network error. Please refresh.');
    } finally {
        showTeamTableLoading(false);
    }
}


// ── BACK TO ORG VIEW ──────────────────────────────────────────────────────────
function backToOrg() {
    currentView   = 'org';
    currentTeamId = null;

    document.getElementById('teamView').classList.add('d-none');
    document.getElementById('orgView').classList.remove('d-none');
}


// ── RENDER TEAM DRILL-DOWN TABLE ──────────────────────────────────────────────
function renderTeamDrillTable(leads) {
    const tbody = document.getElementById('drillTableBody');
    if (!tbody) return;

    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <i class="bi bi-funnel"
                       style="font-size:2rem; opacity:0.3;"></i>
                    <p class="mt-2 mb-0">No leads in this team yet.</p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = leads.map(lead => {
        const color = STAGE_COLORS[lead.currentStage]
                   || { bg: "#F5F5F5", text: "#616161" };

        const stageBadge = `
            <span style="
                background-color:${color.bg};
                color:${color.text};
                padding:4px 10px;
                border-radius:12px;
                font-size:0.75rem;
                font-weight:600;">
                ${escapeHtml(lead.stageName)}
            </span>`;

        const linkedinBtn = lead.linkedinUrl
            ? `<a href="${lead.linkedinUrl}" target="_blank"
                  class="btn btn-sm btn-outline-primary py-0 px-2">
                   <i class="bi bi-linkedin"></i>
               </a>`
            : '';

        return `
            <tr>
                <td class="fw-semibold">${escapeHtml(lead.name)}</td>
                <td class="text-muted">${escapeHtml(lead.company || '—')}</td>
                <td class="text-muted small">${escapeHtml(lead.email || '—')}</td>
                <td>${stageBadge}</td>
                <td>
                    <span class="badge bg-light text-dark border">
                        <i class="bi bi-person me-1"></i>
                        ${escapeHtml(lead.employeeName || '—')}
                    </span>
                </td>
                <td class="text-muted small">${lead.createdAt}</td>
                <td>
                    <div class="d-flex gap-1">
                        ${linkedinBtn}
                        <button
                            class="btn btn-sm btn-outline-info py-0 px-2"
                            onclick="openHistory(
                                '${lead.leadId}',
                                '${escapeHtml(lead.name)}')"
                            title="View History">
                            <i class="bi bi-clock-history"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── FILTER DRILL-DOWN TABLE ───────────────────────────────────────────────────
function filterDrillTable() {
    const search = document.getElementById('drillSearch')
                           .value.toLowerCase().trim();

    const filtered = search
        ? allTeamLeads.filter(l =>
            l.name.toLowerCase().includes(search) ||
            (l.company || '').toLowerCase().includes(search) ||
            (l.employeeName || '').toLowerCase().includes(search))
        : allTeamLeads;

    renderTeamDrillTable(filtered);
}


// ── HISTORY MODAL (read-only for M2) ─────────────────────────────────────────
async function openHistory(leadId, leadName) {
    document.getElementById('historyLeadName').textContent = leadName;
    document.getElementById('historyBody').innerHTML =
        '<p class="text-muted text-center py-3">Loading history...</p>';

    const modal = new bootstrap.Modal(
        document.getElementById('historyModal')
    );
    modal.show();

    try {
        const response = await fetch(`/api/leads/${leadId}/history`);
        const data     = await response.json();

        if (response.ok && data.history.length > 0) {
            document.getElementById('historyBody').innerHTML =
                data.history.map(entry => `
                    <div class="d-flex align-items-start mb-3">
                        <div class="me-3 text-primary">
                            <i class="bi bi-arrow-right-circle-fill fs-5">
                            </i>
                        </div>
                        <div>
                            <div class="fw-semibold">
                                ${entry.fromStageName || 'Start'}
                                → ${entry.toStageName}
                            </div>
                            ${entry.notes
                                ? `<div class="text-muted small">
                                       ${escapeHtml(entry.notes)}
                                   </div>`
                                : ''}
                            <div class="text-muted small">
                                ${entry.changedAt}
                            </div>
                        </div>
                    </div>`).join('');
        } else {
            document.getElementById('historyBody').innerHTML =
                '<p class="text-muted text-center py-3">No history yet.</p>';
        }
    } catch (error) {
        document.getElementById('historyBody').innerHTML =
            '<p class="text-danger text-center py-3">Failed to load.</p>';
    }
}


// ── UTILITY FUNCTIONS ─────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;');
}

function showTeamTableLoading(show) {
    const loading = document.getElementById('drillTableLoading');
    const table   = document.getElementById('drillTable');
    if (loading) loading.classList.toggle('d-none', !show);
    if (table)   table.classList.toggle('d-none', show);
}

function showTeamTableError(message) {
    const tbody = document.getElementById('drillTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </td>
            </tr>`;
    }
}


// ── INITIALISE ON PAGE LOAD ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await fetchOrgSummary();

    // Load charts after a short delay
    setTimeout(() => {
        loadM2Charts('monthly', '', '');
    }, 800);

    // Drill search listener
    const drillSearch = document.getElementById('drillSearch');
    if (drillSearch) {
        drillSearch.addEventListener('input', filterDrillTable);
    }
});
// ── M2 TAB SWITCHER ───────────────────────────────────────────────────────────
function switchM2Tab(tab) {
    const orgView      = document.getElementById('orgView');
    const tasksContent = document.getElementById('m2TasksContent');
    const reviewsContent = document.getElementById('m2ReviewsContent');
    const orgTab       = document.getElementById('m2OrgTab');
    const tasksTab     = document.getElementById('m2TasksTab');
    const reviewsTab   = document.getElementById('m2ReviewsTab');

    // Hide all
    if (orgView)       orgView.classList.add('d-none');
    if (tasksContent)  tasksContent.classList.add('d-none');
    if (reviewsContent)reviewsContent.classList.add('d-none');

    // Remove active from all tabs
    [orgTab, tasksTab, reviewsTab].forEach(t => {
        if (t) t.classList.remove('active');
    });

    if (tab === 'org') {
        if (orgView) orgView.classList.remove('d-none');
        if (orgTab)  orgTab.classList.add('active');
    } else if (tab === 'tasks') {
        if (tasksContent) tasksContent.classList.remove('d-none');
        if (tasksTab)     tasksTab.classList.add('active');
        fetchTaskStats();
    } else if (tab === 'reviews') {
        if (reviewsContent) reviewsContent.classList.remove('d-none');
        if (reviewsTab)     reviewsTab.classList.add('active');
        fetchM1Managers();
        fetchReviews();
    }
}


// ── FETCH TASK STATS ──────────────────────────────────────────────────────────
async function fetchTaskStats() {
    try {
        const response = await fetch('/api/tasks/stats');
        const data     = await response.json();

        if (response.ok) {
            renderOrgTaskStats(data.orgCounts);
            renderTeamTaskBreakdown(data.teamCounts);
        } else {
            console.error('Failed to fetch task stats:', data.error);
        }
    } catch (error) {
        console.error('Error fetching task stats:', error);
    }
}


// ── RENDER ORG TASK STATS ─────────────────────────────────────────────────────
function renderOrgTaskStats(counts) {
    const el = document.getElementById('orgTaskStats');
    if (!el) return;

    el.innerHTML = `
        <div class="row g-2">
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-primary border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-primary">
                            ${counts.total}
                        </div>
                        <div class="small text-muted">Total Tasks</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-warning border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-warning">
                            ${counts.pending}
                        </div>
                        <div class="small text-muted">Pending</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-info border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-info">
                            ${counts.in_progress}
                        </div>
                        <div class="small text-muted">In Progress</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-success border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-success">
                            ${counts.completed}
                        </div>
                        <div class="small text-muted">Completed</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-danger border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-danger">
                            ${counts.overdue}
                        </div>
                        <div class="small text-muted">Overdue</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100
                            border-start border-secondary border-3">
                    <div class="card-body py-2">
                        <div class="fs-3 fw-bold text-secondary">
                            ${counts.total > 0
                                ? Math.round((counts.completed/counts.total)*100)
                                : 0}%
                        </div>
                        <div class="small text-muted">Completion</div>
                    </div>
                </div>
            </div>
        </div>`;
}


// ── RENDER TEAM TASK BREAKDOWN ────────────────────────────────────────────────
function renderTeamTaskBreakdown(teams) {
    const el = document.getElementById('teamTaskBreakdown');
    if (!el) return;

    if (teams.length === 0) {
        el.innerHTML =
            '<p class="text-muted text-center py-3">No task data yet.</p>';
        return;
    }

    el.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover shadow-sm">
                <thead class="table-light">
                    <tr>
                        <th>Team</th>
                        <th class="text-center">Total</th>
                        <th class="text-center">Pending</th>
                        <th class="text-center">In Progress</th>
                        <th class="text-center">Completed</th>
                        <th class="text-center">Overdue</th>
                        <th>Health</th>
                    </tr>
                </thead>
                <tbody>
                    ${teams.map(team => {
                        const completion = team.total > 0
                            ? Math.round((team.completed/team.total)*100) : 0;
                        const health = team.overdue > 0
                            ? 'danger' : completion >= 70
                            ? 'success' : 'warning';
                        return `
                            <tr>
                                <td class="fw-semibold">
                                    ${escapeHtml(team.teamName)}
                                </td>
                                <td class="text-center">${team.total}</td>
                                <td class="text-center text-warning">
                                    ${team.pending}
                                </td>
                                <td class="text-center text-info">
                                    ${team.in_progress}
                                </td>
                                <td class="text-center text-success">
                                    ${team.completed}
                                </td>
                                <td class="text-center">
                                    <span class="fw-bold
                                        ${team.overdue > 0
                                            ? 'text-danger' : 'text-muted'}">
                                        ${team.overdue}
                                    </span>
                                </td>
                                <td style="min-width:120px;">
                                    <div class="d-flex align-items-center gap-2">
                                        <div class="progress flex-grow-1"
                                             style="height:8px;">
                                            <div class="progress-bar bg-${health}"
                                                 style="width:${completion}%">
                                            </div>
                                        </div>
                                        <span class="small text-muted">
                                            ${completion}%
                                        </span>
                                    </div>
                                </td>
                            </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>`;
}
// ── DATE RANGE FILTER ─────────────────────────────────────────────────────────
let currentM2Period    = 'monthly';
let currentM2StartDate = '';
let currentM2EndDate   = '';


function applyDateFilter(period) {
    currentM2Period    = period;
    currentM2StartDate = '';
    currentM2EndDate   = '';

    // Update button styles
    ['filterMonthly', 'filterWeekly', 'filterCustom'].forEach(id => {
        const btn = document.getElementById(id);
        if (!btn) return;
        btn.className = 'btn btn-outline-primary btn-sm';
    });

    const activeId = period === 'monthly' ? 'filterMonthly' : 'filterWeekly';
    const activeBtn = document.getElementById(activeId);
    if (activeBtn) activeBtn.className = 'btn btn-primary btn-sm';

    // Hide custom date row
    const customRow = document.getElementById('customDateRow');
    if (customRow) customRow.classList.add('d-none');

    // Reload all data
    fetchOrgSummary();
    loadM2Charts(period, '', '');
}


function toggleCustomDateFilter() {
    const customRow = document.getElementById('customDateRow');
    if (!customRow) return;
    customRow.classList.toggle('d-none');

    ['filterMonthly', 'filterWeekly'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.className = 'btn btn-outline-primary btn-sm';
    });

    const btn = document.getElementById('filterCustom');
    if (btn) btn.className = 'btn btn-primary btn-sm';
}


function applyCustomDateFilter() {
    const start = document.getElementById('filterStartDate')?.value;
    const end   = document.getElementById('filterEndDate')?.value;

    if (!start || !end) {
        alert('Please select both start and end dates.');
        return;
    }
    if (start > end) {
        alert('Start date must be before end date.');
        return;
    }

    currentM2Period    = 'custom';
    currentM2StartDate = start;
    currentM2EndDate   = end;

    loadM2Charts('custom', start, end);
}


// ── LOAD ALL M2 CHARTS ────────────────────────────────────────────────────────
async function loadM2Charts(period='monthly', startDate='', endDate='') {
    await renderOrgKpiCharts(period, startDate, endDate);
    fetchAndRenderPipelineFunnel('orgFunnelChart', '/api/leads');
}


// ── ORG KPI CHARTS ────────────────────────────────────────────────────────────
async function renderOrgKpiCharts(period, startDate, endDate) {
    try {
        let url = `/api/kpi/org-summary?period=${period}`;
        if (startDate && endDate) {
            url += `&startDate=${startDate}&endDate=${endDate}`;
        }

        const response = await fetch(url);
        const data     = await response.json();

        if (!response.ok) {
            console.error('Org KPI error:', data.error);
            return;
        }

        // Lead measures bar chart
        const leadKeys   = [
            'outreachCount', 'initialMessageCount'
        ];
        const leadLabels = ['Outreach Count', 'Messages Sent'];
        const leadValues = leadKeys.map(
            k => data.orgLeadMeasures?.[k] || 0
        );

        renderBarChart(
            'orgLeadBarChart',
            leadLabels,
            [{
                label:      'Total (All Employees)',
                data:       leadValues,
                color:      '#2E75B633',
                borderColor:'#2E75B6'
            }],
            'Lead Activity — Org Total',
            ''
        );

        // Lag measures bar chart
        const lagKeys   = [
            'meetingsScheduled', 'meetingsCompleted',
            'interestedLeads', 'warmLeadsNurtured'
        ];
        const lagLabels = [
            'Mtg Scheduled', 'Mtg Completed',
            'Interested', 'Warm Leads'
        ];
        const lagValues = lagKeys.map(
            k => data.orgLagMeasures?.[k] || 0
        );

        renderBarChart(
            'orgLagBarChart',
            lagLabels,
            [{
                label:      'Total (All Employees)',
                data:       lagValues,
                color:      '#1E844933',
                borderColor:'#1E8449'
            }],
            'Pipeline Outcomes — Org Total',
            ''
        );

    } catch (error) {
        console.error('Error rendering org KPI charts:', error);
    }
}