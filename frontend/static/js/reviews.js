// reviews.js — Manager Review Tracker JavaScript
// M2 schedules and tracks review meetings with M1 Managers

let allReviews    = [];
let allM1Managers = [];


// ── FETCH M1 MANAGERS ─────────────────────────────────────────────────────────
async function fetchM1Managers() {
    try {
        const response = await fetch('/api/reviews/m1-managers');
        const data     = await response.json();
        if (response.ok) {
            allM1Managers = data.managers;
            populateM1Dropdown();
        }
    } catch (error) {
        console.error('Error fetching M1 managers:', error);
    }
}

function populateM1Dropdown() {
    const select = document.getElementById('reviewM1Manager');
    if (!select) return;
    select.innerHTML =
        '<option value="">Select M1 Manager...</option>';
    allM1Managers.forEach(m => {
        const opt       = document.createElement('option');
        opt.value       = m.uid;
        opt.textContent = m.displayName || m.email;
        select.appendChild(opt);
    });
}


// ── FETCH REVIEWS ─────────────────────────────────────────────────────────────
async function fetchReviews() {
    try {
        showReviewsLoading(true);
        const response = await fetch('/api/reviews');
        const data     = await response.json();

        if (response.ok) {
            allReviews = data.reviews;
            updateReviewStats(data);
            renderReviewsTable(data.reviews);
        } else {
            showReviewsError(data.error || 'Failed to load reviews');
        }
    } catch (error) {
        showReviewsError('Network error. Please refresh.');
    } finally {
        showReviewsLoading(false);
    }
}


// ── UPDATE REVIEW STATS ───────────────────────────────────────────────────────
function updateReviewStats(data) {
    const el = document.getElementById('reviewStatsBar');
    if (!el) return;

    el.innerHTML = `
        <div class="d-flex gap-2 flex-wrap">
            <span class="badge fs-6 px-3 py-2"
                  style="background:#E3F2FD; color:#1565C0;">
                <i class="bi bi-calendar3 me-1"></i>
                Total: ${data.total}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FEF9E7; color:#9A7D0A;">
                <i class="bi bi-hourglass me-1"></i>
                Upcoming: ${data.upcomingCount}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#EAFAF1; color:#1E8449;">
                <i class="bi bi-check-circle me-1"></i>
                Completed: ${data.completedCount}
            </span>
        </div>`;
}


