// ── Sales & Marketing Tracker — Global JavaScript ──────────────────────────
// Day 9: Added global error handling, network detection, utility functions

console.log('✅ Sales & Marketing Tracker — JS loaded');


// ── NETWORK STATUS DETECTION ──────────────────────────────────────────────
window.addEventListener('online', () => {
    showGlobalToast('Back online!', 'success');
});

window.addEventListener('offline', () => {
    showGlobalToast(
        'You are offline. Some features may not work.',
        'warning',
        5000
    );
});


// ── GLOBAL TOAST ──────────────────────────────────────────────────────────
function showGlobalToast(message, type = 'success', duration = 3000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('globalToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id            = 'globalToastContainer';
        container.className     = 'position-fixed bottom-0 end-0 p-3';
        container.style.zIndex  = '9999';
        document.body.appendChild(container);
    }

    const toastId  = 'toast_' + Date.now();
    const bgClass  = {
        success: 'bg-success',
        danger:  'bg-danger',
        warning: 'bg-warning text-dark',
        info:    'bg-info text-dark'
    }[type] || 'bg-success';

    const toastHtml = `
        <div id="${toastId}"
             class="toast align-items-center text-white ${bgClass} border-0"
             role="alert">
            <div class="d-flex">
                <div class="toast-body fw-semibold">${message}</div>
                <button type="button"
                        class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast"></button>
            </div>
        </div>`;

    container.insertAdjacentHTML('beforeend', toastHtml);

    const toastEl = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastEl, { delay: duration });
    bsToast.show();

    // Remove from DOM after hidden
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}


// ── GLOBAL FETCH WRAPPER WITH ERROR HANDLING ──────────────────────────────
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });

        if (response.status === 401) {
            // Session expired — redirect to login
            showGlobalToast('Session expired. Redirecting to login...', 'warning');
            setTimeout(() => { window.location.href = '/login'; }, 2000);
            return null;
        }

        if (response.status === 403) {
            showGlobalToast('You do not have permission for this action.', 'danger');
            return null;
        }

        return response;

    } catch (error) {
        if (!navigator.onLine) {
            showGlobalToast('No internet connection.', 'danger');
        } else {
            showGlobalToast('Network error. Please try again.', 'danger');
        }
        console.error('API fetch error:', error);
        return null;
    }
}


// ── UTILITY: Show alert in a container ────────────────────────────────────
function showAlert(containerId, message, type = 'danger') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show
                    d-flex align-items-center" role="alert">
            <i class="bi bi-${type === 'success'
                ? 'check-circle' : 'exclamation-triangle'}-fill me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close"
                    data-bs-dismiss="alert"></button>
        </div>`;
}


// ── UTILITY: Format date ──────────────────────────────────────────────────
function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day:   '2-digit',
            month: 'short',
            year:  'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}


// ── UTILITY: Truncate text ────────────────────────────────────────────────
function truncate(str, maxLen = 30) {
    if (!str) return '—';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}


// ── UTILITY: Escape HTML ──────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;')
        .replace(/'/g,  '&#039;');
}


// ── CONFIRM DELETE HELPER ─────────────────────────────────────────────────
function confirmAction(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}


// ── SESSION CHECK ─────────────────────────────────────────────────────────
// Ping /api/auth/me every 10 minutes to keep session alive
setInterval(async () => {
    try {
        const response = await fetch('/api/auth/me');
        if (response.status === 401) {
            window.location.href = '/login';
        }
    } catch (e) {
        // Ignore network errors during ping
    }
}, 10 * 60 * 1000);
// ── NOTIFICATIONS ─────────────────────────────────────────────────────────────

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const data     = await response.json();

        if (!response.ok) return;

        const unread = data.unreadCount;
        const badge  = document.getElementById('notifBadge');

        // Update badge
        if (badge) {
            if (unread > 0) {
                badge.textContent = unread > 9 ? '9+' : unread;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }

        // Render notification list
        const list = document.getElementById('notifList');
        if (!list) return;

        if (data.notifications.length === 0) {
            list.innerHTML = `
                <div class="text-center py-4 text-muted small">
                    <i class="bi bi-bell-slash fs-4 d-block mb-2"></i>
                    No notifications yet
                </div>`;
            return;
        }

        const icons = {
            task_assigned: 'bi-clipboard-plus text-primary',
            task_completed: 'bi-check-circle text-success',
            task_overdue: 'bi-exclamation-triangle text-danger',
        };

        list.innerHTML = data.notifications.map(n => `
            <div class="dropdown-item py-2 border-bottom
                        ${n.isRead ? '' : 'bg-light'}"
                 style="white-space:normal; cursor:pointer;"
                 onclick="markRead('${n.notifId}', this)">
                <div class="d-flex align-items-start gap-2">
                    <i class="bi ${icons[n.type]
                        || 'bi-bell text-secondary'} mt-1"></i>
                    <div>
                        <div class="small ${n.isRead
                            ? 'text-muted' : 'fw-semibold text-dark'}">
                            ${n.message}
                        </div>
                        <div class="text-muted" style="font-size:0.72rem;">
                            ${n.createdAt}
                        </div>
                    </div>
                    ${!n.isRead
                        ? '<span class="ms-auto badge bg-primary rounded-pill"'
                          + ' style="font-size:0.5rem;">NEW</span>'
                        : ''}
                </div>
            </div>`).join('');

    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}


async function markRead(notifId, el) {
    try {
        await fetch(`/api/notifications/${notifId}/read`, { method: 'PUT' });
        if (el) {
            el.classList.remove('bg-light');
            const badge = el.querySelector('.badge');
            if (badge) badge.remove();
            const text = el.querySelector('.fw-semibold');
            if (text) {
                text.classList.remove('fw-semibold', 'text-dark');
                text.classList.add('text-muted');
            }
        }
        // Reload to update badge count
        await loadNotifications();
    } catch (error) {
        console.error('Error marking notification read:', error);
    }
}


async function markAllRead() {
    try {
        await fetch('/api/notifications/read-all', { method: 'PUT' });
        await loadNotifications();
    } catch (error) {
        console.error('Error marking all read:', error);
    }
}


// Auto-check notifications every 2 minutes
setInterval(async () => {
    try {
        const response = await fetch('/api/notifications');
        const data     = await response.json();
        if (response.ok) {
            const badge = document.getElementById('notifBadge');
            if (badge) {
                if (data.unreadCount > 0) {
                    badge.textContent = data.unreadCount > 9
                        ? '9+' : data.unreadCount;
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            }
        }
    } catch (e) { /* ignore */ }
}, 2 * 60 * 1000);


// Load notification count on page load
document.addEventListener('DOMContentLoaded', () => {
    // Small delay so session is established
    setTimeout(loadNotifications, 1500);
});