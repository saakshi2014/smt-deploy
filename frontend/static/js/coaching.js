// coaching.js — Coaching Session Tracker JavaScript
// Handles: log session, list sessions, update, delete

let allCoachingSessions = [];
let coachingAssignees   = [];


// ── FETCH ASSIGNEES (reuse from tasks) ───────────────────────────────────────
async function fetchCoachingAssignees() {
    try {
        const response = await fetch('/api/tasks/assignees');
        const data     = await response.json();
        if (response.ok) {
            coachingAssignees = data.assignees;
            populateCoachingAssigneeDropdown();
        }
    } catch (error) {
        console.error('Error fetching assignees:', error);
    }
}

function populateCoachingAssigneeDropdown() {
    const select = document.getElementById('coachingSpecialist');
    if (!select) return;
    select.innerHTML =
        '<option value="">Select team member...</option>';
    coachingAssignees.forEach(a => {
        const opt       = document.createElement('option');
        opt.value       = a.uid;
        opt.textContent = a.displayName || a.email;
        select.appendChild(opt);
    });
}


// ── FETCH COACHING SESSIONS ───────────────────────────────────────────────────
async function fetchCoachingSessions() {
    try {
        showCoachingLoading(true);
        const response = await fetch('/api/coaching');
        const data     = await response.json();

        if (response.ok) {
            allCoachingSessions = data.sessions;
            updateCoachingStats(data);
            renderCoachingTable(data.sessions);
        } else {
            showCoachingError(data.error || 'Failed to load sessions');
        }
    } catch (error) {
        showCoachingError('Network error. Please refresh.');
    } finally {
        showCoachingLoading(false);
    }
}


// ── UPDATE COACHING STATS ─────────────────────────────────────────────────────
function updateCoachingStats(data) {
    const el = document.getElementById('coachingStatsBar');
    if (!el) return;

    const followUpsDue = data.followUpsDue || 0;

    el.innerHTML = `
        <div class="d-flex gap-2 flex-wrap">
            <span class="badge fs-6 px-3 py-2"
                  style="background:#E3F2FD; color:#1565C0;">
                <i class="bi bi-chat-dots me-1"></i>
                Total Sessions: ${data.total}
            </span>
            ${followUpsDue > 0 ? `
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FDEDEC; color:#922B21;">
                <i class="bi bi-alarm me-1"></i>
                Follow-ups Due: ${followUpsDue}
            </span>` : `
            <span class="badge fs-6 px-3 py-2"
                  style="background:#EAFAF1; color:#1E8449;">
                <i class="bi bi-check-circle me-1"></i>
                No Follow-ups Overdue
            </span>`}
        </div>`;
}


