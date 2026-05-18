// leads.js — Lead Management JavaScript
// Handles: fetching leads, adding leads, changing stages, viewing history

// ── STAGE COLOURS ─────────────────────────────────────────────────────────────
// Each stage group gets a colour for the badge in the table

const STAGE_COLORS = {
    "stage_1_1": { bg: "#E8F5E9", text: "#2E7D32", label: "Qualified" },
    "stage_1_2": { bg: "#FFEBEE", text: "#C62828", label: "Not Qualified" },
    "stage_2":   { bg: "#E3F2FD", text: "#1565C0", label: "Request Sent" },
    "stage_2_1": { bg: "#E8EAF6", text: "#283593", label: "Connected" },
    "stage_2_2": { bg: "#FFF3E0", text: "#E65100", label: "Not Accepted" },
    "stage_3":   { bg: "#F3E5F5", text: "#6A1B9A", label: "Msg Sent" },
    "stage_3_1": { bg: "#FAFAFA", text: "#616161", label: "No Response" },
    "stage_4":   { bg: "#E0F7FA", text: "#00695C", label: "Reply Received" },
    "stage_6_1": { bg: "#F9FBE7", text: "#558B2F", label: "Interested" },
    "stage_6_2": { bg: "#FFEBEE", text: "#B71C1C", label: "Archived" },
    "stage_6_3": { bg: "#FFF8E1", text: "#F57F17", label: "Warm Lead" },
    "stage_7":   { bg: "#E8F5E9", text: "#1B5E20", label: "Mtg Scheduled" },
    "stage_8":   { bg: "#E0F2F1", text: "#004D40", label: "Mtg Completed" },
};

// ── GLOBAL STATE ──────────────────────────────────────────────────────────────
let allLeads   = [];
let allStages  = [];
let currentFilter = 'all';
let currentPage   = 1;
const PER_PAGE    = 50;
let showArchived  = false;

// ── FETCH ALL STAGES ──────────────────────────────────────────────────────────
async function fetchStages() {
    try {
        const response = await fetch('/api/stages');
        const data     = await response.json();
        if (response.ok) {
            allStages = data.stages;
            populateStageDropdowns();
        }
    } catch (error) {
        console.error('Error fetching stages:', error);
    }
}


// ── POPULATE STAGE DROPDOWNS ──────────────────────────────────────────────────
function populateStageDropdowns() {
    // Populate the Add Lead form stage dropdown (if exists)
    const addStageSelect = document.getElementById('addLeadStage');
    if (addStageSelect) {
        addStageSelect.innerHTML = '';
        allStages.forEach(stage => {
            const option    = document.createElement('option');
            option.value    = stage.stageId;
            option.textContent = `${stage.stageNumber} — ${stage.stageName}`;
            if (stage.stageId === 'stage_1_1') option.selected = true;
            addStageSelect.appendChild(option);
        });
    }
}


// ── FETCH ALL LEADS ───────────────────────────────────────────────────────────
async function fetchLeads() {
    try {
        showTableLoading(true);
        const response = await fetch('/api/leads');
        const data     = await response.json();

       if (response.ok) {
            allLeads = data.leads;

            // Update pagination controls
            updatePaginationControls(
                data.page || 1,
                data.totalPages || 1,
                data.total || data.leads.length,
                data.leads.length
            );
            // Filter archived by default
            const visibleLeads = showArchived
                ? data.leads
                : data.leads.filter(l => !l.isArchived);
            updateStatsBar(data.total, data.activeCount);
            renderLeadsTable(visibleLeads);
        } else {
            showTableError(data.error || 'Failed to load leads');
        }
    } catch (error) {
        showTableError('Network error. Please refresh the page.');
        console.error('Error fetching leads:', error);
    } finally {
        showTableLoading(false);
    }
}