// ── RENDER REVIEWS TABLE ──────────────────────────────────────────────────────
function renderReviewsTable(reviews) {
    const tbody = document.getElementById('reviewsTableBody');
    if (!tbody) return;

    if (reviews.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6"
                    class="text-center py-5 text-muted">
                    <i class="bi bi-calendar3"
                       style="font-size:2.5rem; opacity:0.25;"></i>
                    <p class="mt-2 mb-0">
                        No reviews scheduled yet.
                    </p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = reviews.map(r => {
        const statusBadge = r.isCompleted
            ? `<span class="badge"
                     style="background:#EAFAF1; color:#1E8449;">
                   ✓ Completed
               </span>`
            : r.isUpcoming
            ? `<span class="badge"
                     style="background:#E3F2FD; color:#1565C0;">
                   Upcoming
               </span>`
            : `<span class="badge"
                     style="background:#FDEDEC; color:#922B21;">
                   Overdue
               </span>`;

        const actionItemsBadge = r.actionItems?.length > 0
            ? `<span class="badge bg-secondary ms-1">
                   ${r.actionItems.length} items
               </span>`
            : '';

        return `
            <tr style="${!r.isCompleted && !r.isUpcoming
                ? 'background:#fff5f5;' : ''}">
                <td class="fw-semibold small">
                    <i class="bi bi-person-badge me-1 text-muted"></i>
                    ${escapeHtmlReview(r.m1ManagerName || '—')}
                </td>
                <td class="small ${!r.isUpcoming && !r.isCompleted
                    ? 'text-danger fw-bold' : 'text-muted'}">
                    ${r.scheduledDate}
                </td>
                <td class="small">
                    ${escapeHtmlReview(r.agenda || '—')}
                </td>
                <td class="small text-muted"
                    style="max-width:150px; overflow:hidden;
                           text-overflow:ellipsis; white-space:nowrap;">
                    ${escapeHtmlReview(r.notes || '—')}
                    ${actionItemsBadge}
                </td>
                <td>${statusBadge}</td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary
                                       py-0 px-2"
                                onclick="openEditReview('${r.reviewId}')"
                                title="Edit / Add Notes">
                            <i class="bi bi-pencil"></i>
                        </button>
                        ${!r.isCompleted ? `
                        <button class="btn btn-sm btn-outline-success
                                       py-0 px-2"
                                onclick="markReviewComplete(
                                    '${r.reviewId}')"
                                title="Mark Complete">
                            <i class="bi bi-check-lg"></i>
                        </button>` : ''}
                        <button class="btn btn-sm btn-outline-danger
                                       py-0 px-2"
                                onclick="deleteReview('${r.reviewId}')"
                                title="Delete">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── CREATE REVIEW ─────────────────────────────────────────────────────────────
async function submitScheduleReview() {
    const m1Uid   = document.getElementById('reviewM1Manager').value;
    const date    = document.getElementById('reviewDate').value;
    const agenda  = document.getElementById('reviewAgenda').value.trim();
    const errorEl = document.getElementById('reviewFormError');

    errorEl.classList.add('d-none');

    if (!m1Uid) {
        errorEl.textContent = 'Please select an M1 Manager.';
        errorEl.classList.remove('d-none');
        return;
    }
    if (!date) {
        errorEl.textContent = 'Scheduled date is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    const btn       = document.getElementById('submitScheduleReview');
    btn.disabled    = true;
    btn.textContent = 'Scheduling...';

    try {
        const response = await fetch('/api/reviews', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                m1ManagerUid:  m1Uid,
                scheduledDate: date,
                agenda:        agenda
            })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('scheduleReviewModal')
            ).hide();
            document.getElementById('scheduleReviewForm').reset();
            await fetchReviews();
            showReviewsToast('Review scheduled!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to schedule.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error.';
        errorEl.classList.remove('d-none');
    } finally {
        btn.disabled    = false;
        btn.textContent = 'Schedule Review';
    }
}


// ── EDIT REVIEW ───────────────────────────────────────────────────────────────
async function openEditReview(reviewId) {
    const review = allReviews.find(r => r.reviewId === reviewId);
    if (!review) return;

    document.getElementById('editReviewId').value      = reviewId;
    document.getElementById('editReviewAgenda').value  = review.agenda;
    document.getElementById('editReviewNotes').value   = review.notes;
    document.getElementById('editReviewDate').value    = review.scheduledIso;
    document.getElementById('editReviewActionItems').value =
        (review.actionItems || []).join('\n');
    document.getElementById('editReviewError')
        .classList.add('d-none');

    new bootstrap.Modal(
        document.getElementById('editReviewModal')
    ).show();
}


async function submitEditReview() {
    const reviewId    = document.getElementById('editReviewId').value;
    const agenda      = document.getElementById(
        'editReviewAgenda').value.trim();
    const notes       = document.getElementById(
        'editReviewNotes').value.trim();
    const date        = document.getElementById('editReviewDate').value;
    const actionRaw   = document.getElementById(
        'editReviewActionItems').value.trim();
    const actionItems = actionRaw
        ? actionRaw.split('\n').map(i => i.trim()).filter(Boolean)
        : [];
    const errorEl     = document.getElementById('editReviewError');

    errorEl.classList.add('d-none');

    const btn       = document.getElementById('submitEditReview');
    btn.disabled    = true;
    btn.textContent = 'Saving...';

    try {
        const response = await fetch(`/api/reviews/${reviewId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                agenda, notes, actionItems,
                scheduledDate: date || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById('editReviewModal')
            ).hide();
            await fetchReviews();
            showReviewsToast('Review updated!', 'success');
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


// ── MARK COMPLETE ─────────────────────────────────────────────────────────────
async function markReviewComplete(reviewId) {
    if (!confirm('Mark this review as completed?')) return;

    try {
        const response = await fetch(`/api/reviews/${reviewId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ isCompleted: true })
        });

        const data = await response.json();

        if (response.ok) {
            await fetchReviews();
            showReviewsToast('Review marked as completed!', 'success');
        } else {
            alert(data.error || 'Failed to update.');
        }
    } catch (error) {
        alert('Network error.');
    }
}


// ── DELETE REVIEW ─────────────────────────────────────────────────────────────
async function deleteReview(reviewId) {
    if (!confirm('Delete this review?')) return;

    try {
        const response = await fetch(`/api/reviews/${reviewId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (response.ok) {
            await fetchReviews();
            showReviewsToast('Review deleted.', 'warning');
        } else {
            alert(data.error || 'Failed to delete.');
        }
    } catch (error) {
        alert('Network error.');
    }
}


// ── UTILITIES ─────────────────────────────────────────────────────────────────
function escapeHtmlReview(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
              .replace(/'/g,'&#039;');
}

function showReviewsLoading(show) {
    const loading = document.getElementById('reviewsLoading');
    const wrapper = document.getElementById('reviewsTableWrapper');
    if (loading) loading.classList.toggle('d-none', !show);
    if (wrapper) wrapper.classList.toggle('d-none', show);
}

function showReviewsError(message) {
    const tbody = document.getElementById('reviewsTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </td>
            </tr>`;
    }
}

function showReviewsToast(message, type='success') {
    const toast = document.getElementById('reviewsToast');
    if (!toast) return;
    toast.querySelector('.toast-body').textContent = message;
    toast.className =
        `toast align-items-center text-white bg-${type} border-0`;
    new bootstrap.Toast(toast, { delay: 3000 }).show();
}


// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('reviewsTableBody')) {
        fetchM1Managers();
        fetchReviews();
    }
});