// m1_dashboard.js — M1 Manager Dashboard JavaScript
// Handles: fetching team leads, stats, stage distribution, filters

// ── STAGE COLOURS (same as leads.js) ──────────────────────────────────────────
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
let allTeamLeads  = [];
let allStages     = [];
let allMembers    = {};


// ── FETCH STAGES ──────────────────────────────────────────────────────────────
async function fetchStages() {
    try {
        const response = await fetch('/api/stages');
        const data     = await response.json();
        if (response.ok) {
            allStages = data.stages;
            populateStageFilter();
        }
    } catch (error) {
        console.error('Error fetching stages:', error);
    }
}


// ── POPULATE STAGE FILTER DROPDOWN ───────────────────────────────────────────
function populateStageFilter() {
    const stageFilter = document.getElementById('stageFilter');
    if (!stageFilter) return;
    allStages.forEach(stage => {
        const option       = document.createElement('option');
        option.value       = stage.stageId;
        option.textContent = `${stage.stageNumber} — ${stage.stageName}`;
        stageFilter.appendChild(option);
    });
}


// ── FETCH TEAM LEADS ──────────────────────────────────────────────────────────
async function fetchTeamLeads() {
    try {
        showTableLoading(true);
        const response = await fetch('/api/leads');
        const data     = await response.json();

        if (response.ok) {
            allTeamLeads = data.leads;
            updateTeamStatsBar(data.total, data.activeCount);
            renderStageDistribution(data.leads);
            renderTeamTable(data.leads);
            buildMemberFilter(data.leads);
        } else {
            showTableError(data.error || 'Failed to load team leads');
        }
    } catch (error) {
        showTableError('Network error. Please refresh the page.');
        console.error('Error fetching team leads:', error);
    } finally {
        showTableLoading(false);
    }
}


// ── FETCH USER DISPLAY NAMES ──────────────────────────────────────────────────
async function fetchMemberNames() {
    try {
        const response = await fetch('/api/team/members');
        const data     = await response.json();
        if (response.ok) {
            data.members.forEach(m => {
                allMembers[m.uid] = m.displayName || m.email;
            });
        }
    } catch (error) {
        console.error('Error fetching members:', error);
    }
}