// ── RENDER LEADS TABLE ────────────────────────────────────────────────────────
function renderLeadsTable(leads) {
    const tbody = document.getElementById('leadsTableBody');
    if (!tbody) return;

    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5 text-muted">
                    <i class="bi bi-funnel" style="font-size:2rem; opacity:0.3;"></i>
                    <p class="mt-2 mb-0">No leads yet. Click "Add Lead" to get started.</p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = leads.map(lead => {
        const color     = STAGE_COLORS[lead.currentStage] || { bg: "#F5F5F5", text: "#616161" };
        const stageBadge = `
            <span style="
                background-color: ${color.bg};
                color: ${color.text};
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                white-space: nowrap;
            ">${lead.stageName}</span>`;

        const linkedinBtn = lead.linkedinUrl
            ? `<a href="${lead.linkedinUrl}" target="_blank"
                  class="btn btn-sm btn-outline-primary py-0 px-2">
                   <i class="bi bi-linkedin"></i>
               </a>`
            : '';

        return `
            <tr style="cursor:pointer;"
                onclick="openLeadDetail('${lead.leadId}')">
                <td class="fw-semibold">${escapeHtml(lead.name)}</td>
                <td class="text-muted">${escapeHtml(lead.company || '—')}</td>
                <td class="text-muted small">${escapeHtml(lead.email || '—')}</td>
                <td>${stageBadge}</td>
                <td class="text-muted small">${lead.createdAt}</td>
                <td onclick="event.stopPropagation()">
                    <div class="d-flex gap-1">
                        ${linkedinBtn}
                        <button class="btn btn-sm btn-outline-primary py-0 px-2"
                                onclick="openEditLead('${lead.leadId}')"
                                title="Edit Lead">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary py-0 px-2"
                                onclick="openChangeStage(
                                    '${lead.leadId}',
                                    '${lead.currentStage}',
                                    '${escapeHtml(lead.name)}')"
                                title="Change Stage">
                            <i class="bi bi-arrow-left-right"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info py-0 px-2"
                                onclick="openHistory(
                                    '${lead.leadId}',
                                    '${escapeHtml(lead.name)}')"
                                title="View History">
                            <i class="bi bi-clock-history"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning py-0 px-2"
                                onclick="toggleArchive(
                                    '${lead.leadId}',
                                    ${!lead.isArchived})"
                                title="${lead.isArchived
                                    ? 'Unarchive' : 'Archive'}">
                            <i class="bi bi-archive"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── UPDATE STATS BAR ──────────────────────────────────────────────────────────
function updateStatsBar(total, activeCount) {
    const el = document.getElementById('statsBar');
    if (!el) return;
    el.innerHTML = `
        <div class="d-flex gap-3 flex-wrap">
            <span class="badge bg-primary fs-6 px-3 py-2">
                <i class="bi bi-people me-1"></i> Total Leads: ${total}
            </span>
            <span class="badge bg-success fs-6 px-3 py-2">
                <i class="bi bi-funnel me-1"></i> Active: ${activeCount}
            </span>
            <span class="badge bg-secondary fs-6 px-3 py-2">
                <i class="bi bi-archive me-1"></i> Archived: ${total - activeCount}
            </span>
        </div>`;
}


// ── ADD LEAD FORM SUBMIT ───────────────────────────────────────────────────────
async function submitAddLead() {
    const name        = document.getElementById('leadName').value.trim();
    const company     = document.getElementById('leadCompany').value.trim();
    const email       = document.getElementById('leadEmail').value.trim();
    const phone       = document.getElementById('leadPhone').value.trim();
    const linkedinUrl = document.getElementById('leadLinkedin').value.trim();
    const errorEl     = document.getElementById('addLeadError');

    // Validate
    if (!name) {
        errorEl.textContent = 'Lead name is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    errorEl.classList.add('d-none');

    const submitBtn = document.getElementById('submitAddLead');
    submitBtn.disabled     = true;
    submitBtn.textContent  = 'Adding...';

    try {
        const response = await fetch('/api/leads', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ name, company, email, phone, linkedinUrl })
        });

        const data = await response.json();

        if (response.ok) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('addLeadModal')
            );
            modal.hide();

            // Reset form
            document.getElementById('addLeadForm').reset();

            // Refresh leads table
            await fetchLeads();

            // Show success toast
            showToast('Lead added successfully!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to add lead.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Add Lead';
    }
}


// ── CHANGE STAGE MODAL ────────────────────────────────────────────────────────
function openChangeStage(leadId, currentStageId, leadName) {
    document.getElementById('changeStageLeadId').value   = leadId;
    document.getElementById('changeStageLeadName').textContent = leadName;

    // Populate stage select
    const select = document.getElementById('newStageSelect');
    select.innerHTML = '';
    allStages.forEach(stage => {
        const option       = document.createElement('option');
        option.value       = stage.stageId;
        option.textContent = `${stage.stageNumber} — ${stage.stageName}`;
        if (stage.stageId === currentStageId) option.selected = true;
        select.appendChild(option);
    });

    const modal = new bootstrap.Modal(document.getElementById('changeStageModal'));
    modal.show();
}


async function submitChangeStage() {
    const leadId   = document.getElementById('changeStageLeadId').value;
    const newStage = document.getElementById('newStageSelect').value;
    const notes    = document.getElementById('stageNotes').value.trim();
    const errorEl  = document.getElementById('changeStageError');

    errorEl.classList.add('d-none');

    const submitBtn = document.getElementById('submitChangeStage');
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Updating...';

    try {
        const response = await fetch(`/api/leads/${leadId}/stage`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ newStage, notes })
        });

        const data = await response.json();

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('changeStageModal')
            );
            modal.hide();
            document.getElementById('stageNotes').value = '';
            await fetchLeads();
            showToast(`Stage updated to: ${data.stageName}`, 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to update stage.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Update Stage';
    }
}


// ── HISTORY MODAL ─────────────────────────────────────────────────────────────
async function openHistory(leadId, leadName) {
    document.getElementById('historyLeadName').textContent = leadName;
    document.getElementById('historyBody').innerHTML =
        '<p class="text-muted text-center py-3">Loading history...</p>';

    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
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
                                ? `<div class="text-muted small">${escapeHtml(entry.notes)}</div>`
                                : ''}
                            <div class="text-muted small">${entry.changedAt}</div>
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


// ── SEARCH / FILTER ───────────────────────────────────────────────────────────
function filterLeads() {
    const searchTerm = document.getElementById('searchInput')
        .value.toLowerCase().trim();
    const stageFilter = document.getElementById('stageFilter').value;

    let filtered = allLeads;

    if (searchTerm) {
        filtered = filtered.filter(lead =>
            lead.name.toLowerCase().includes(searchTerm) ||
            (lead.company || '').toLowerCase().includes(searchTerm) ||
            (lead.email || '').toLowerCase().includes(searchTerm)
        );
    }

    if (stageFilter) {
        filtered = filtered.filter(lead => lead.currentStage === stageFilter);
    }

    renderLeadsTable(filtered);
}


// ── UTILITY FUNCTIONS ─────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;')
              .replace(/</g,'&lt;')
              .replace(/>/g,'&gt;')
              .replace(/"/g,'&quot;');
}

function showTableLoading(show) {
    const loading = document.getElementById('tableLoading');
    const table   = document.getElementById('leadsTable');
    if (loading) loading.classList.toggle('d-none', !show);
    if (table)   table.classList.toggle('d-none', show);
}

function showTableError(message) {
    const tbody = document.getElementById('leadsTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>${message}
                </td>
            </tr>`;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('successToast');
    if (!toast) return;
    toast.querySelector('.toast-body').textContent = message;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
}
// ── EDIT LEAD ─────────────────────────────────────────────────────────────────
function openEditLead(leadId) {
    // Find the lead from our cached data
    const lead = allLeads.find(l => l.leadId === leadId);
    if (!lead) return;

    // Fill the edit form
    document.getElementById('editLeadId').value          = leadId;
    document.getElementById('editLeadName').value        = lead.name || '';
    document.getElementById('editLeadCompany').value     = lead.company || '';
    document.getElementById('editLeadEmail').value       = lead.email || '';
    document.getElementById('editLeadPhone').value       = lead.phone || '';
    document.getElementById('editLeadLinkedin').value    = lead.linkedinUrl || '';

    // Clear error
    document.getElementById('editLeadError').classList.add('d-none');

    // Open modal
    const modal = new bootstrap.Modal(
        document.getElementById('editLeadModal')
    );
    modal.show();
}


async function submitEditLead() {
    const leadId      = document.getElementById('editLeadId').value;
    const name        = document.getElementById('editLeadName').value.trim();
    const company     = document.getElementById('editLeadCompany').value.trim();
    const email       = document.getElementById('editLeadEmail').value.trim();
    const phone       = document.getElementById('editLeadPhone').value.trim();
    const linkedinUrl = document.getElementById('editLeadLinkedin').value.trim();
    const errorEl     = document.getElementById('editLeadError');

    if (!name) {
        errorEl.textContent = 'Lead name is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    errorEl.classList.add('d-none');

    const submitBtn       = document.getElementById('submitEditLead');
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Saving...';

    try {
        const response = await fetch(`/api/leads/${leadId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ name, company, email, phone, linkedinUrl })
        });

        const data = await response.json();

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('editLeadModal')
            );
            modal.hide();
            await fetchLeads();
            showToast('Lead updated successfully!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to update lead.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Save Changes';
    }
}


// ── ARCHIVE LEAD ──────────────────────────────────────────────────────────────
async function toggleArchive(leadId, archive) {
    const action = archive ? 'archive' : 'unarchive';
    if (!confirm(`Are you sure you want to ${action} this lead?`)) return;

    try {
        const response = await fetch(`/api/leads/${leadId}/archive`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ archive })
        });

        const data = await response.json();

        if (response.ok) {
            await fetchLeads();
            showToast(
                archive ? 'Lead archived.' : 'Lead unarchived.',
                archive ? 'warning' : 'success'
            );
        } else {
            alert(data.error || 'Failed to update lead.');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}


// ── LEAD DETAIL PANEL ─────────────────────────────────────────────────────────
async function openLeadDetail(leadId) {
    const panel = document.getElementById('leadDetailPanel');
    if (!panel) return;

    panel.classList.remove('d-none');
    document.getElementById('detailContent').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary spinner-border-sm"></div>
            <p class="mt-2 text-muted small">Loading...</p>
        </div>`;

    try {
        const response = await fetch(`/api/leads/${leadId}`);
        const lead     = await response.json();

        if (!response.ok) {
            document.getElementById('detailContent').innerHTML =
                '<p class="text-danger small">Failed to load lead details.</p>';
            return;
        }

        const color = STAGE_COLORS[lead.currentStage]
                   || { bg: "#F5F5F5", text: "#616161" };

        document.getElementById('detailContent').innerHTML = `
            <div class="mb-3">
                <h6 class="fw-bold text-dark mb-1">${escapeHtml(lead.name)}</h6>
                <span style="
                    background:${color.bg};
                    color:${color.text};
                    padding:3px 10px;
                    border-radius:10px;
                    font-size:0.75rem;
                    font-weight:600;">
                    ${escapeHtml(lead.stageName)}
                </span>
            </div>

            <div class="mb-3">
                <table class="table table-sm table-borderless mb-0">
                    <tr>
                        <td class="text-muted small fw-semibold ps-0"
                            style="width:35%">Company</td>
                        <td class="small">
                            ${escapeHtml(lead.company || '—')}
                        </td>
                    </tr>
                    <tr>
                        <td class="text-muted small fw-semibold ps-0">Email</td>
                        <td class="small">
                            ${lead.email
                                ? `<a href="mailto:${escapeHtml(lead.email)}"
                                      class="text-decoration-none">
                                       ${escapeHtml(lead.email)}
                                   </a>`
                                : '—'}
                        </td>
                    </tr>
                    <tr>
                        <td class="text-muted small fw-semibold ps-0">Phone</td>
                        <td class="small">
                            ${escapeHtml(lead.phone || '—')}
                        </td>
                    </tr>
                    <tr>
                        <td class="text-muted small fw-semibold ps-0">LinkedIn</td>
                        <td class="small">
                            ${lead.linkedinUrl
                                ? `<a href="${escapeHtml(lead.linkedinUrl)}"
                                      target="_blank"
                                      class="text-decoration-none">
                                       View Profile
                                       <i class="bi bi-box-arrow-up-right ms-1"></i>
                                   </a>`
                                : '—'}
                        </td>
                    </tr>
                    <tr>
                        <td class="text-muted small fw-semibold ps-0">Status</td>
                        <td class="small">
                            ${lead.isArchived
                                ? '<span class="badge bg-secondary">Archived</span>'
                                : '<span class="badge bg-success">Active</span>'}
                        </td>
                    </tr>
                </table>
            </div>

            <div class="d-flex gap-2 flex-wrap">
                <button class="btn btn-sm btn-outline-primary"
                        onclick="openEditLead('${lead.leadId}')">
                    <i class="bi bi-pencil me-1"></i>Edit
                </button>
                <button class="btn btn-sm btn-outline-secondary"
                        onclick="openChangeStage(
                            '${lead.leadId}',
                            '${lead.currentStage}',
                            '${escapeHtml(lead.name)}')">
                    <i class="bi bi-arrow-left-right me-1"></i>Stage
                </button>
                <button class="btn btn-sm btn-outline-warning"
                        onclick="toggleArchive(
                            '${lead.leadId}',
                            ${!lead.isArchived})">
                    <i class="bi bi-archive me-1"></i>
                    ${lead.isArchived ? 'Unarchive' : 'Archive'}
                </button>
            </div>`;

    } catch (error) {
        document.getElementById('detailContent').innerHTML =
            '<p class="text-danger small">Network error.</p>';
    }
}


function closeLeadDetail() {
    const panel = document.getElementById('leadDetailPanel');
    if (panel) panel.classList.add('d-none');
}

// ── TOGGLE SHOW ARCHIVED ──────────────────────────────────────────────────────
function toggleShowArchived() {
    showArchived = !showArchived;
    const btn = document.getElementById('archiveToggleBtn');
    if (btn) {
        btn.classList.toggle('btn-outline-warning', !showArchived);
        btn.classList.toggle('btn-warning',          showArchived);
    }
    const visibleLeads = showArchived
        ? allLeads
        : allLeads.filter(l => !l.isArchived);
    renderLeadsTable(visibleLeads);
}
// ── PAGINATION ────────────────────────────────────────────────────────────────
function changePage(direction) {
    currentPage = currentPage + direction;
    if (currentPage < 1) currentPage = 1;
    fetchLeadsPage(currentPage);
}

async function fetchLeadsPage(page = 1) {
    try {
        showTableLoading(true);
        const response = await fetch(
            `/api/leads?page=${page}&per_page=${PER_PAGE}`);
        const data     = await response.json();

        if (response.ok) {
            allLeads = data.leads;
            updateStatsBar(data.total, data.activeCount);
            renderLeadsTable(
                showArchived
                    ? data.leads
                    : data.leads.filter(l => !l.isArchived)
            );
            updatePaginationControls(
                data.page, data.totalPages,
                data.total, data.leads.length
            );
        }
    } catch (error) {
        showTableError('Network error. Please refresh.');
    } finally {
        showTableLoading(false);
    }
}

function updatePaginationControls(page, totalPages,
                                   total, showing) {
    const controls  = document.getElementById('paginationControls');
    const info      = document.getElementById('paginationInfo');
    const indicator = document.getElementById('pageIndicator');
    const prevBtn   = document.getElementById('prevPageBtn');
    const nextBtn   = document.getElementById('nextPageBtn');

    if (!controls) return;

    if (total > PER_PAGE) {
        controls.classList.remove('d-none');
    } else {
        controls.classList.add('d-none');
    }

    if (info) {
        const start = ((page - 1) * PER_PAGE) + 1;
        const end   = Math.min(page * PER_PAGE, total);
        info.textContent =
            `Showing ${start}–${end} of ${total} leads`;
    }
    if (indicator) {
        indicator.textContent = `Page ${page} of ${totalPages}`;
    }
    if (prevBtn) prevBtn.disabled = page <= 1;
    if (nextBtn) nextBtn.disabled = page >= totalPages;

    currentPage = page;
}
// ── BULK IMPORT ───────────────────────────────────────────────────────────────
async function submitBulkImport() {
    const fileInput = document.getElementById('bulkImportFile');
    const errorEl   = document.getElementById('importError');
    const resultsEl = document.getElementById('importResults');
    const successEl = document.getElementById('importSuccess');
    const errorsEl  = document.getElementById('importErrors');

    errorEl.classList.add('d-none');
    resultsEl.classList.add('d-none');
    successEl.classList.add('d-none');
    errorsEl.classList.add('d-none');

    if (!fileInput.files || fileInput.files.length === 0) {
        errorEl.textContent = 'Please select a CSV file first.';
        errorEl.classList.remove('d-none');
        return;
    }

    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.csv')) {
        errorEl.textContent = 'Only CSV files are supported.';
        errorEl.classList.remove('d-none');
        return;
    }

    const btn       = document.getElementById('submitBulkImport');
    btn.disabled    = true;
    btn.innerHTML   = '<span class="spinner-border spinner-border-sm me-2">'
                    + '</span>Importing...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/leads/bulk-import', {
            method: 'POST',
            body:   formData
        });

        const data = await response.json();

        if (response.ok) {
            resultsEl.classList.remove('d-none');

            // Show success message
            successEl.classList.remove('d-none');
            document.getElementById('importSuccessMsg').textContent =
                data.message;

            // Show errors if any
            if (data.errors && data.errors.length > 0) {
                errorsEl.classList.remove('d-none');
                const errorList =
                    document.getElementById('importErrorList');
                errorList.innerHTML = data.errors
                    .map(e => `<li>${e}</li>`).join('');
            }

            // Reset file input
            fileInput.value = '';

            // Refresh leads table
            await fetchLeads();
            showToast(
                `Imported ${data.imported} leads successfully!`,
                'success'
            );
        } else {
            errorEl.textContent = data.error || 'Import failed.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        btn.disabled  = false;
        btn.innerHTML = '<i class="bi bi-upload me-1"></i>Import Leads';
    }
}
// ── INITIALISE ON PAGE LOAD ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await fetchStages();
    await fetchLeads();

    // Search input listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterLeads);
    }

    // Stage filter listener
    const stageFilter = document.getElementById('stageFilter');
    if (stageFilter) {
        stageFilter.addEventListener('change', filterLeads);
    }
});