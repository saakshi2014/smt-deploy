// tasks.js — Task Management JavaScript
// Handles: fetch tasks, create task, update status, delete task

// ── PRIORITY COLOURS ──────────────────────────────────────────────────────────
const PRIORITY_COLORS = {
    high:   { bg: "#FDEDEC", text: "#922B21", label: "High" },
    medium: { bg: "#FEF9E7", text: "#9A7D0A", label: "Medium" },
    low:    { bg: "#EBF5FB", text: "#1A5276", label: "Low"  },
};

// ── STATUS COLOURS ────────────────────────────────────────────────────────────
const STATUS_COLORS = {
    pending:     { bg: "#EBF5FB", text: "#1A5276", label: "Pending"     },
    in_progress: { bg: "#FEF9E7", text: "#9A7D0A", label: "In Progress" },
    completed:   { bg: "#EAFAF1", text: "#1E8449", label: "Completed"   },
    overdue:     { bg: "#FDEDEC", text: "#922B21", label: "Overdue"     },
};

// ── GLOBAL STATE ──────────────────────────────────────────────────────────────
let allTasks    = [];
let allAssignees = [];


// ── FETCH ASSIGNEES ───────────────────────────────────────────────────────────
async function fetchAssignees() {
    try {
        const response = await fetch('/api/tasks/assignees');
        const data     = await response.json();
        if (response.ok) {
            allAssignees = data.assignees;
            populateAssigneeDropdown();
        }
    } catch (error) {
        console.error('Error fetching assignees:', error);
    }
}


// ── POPULATE ASSIGNEE DROPDOWN ────────────────────────────────────────────────
function populateAssigneeDropdown() {
    const select = document.getElementById('taskAssignee');
    if (!select) return;

    select.innerHTML = '<option value="">Select employee...</option>';
    allAssignees.forEach(a => {
        const option       = document.createElement('option');
        option.value       = a.uid;
        option.textContent = `${a.displayName || a.email}`;
        select.appendChild(option);
    });
}


// ── FETCH TASKS ───────────────────────────────────────────────────────────────
async function fetchTasks() {
    try {
        showTasksLoading(true);
        const response = await fetch('/api/tasks');
        const data     = await response.json();

        if (response.ok) {
            allTasks = data.tasks;
            updateTaskStatsBar(data.counts);
            renderTasksTable(data.tasks);
        } else {
            showTasksError(data.error || 'Failed to load tasks');
        }
    } catch (error) {
        showTasksError('Network error. Please refresh.');
        console.error('Error fetching tasks:', error);
    } finally {
        showTasksLoading(false);
    }
}