// ── RENDER TEAM LEADS TABLE ───────────────────────────────────────────────────
function renderTeamTable(leads) {
    const tbody = document.getElementById('teamLeadsTableBody');
    if (!tbody) return;

    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <i class="bi bi-people"
                       style="font-size:2rem; opacity:0.3;"></i>
                    <p class="mt-2 mb-0">
                        No leads in your team yet.
                    </p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = leads.map(lead => {
        const color = STAGE_COLORS[lead.currentStage]
                   || { bg: "#F5F5F5", text: "#616161" };

        const stageBadge = `
            <span style="
                background-color: ${color.bg};
                color: ${color.text};
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                white-space: nowrap;">
                ${escapeHtml(lead.stageName)}
            </span>`;

        const memberName = allMembers[lead.employeeUid]
                        || lead.employeeUid.substring(0, 8) + '...';

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
                        ${escapeHtml(memberName)}
                    </span>
                </td>
                <td class="text-muted small">${lead.createdAt}</td>
                <td>
                    <div class="d-flex gap-1">
                        ${linkedinBtn}
                        <button class="btn btn-sm btn-outline-info py-0 px-2"
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


// ── UPDATE TEAM STATS BAR ─────────────────────────────────────────────────────
function updateTeamStatsBar(total, activeCount) {
    const el = document.getElementById('teamStatsBar');
    if (!el) return;

    const archived    = total - activeCount;
    const meetingsDone = allTeamLeads.filter(
        l => l.currentStage === 'stage_8'
    ).length;
    const meetingsSched = allTeamLeads.filter(
        l => l.currentStage === 'stage_7'
    ).length;
    const interested = allTeamLeads.filter(
        l => l.currentStage === 'stage_6_1'
    ).length;

    el.innerHTML = `
        <div class="row g-2">
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-primary">${total}</div>
                        <div class="small text-muted">Total Leads</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-success">${activeCount}</div>
                        <div class="small text-muted">Active</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-info">${interested}</div>
                        <div class="small text-muted">Interested</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-warning">${meetingsSched}</div>
                        <div class="small text-muted">Mtg Scheduled</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-success">${meetingsDone}</div>
                        <div class="small text-muted">Mtg Completed</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-2">
                <div class="card text-center border-0 shadow-sm h-100">
                    <div class="card-body py-2">
                        <div class="fs-4 fw-bold text-secondary">${archived}</div>
                        <div class="small text-muted">Archived</div>
                    </div>
                </div>
            </div>
        </div>`;
}


// ── STAGE DISTRIBUTION PANEL ──────────────────────────────────────────────────
function renderStageDistribution(leads) {
    const el = document.getElementById('stageDistribution');
    if (!el) return;

    // Count leads per stage
    const stageCounts = {};
    leads.forEach(lead => {
        const sid = lead.currentStage;
        stageCounts[sid] = (stageCounts[sid] || 0) + 1;
    });

    if (Object.keys(stageCounts).length === 0) {
        el.innerHTML = '<p class="text-muted small text-center py-3">No data yet.</p>';
        return;
    }

    // Sort by stage order
    const sorted = allStages.filter(s => stageCounts[s.stageId]);

    el.innerHTML = sorted.map(stage => {
        const count = stageCounts[stage.stageId] || 0;
        const color = STAGE_COLORS[stage.stageId]
                   || { bg: "#F5F5F5", text: "#616161" };
        const pct   = leads.length > 0
                    ? Math.round((count / leads.length) * 100)
                    : 0;

        return `
            <div class="mb-2">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="small fw-semibold" style="color:${color.text}">
                        ${stage.stageNumber} — ${stage.stageName}
                    </span>
                    <span class="badge"
                          style="background:${color.bg}; color:${color.text}">
                        ${count}
                    </span>
                </div>
                <div class="progress" style="height:6px;">
                    <div class="progress-bar"
                         style="width:${pct}%;
                                background-color:${color.text};">
                    </div>
                </div>
            </div>`;
    }).join('');
}


// ── BUILD MEMBER FILTER DROPDOWN ──────────────────────────────────────────────
function buildMemberFilter(leads) {
    const select = document.getElementById('memberFilter');
    if (!select) return;

    // Get unique employee UIDs
    const uids = [...new Set(leads.map(l => l.employeeUid))];

    // Clear existing options except the first
    while (select.options.length > 1) select.remove(1);

    uids.forEach(uid => {
        const option       = document.createElement('option');
        option.value       = uid;
        option.textContent = allMembers[uid] || uid.substring(0, 8) + '...';
        select.appendChild(option);
    });
}


// ── FILTER TEAM LEADS ─────────────────────────────────────────────────────────
function filterTeamLeads() {
    const searchTerm   = document.getElementById('searchInput')
                               .value.toLowerCase().trim();
    const stageFilter  = document.getElementById('stageFilter').value;
    const memberFilter = document.getElementById('memberFilter').value;

    let filtered = allTeamLeads;

    if (searchTerm) {
        filtered = filtered.filter(lead =>
            lead.name.toLowerCase().includes(searchTerm) ||
            (lead.company || '').toLowerCase().includes(searchTerm) ||
            (lead.email   || '').toLowerCase().includes(searchTerm)
        );
    }

    if (stageFilter) {
        filtered = filtered.filter(l => l.currentStage === stageFilter);
    }

    if (memberFilter) {
        filtered = filtered.filter(l => l.employeeUid === memberFilter);
    }

    renderTeamTable(filtered);
}


// ── HISTORY MODAL (read-only for M1) ─────────────────────────────────────────
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
                            <i class="bi bi-arrow-right-circle-fill fs-5"></i>
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
            '<p class="text-danger text-center py-3">Failed to load history.</p>';
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

function showTableLoading(show) {
    const loading = document.getElementById('tableLoading');
    const table   = document.getElementById('teamLeadsTable');
    if (loading) loading.classList.toggle('d-none', !show);
    if (table)   table.classList.toggle('d-none', show);
}

function showTableError(message) {
    const tbody = document.getElementById('teamLeadsTableBody');
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
    await fetchMemberNames();
    await fetchStages();
    await fetchTeamLeads();

    // Search listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterTeamLeads);
    }

    // Stage filter listener
    const stageFilter = document.getElementById('stageFilter');
    if (stageFilter) {
        stageFilter.addEventListener('change', filterTeamLeads);
    }

    // Member filter listener
    const memberFilter = document.getElementById('memberFilter');
    if (memberFilter) {
        memberFilter.addEventListener('change', filterTeamLeads);
    }
});