// ── RENDER COACHING TABLE ─────────────────────────────────────────────────────
function renderCoachingTable(sessions) {
    const tbody = document.getElementById('coachingTableBody');
    if (!tbody) return;

    if (sessions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6"
                    class="text-center py-5 text-muted">
                    <i class="bi bi-chat-dots"
                       style="font-size:2.5rem; opacity:0.25;"></i>
                    <p class="mt-2 mb-0">
                        No coaching sessions logged yet.
                    </p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = sessions.map(s => {
        const followUpBadge = s.followUpDate
            ? `<span class="badge ${s.isFollowUpDue
                ? 'bg-danger' : 'bg-light border text-dark'}"
                      style="font-size:0.7rem;">
                   <i class="bi bi-calendar me-1"></i>
                   ${s.followUpDate}
                   ${s.isFollowUpDue && !s.isCompleted
                       ? ' ⚠️' : ''}
               </span>`
            : '<span class="text-muted small">—</span>';

        const statusBadge = s.isCompleted
            ? `<span class="badge"
                     style="background:#EAFAF1; color:#1E8449;">
                   ✓ Completed
               </span>`
            : `<span class="badge"
                     style="background:#FEF9E7; color:#9A7D0A;">
                   Pending
               </span>`;

        return `
            <tr>
                <td class="fw-semibold small">
                    <i class="bi bi-person-circle me-1 text-muted"></i>
                    ${escapeHtmlCoaching(s.specialistName || '—')}
                </td>
                <td class="small text-muted">${s.sessionDate}</td>
                <td class="fw-semibold small">
                    ${escapeHtmlCoaching(s.topic)}
                </td>
                <td class="small text-muted"
                    style="max-width:200px; overflow:hidden;
                           text-overflow:ellipsis; white-space:nowrap;">
                    ${escapeHtmlCoaching(s.notes || '—')}
                </td>
                <td>${followUpBadge}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary
                                       py-0 px-2"
                                onclick="openEditSession('${s.sessionId}',
                                    '${escapeHtmlCoaching(s.topic)}',
                                    '${escapeHtmlCoaching(s.notes)}',
                                    '${s.followUpDateIso}',
                                    ${s.isCompleted})"
                                title="Edit">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger
                                       py-0 px-2"
                                onclick="deleteCoachingSession(
                                    '${s.sessionId}')"
                                title="Delete">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── CREATE COACHING SESSION ───────────────────────────────────────────────────
async function submitLogSession() {
    const specialistUid = document.getElementById(
        'coachingSpecialist').value;
    const sessionDate   = document.getElementById(
        'coachingDate').value;
    const topic         = document.getElementById(
        'coachingTopic').value.trim();
    const notes         = document.getElementById(
        'coachingNotes').value.trim();
    const followUpDate  = document.getElementById(
        'coachingFollowUp').value;
    const errorEl       = document.getElementById('coachingFormError');

    errorEl.classList.add('d-none');

    if (!specialistUid) {
        errorEl.textContent = 'Please select a team member.';
        errorEl.classList.remove('d-none');
        return;
    }
    if (!topic) {
        errorEl.textContent = 'Session topic is required.';
        errorEl.classList.remove('d-none');
        return;
    }
    if (!sessionDate) {
        errorEl.textContent = 'Session date is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    const btn       = document.getElementById('submitLogSession');
    btn.disabled    = true;
    btn.textContent = 'Logging...';

    try {
        const response = await fetch('/api/coaching', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                specialistUid, sessionDate, topic, notes,
                followUpDate: followUpDate || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('logSessionModal')
            ).hide();
            document.getElementById('logSessionForm').reset();
            await fetchCoachingSessions();
            showCoachingToast('Coaching session logged!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to log session.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Log Session';
    }
}


// ── EDIT SESSION ──────────────────────────────────────────────────────────────
function openEditSession(sessionId, topic, notes,
                         followUpDate, isCompleted) {
    document.getElementById('editSessionId').value       = sessionId;
    document.getElementById('editSessionTopic').value    = topic;
    document.getElementById('editSessionNotes').value    = notes;
    document.getElementById('editSessionFollowUp').value = followUpDate;
    document.getElementById('editSessionCompleted')
        .checked = isCompleted;
    document.getElementById('editSessionError')
        .classList.add('d-none');

    new bootstrap.Modal(
        document.getElementById('editSessionModal')
    ).show();
}


async function submitEditSession() {
    const sessionId   = document.getElementById('editSessionId').value;
    const topic       = document.getElementById(
        'editSessionTopic').value.trim();
    const notes       = document.getElementById(
        'editSessionNotes').value.trim();
    const followUpDate = document.getElementById(
        'editSessionFollowUp').value;
    const isCompleted = document.getElementById(
        'editSessionCompleted').checked;
    const errorEl     = document.getElementById('editSessionError');

    errorEl.classList.add('d-none');

    const btn       = document.getElementById('submitEditSession');
    btn.disabled    = true;
    btn.textContent = 'Saving...';

    try {
        const response = await fetch(`/api/coaching/${sessionId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                topic, notes, isCompleted,
                followUpDate: followUpDate || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('editSessionModal')
            ).hide();
            await fetchCoachingSessions();
            showCoachingToast('Session updated!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to update.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error.';
        errorEl.classList.remove('d-none');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Save Changes';
    }
}


// ── DELETE SESSION ────────────────────────────────────────────────────────────
async function deleteCoachingSession(sessionId) {
    if (!confirm('Delete this coaching session?')) return;

    try {
        const response = await fetch(`/api/coaching/${sessionId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (response.ok) {
            await fetchCoachingSessions();
            showCoachingToast('Session deleted.', 'warning');
        } else {
            alert(data.error || 'Failed to delete.');
        }
    } catch (error) {
        alert('Network error.');
    }
}


// ── FILTER SESSIONS ───────────────────────────────────────────────────────────
function filterCoachingSessions() {
    const search   = document.getElementById('coachingSearch')
                             ?.value.toLowerCase().trim() || '';
    const filtered = search
        ? allCoachingSessions.filter(s =>
            s.specialistName.toLowerCase().includes(search) ||
            s.topic.toLowerCase().includes(search))
        : allCoachingSessions;
    renderCoachingTable(filtered);
}


// ── UTILITIES ─────────────────────────────────────────────────────────────────
function escapeHtmlCoaching(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
              .replace(/'/g,'&#039;');
}

function showCoachingLoading(show) {
    const loading = document.getElementById('coachingLoading');
    const wrapper = document.getElementById('coachingTableWrapper');
    if (loading) loading.classList.toggle('d-none', !show);
    if (wrapper) wrapper.classList.toggle('d-none', show);
}

function showCoachingError(message) {
    const tbody = document.getElementById('coachingTableBody');
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

function showCoachingToast(message, type='success') {
    const toast = document.getElementById('coachingToast');
    if (!toast) return;
    toast.querySelector('.toast-body').textContent = message;
    toast.className =
        `toast align-items-center text-white bg-${type} border-0`;
    new bootstrap.Toast(toast, { delay: 3000 }).show();
}


// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('coachingTableBody')) {
        fetchCoachingAssignees();
        fetchCoachingSessions();

        const search = document.getElementById('coachingSearch');
        if (search) search.addEventListener('input', filterCoachingSessions);
    }
});