// ── RENDER TASKS TABLE ────────────────────────────────────────────────────────
function renderTasksTable(tasks) {
    const tbody = document.getElementById('tasksTableBody');
    if (!tbody) return;

    if (tasks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <i class="bi bi-check2-square"
                       style="font-size:2.5rem; opacity:0.25;"></i>
                    <p class="mt-2 mb-0">No tasks yet.</p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = tasks.map(task => {
        const pri    = PRIORITY_COLORS[task.priority]
                    || PRIORITY_COLORS.medium;
        const stat   = STATUS_COLORS[task.status]
                    || STATUS_COLORS.pending;

        const priBadge = `
            <span style="background:${pri.bg}; color:${pri.text};
                         padding:3px 9px; border-radius:10px;
                         font-size:0.72rem; font-weight:600;">
                ${pri.label}
            </span>`;

        const statBadge = `
            <span style="background:${stat.bg}; color:${stat.text};
                         padding:3px 9px; border-radius:10px;
                         font-size:0.72rem; font-weight:600;">
                ${stat.label}
            </span>`;

        // Status update dropdown (employee sees only their tasks)
        const statusSelect = `
            <select class="form-select form-select-sm"
                    style="min-width:130px; font-size:0.8rem;"
                    onchange="updateTaskStatus('${task.taskId}', this.value)"
                    ${task.status === 'completed' ? 'disabled' : ''}>
                <option value="pending"
                    ${task.status==='pending'     ? 'selected':''}>
                    Pending
                </option>
                <option value="in_progress"
                    ${task.status==='in_progress' ? 'selected':''}>
                    In Progress
                </option>
                <option value="completed"
                    ${task.status==='completed'   ? 'selected':''}>
                    Completed
                </option>
            </select>`;

        const isOverdue = task.status === 'overdue';

        return `
            <tr style="${isOverdue
                ? 'background:#fff5f5;' : ''}">
                <td class="fw-semibold">
                    ${escapeHtml(task.title)}
                    ${isOverdue
                        ? '<span class="badge bg-danger ms-2 small">OVERDUE</span>'
                        : ''}
                </td>
                <td class="text-muted small">
                    ${escapeHtml(task.description || '—')}
                </td>
                <td>${priBadge}</td>
                <td class="text-muted small
                    ${isOverdue ? 'text-danger fw-bold' : ''}">
                    ${task.dueDateDisplay || task.dueDate}
                </td>
                <td>
                    <span class="badge bg-light text-dark border">
                        <i class="bi bi-person me-1"></i>
                        ${escapeHtml(task.assignedToName || '—')}
                    </span>
                </td>
                <td>${statBadge}</td>
                <td onclick="event.stopPropagation()">
                    <div class="d-flex gap-1 align-items-center">
                        ${statusSelect}
                        <button class="btn btn-sm btn-outline-danger py-0 px-2"
                                onclick="deleteTask('${task.taskId}')"
                                title="Delete task"
                                style="display:${
                                    ['m1_manager','m2_manager'].includes(
                                        window.userRole) ? 'inline':'none'}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}


// ── UPDATE TASK STATUS ────────────────────────────────────────────────────────
async function updateTaskStatus(taskId, newStatus) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ status: newStatus })
        });

        const data = await response.json();

        if (response.ok) {
            await fetchTasks();
            showToast(`Task status updated to: ${newStatus.replace('_', ' ')}`,
                      'success');
        } else {
            showToast(data.error || 'Failed to update task', 'danger');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'danger');
    }
}


// ── CREATE TASK ───────────────────────────────────────────────────────────────
async function submitCreateTask() {
    const title       = document.getElementById('taskTitle').value.trim();
    const description = document.getElementById('taskDescription').value.trim();
    const assigneeUid = document.getElementById('taskAssignee').value;
    const dueDate     = document.getElementById('taskDueDate').value;
    const priority    = document.getElementById('taskPriority').value;
    const errorEl     = document.getElementById('createTaskError');

    errorEl.classList.add('d-none');

    if (!title) {
        errorEl.textContent = 'Task title is required.';
        errorEl.classList.remove('d-none');
        return;
    }
    if (!assigneeUid) {
        errorEl.textContent = 'Please select an employee to assign to.';
        errorEl.classList.remove('d-none');
        return;
    }
    if (!dueDate) {
        errorEl.textContent = 'Due date is required.';
        errorEl.classList.remove('d-none');
        return;
    }

    const submitBtn       = document.getElementById('submitCreateTask');
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Creating...';

    try {
        const response = await fetch('/api/tasks', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                title, description,
                assignedToUid: assigneeUid,
                dueDate, priority
            })
        });

        const data = await response.json();

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(
                document.getElementById('createTaskModal')
            );
            modal.hide();
            document.getElementById('createTaskForm').reset();
            await fetchTasks();
            showToast('Task created and assigned successfully!', 'success');
        } else {
            errorEl.textContent = data.error || 'Failed to create task.';
            errorEl.classList.remove('d-none');
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('d-none');
    } finally {
        submitBtn.disabled    = false;
        submitBtn.textContent = 'Create Task';
    }
}


// ── DELETE TASK ───────────────────────────────────────────────────────────────
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (response.ok) {
            await fetchTasks();
            showToast('Task deleted.', 'success');
        } else {
            showToast(data.error || 'Failed to delete task.', 'danger');
        }
    } catch (error) {
        showToast('Network error.', 'danger');
    }
}


// ── FILTER TASKS ──────────────────────────────────────────────────────────────
function filterTasks() {
    const statusFilter   = document.getElementById('taskStatusFilter').value;
    const priorityFilter = document.getElementById('taskPriorityFilter').value;
    const search         = document.getElementById('taskSearch')
                                  .value.toLowerCase().trim();

    let filtered = allTasks;

    if (statusFilter) {
        filtered = filtered.filter(t => t.status === statusFilter);
    }
    if (priorityFilter) {
        filtered = filtered.filter(t => t.priority === priorityFilter);
    }
    if (search) {
        filtered = filtered.filter(t =>
            t.title.toLowerCase().includes(search) ||
            (t.assignedToName || '').toLowerCase().includes(search) ||
            (t.description    || '').toLowerCase().includes(search)
        );
    }

    renderTasksTable(filtered);
}


// ── STATS BAR ─────────────────────────────────────────────────────────────────
function updateTaskStatsBar(counts) {
    const el = document.getElementById('taskStatsBar');
    if (!el) return;

    el.innerHTML = `
        <div class="d-flex gap-2 flex-wrap">
            <span class="badge fs-6 px-3 py-2"
                  style="background:#EBF5FB; color:#1A5276;">
                <i class="bi bi-list-task me-1"></i>
                Total: ${counts.total}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FEF9E7; color:#9A7D0A;">
                <i class="bi bi-hourglass me-1"></i>
                Pending: ${counts.pending}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#E8F4FD; color:#1A5276;">
                <i class="bi bi-arrow-repeat me-1"></i>
                In Progress: ${counts.in_progress}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#EAFAF1; color:#1E8449;">
                <i class="bi bi-check-circle me-1"></i>
                Completed: ${counts.completed}
            </span>
            <span class="badge fs-6 px-3 py-2"
                  style="background:#FDEDEC; color:#922B21;">
                <i class="bi bi-exclamation-triangle me-1"></i>
                Overdue: ${counts.overdue}
            </span>
        </div>`;
}


// ── UTILITIES ─────────────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showTasksLoading(show) {
    const loading = document.getElementById('tasksLoading');
    const table   = document.getElementById('tasksTableWrapper');
    if (loading) loading.classList.toggle('d-none', !show);
    if (table)   table.classList.toggle('d-none', show);
}

function showTasksError(message) {
    const tbody = document.getElementById('tasksTableBody');
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

function showToast(message, type='success') {
    const toast = document.getElementById('taskToast');
    if (!toast) return;
    toast.querySelector('.toast-body').textContent = message;
    toast.className =
        `toast align-items-center text-white bg-${type} border-0`;
    new bootstrap.Toast(toast, { delay: 3000 }).show();
}

// ── SET MIN DATE FOR DUE DATE INPUT ───────────────────────────────────────────
function setMinDate() {
    const dueDateInput = document.getElementById('taskDueDate');
    if (dueDateInput) {
        const today = new Date().toISOString().split('T')[0];
        dueDateInput.setAttribute('min', today);
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    setMinDate();
    await fetchAssignees();
    await fetchTasks();

    ['taskStatusFilter', 'taskPriorityFilter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', filterTasks);
    });

    const searchEl = document.getElementById('taskSearch');
    if (searchEl) searchEl.addEventListener('input', filterTasks);
});