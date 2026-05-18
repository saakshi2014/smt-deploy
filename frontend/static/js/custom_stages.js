// custom_stages.js — Custom Pipeline Stage Management
// Handles: list all stages, create custom stage, rename, deactivate

let allStagesManagement = [];


// ── FETCH ALL STAGES (including inactive) ─────────────────────────────────────
async function fetchAllStagesForManagement() {
    try {
        const response = await fetch('/api/custom-stages');
        const data     = await response.json();

        if (response.ok) {
            allStagesManagement = data.stages;
            renderStagesManagementTable(data.stages);
            updateStageSummary(data);
        } else {
            console.error('Failed to fetch stages:', data.error);
        }
    } catch (error) {
        console.error('Error fetching stages:', error);
    }
}


// ── UPDATE SUMMARY COUNTS ─────────────────────────────────────────────────────
function updateStageSummary(data) {
    const el = document.getElementById('stageSummary');
    if (!el) return;

    el.innerHTML = `
        <div class="d-flex gap-2 flex-wrap">
            <span class="badge fs-6 px-3 py-2"
                  style="background:#E3F2FD; color:#1565C0;">
                Total: ${data.total}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#EAFAF1; color:#1E8449;">
                Active: ${data.activeCount}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FDEDEC; color:#922B21;">
                Inactive: ${data.inactiveCount}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FEF9E7; color:#9A7D0A;">
                Custom: ${data.customCount}
            </span>
        </div>`;
}


// ── RENDER STAGES TABLE ───────────────────────────────────────────────────────
function renderStagesManagementTable(stages) {
    const tbody = document.getElementById('stagesManagementBody');
    if (!tbody) return;

    if (stages.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    No stages found.
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = stages.map((stage, idx) => {
        const isDefault   = stage.isDefault;
        const isActive    = stage.isActive;
        const rowBg       = !isActive ? 'background:#fafafa; opacity:0.7;' : '';

        const typeBadge = isDefault
            ? `<span class="badge"
                     style="background:#E3F2FD; color:#1565C0;">Default</span>`
            : `<span class="badge"
                     style="background:#FEF9E7; color:#9A7D0A;">Custom</span>`;

        const statusBadge = isActive
            ? `<span class="badge"
                     style="background:#EAFAF1; color:#1E8449;">Active</span>`
            : `<span class="badge"
                     style="background:#FDEDEC; color:#922B21;">Inactive</span>`;

        const renameBtn = !isDefault
            ? `<button class="btn btn-sm btn-outline-secondary py-0 px-2"
                       onclick="openRenameStage('${stage.stageId}',
                                '${escapeHtml(stage.stageName)}')"
                       title="Rename">
                   <i class="bi bi-pencil"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-secondary py-0 px-2
                               disabled" title="Cannot rename default stages"
                       disabled>
                   <i class="bi bi-pencil"></i>
               </button>`;

        const toggleBtn = `
            <button class="btn btn-sm py-0 px-2
                    ${isActive
                        ? 'btn-outline-danger'
                        : 'btn-outline-success'}"
                    onclick="toggleStage('${stage.stageId}', ${!isActive})"
                    title="${isActive ? 'Deactivate' : 'Activate'}">
                <i class="bi bi-${isActive
                    ? 'eye-slash' : 'eye'}"></i>
            </button>`;

        return `
            <tr style="${rowBg}">
                <td class="text-muted small">${stage.stageNumber}</td>
                <td class="fw-semibold">
                    ${escapeHtml(stage.stageName)}
                    ${!isActive
                        ? '<span class="text-muted small ms-2">'
                          + '(inactive)</span>'
                        : ''}
                </td>
                <td class="text-muted small">
                    ${escapeHtml(stage.description || '—')}
                </td>
                <td>${typeBadge}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="d-flex gap-1">
                        ${renameBtn}
                        ${toggleBtn}
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── CREATE CUSTOM STAGE ───────────────────────────────────────────────────────
async function submitCreateStage() {
    const stageName   = document.getElementById('newStageName').value.trim();
    const description = document.getElementById('newStageDesc').value.trim();
    const stageOrder  = document.getElementById('newStageOrder').value || 99;
    const errorEl     = document.getElementById('createStageError');

    errorEl.classList.add('d-none');

    if (!stageName) {
        errorEl.textContent = 'Stage name is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    const submitBtn       = document.getElementById('submitCreateStage');
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Creating...';

    try {
        const response = await fetch('/api/custom-stages', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                stageName:   stageName,
                description: description,
                stageOrder:  parseFloat(stageOrder)
            })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('createStageModal')
            ).hide();
            document.getElementById('createStageForm').reset();
            await fetchAllStagesForManagement();
            showStageToast('Custom stage created successfully!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to create stage.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Create Stage';
    }
}


// ── RENAME STAGE ──────────────────────────────────────────────────────────────
function openRenameStage(stageId, currentName) {
    document.getElementById('renameStageId').value   = stageId;
    document.getElementById('renameStageInput').value = currentName;
    document.getElementById('renameStageError').classList.add('d-none');

    new bootstrap.Modal(
        document.getElementById('renameStageModal')
    ).show();
}


async function submitRenameStage() {
    const stageId  = document.getElementById('renameStageId').value;
    const newName  = document.getElementById('renameStageInput').value.trim();
    const errorEl  = document.getElementById('renameStageError');

    errorEl.classList.add('d-none');

    if (!newName) {
        errorEl.textContent = 'Stage name cannot be empty.';
        errorEl.classList.remove('d-none');
        return;
    }

    const submitBtn       = document.getElementById('submitRenameStage');
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Saving...';

    try {
        const response = await fetch(`/api/custom-stages/${stageId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ stageName: newName })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('renameStageModal')
            ).hide();
            await fetchAllStagesForManagement();
            showStageToast('Stage renamed successfully!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to rename stage.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Save';
    }
}


// ── TOGGLE STAGE ACTIVE/INACTIVE ──────────────────────────────────────────────
async function toggleStage(stageId, makeActive) {
    const action = makeActive ? 'activate' : 'deactivate';
    if (!confirm(`Are you sure you want to ${action} this stage?`)) return;

    try {
        const response = await fetch(
            `/api/custom-stages/${stageId}/toggle`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ isActive: makeActive })
        });

        const data = await response.json();

        if (response.ok) {
            await fetchAllStagesForManagement();
            showStageToast(
                makeActive
                    ? 'Stage activated.' : 'Stage deactivated.',
                makeActive ? 'success' : 'warning'
            );
        } else {
            alert(data.error || 'Failed to update stage.');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}


// ── UTILITIES ─────────────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showStageToast(message, type='success') {
    const toast = document.getElementById('stageToast');
    if (!toast) return;
    toast.querySelector('.toast-body').textContent = message;
    toast.className =
        `toast align-items-center text-white bg-${type} border-0`;
    new bootstrap.Toast(toast, { delay: 3000 }).show();
}


// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Only load if on stages management tab
    if (document.getElementById('stagesManagementBody')) {
        fetchAllStagesForManagement();
    }
});