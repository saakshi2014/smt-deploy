// charts.js — Chart.js Wrapper Functions
// Handles: Bar charts, Line graphs, Funnel charts, Progress meters
// All charts are destroyed before re-creating to prevent canvas reuse errors

// ── CHART REGISTRY ────────────────────────────────────────────────────────────
// Keeps track of all active Chart.js instances so we can destroy them
// before creating new ones (prevents "canvas already in use" errors)
const activeCharts = {};

function destroyChart(chartId) {
    if (activeCharts[chartId]) {
        activeCharts[chartId].destroy();
        delete activeCharts[chartId];
    }
}


// ── COLOUR PALETTE ────────────────────────────────────────────────────────────
const CHART_COLORS = [
    '#1F4E79', '#2E75B6', '#1E8449', '#CA6F1E',
    '#6C3483', '#117A65', '#922B21', '#1A5276',
    '#7D6608', '#4A235A', '#1B4F72', '#0E6251',
];

const CHART_COLORS_TRANSPARENT = CHART_COLORS.map(c => c + '33');


// ══════════════════════════════════════════════════════════════════════════════
// BAR CHART — Team KPI Comparison
// ══════════════════════════════════════════════════════════════════════════════

/**
 * renderBarChart
 * Renders a grouped bar chart comparing multiple employees on a KPI.
 *
 * @param {string} canvasId   - ID of the <canvas> element
 * @param {Array}  labels     - X-axis labels (employee names)
 * @param {Array}  datasets   - Array of { label, data, color } objects
 * @param {string} title      - Chart title
 * @param {string} yLabel     - Y-axis label (e.g. "Count" or "%")
 */
function renderBarChart(canvasId, labels, datasets, title='', yLabel='') {
    destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    const chartDatasets = datasets.map((ds, i) => ({
        label:           ds.label,
        data:            ds.data,
        backgroundColor: ds.color
                      || CHART_COLORS_TRANSPARENT[i % CHART_COLORS.length],
        borderColor:     ds.borderColor
                      || CHART_COLORS[i % CHART_COLORS.length],
        borderWidth:     2,
        borderRadius:    4,
    }));

    activeCharts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels:   labels,
            datasets: chartDatasets,
        },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels:   { font: { size: 11 }, padding: 12 }
                },
                title: {
                    display: !!title,
                    text:    title,
                    font:    { size: 13, weight: 'bold' },
                    padding: { bottom: 10 }
                },
                tooltip: {
                    callbacks: {
                        label: ctx =>
                            ` ${ctx.dataset.label}: ${ctx.parsed.y}${
                                yLabel === '%' ? '%' : ''}`
                    }
                }
            },
            scales: {
                x: {
                    grid:  { display: false },
                    ticks: { font: { size: 11 } }
                },
                y: {
                    beginAtZero: true,
                    grid:  { color: '#F0F0F0' },
                    ticks: {
                        font:     { size: 11 },
                        callback: v => yLabel === '%' ? `${v}%` : v
                    },
                    title: {
                        display: !!yLabel && yLabel !== '%',
                        text:    yLabel,
                        font:    { size: 11 }
                    }
                }
            }
        }
    });
}


// ══════════════════════════════════════════════════════════════════════════════
// LINE GRAPH — KPI Trends Over Time
// ══════════════════════════════════════════════════════════════════════════════

/**
 * renderLineChart
 * Renders a multi-line trend chart.
 *
 * @param {string} canvasId  - ID of the <canvas> element
 * @param {Array}  labels    - X-axis labels (dates/weeks)
 * @param {Array}  datasets  - Array of { label, data, color } objects
 * @param {string} title     - Chart title
 */
function renderLineChart(canvasId, labels, datasets, title='') {
    destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    const chartDatasets = datasets.map((ds, i) => ({
        label:           ds.label,
        data:            ds.data,
        borderColor:     ds.color || CHART_COLORS[i % CHART_COLORS.length],
        backgroundColor: (ds.color || CHART_COLORS[i % CHART_COLORS.length])
                       + '15',
        borderWidth:     2.5,
        pointRadius:     4,
        pointHoverRadius: 6,
        fill:            ds.fill !== undefined ? ds.fill : true,
        tension:         0.35,
    }));

    activeCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: chartDatasets },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            interaction: {
                mode:      'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels:   { font: { size: 11 }, padding: 12 }
                },
                title: {
                    display: !!title,
                    text:    title,
                    font:    { size: 13, weight: 'bold' },
                    padding: { bottom: 10 }
                }
            },
            scales: {
                x: {
                    grid:  { color: '#F5F5F5' },
                    ticks: { font: { size: 10 } }
                },
                y: {
                    beginAtZero: true,
                    grid:        { color: '#F0F0F0' },
                    ticks:       { font: { size: 11 } }
                }
            }
        }
    });
}


// ══════════════════════════════════════════════════════════════════════════════
// DOUGHNUT CHART — Status Distribution
// ══════════════════════════════════════════════════════════════════════════════

/**
 * renderDoughnutChart
 * Renders a doughnut chart for status/category breakdown.
 *
 * @param {string} canvasId - ID of the <canvas> element
 * @param {Array}  labels   - Category labels
 * @param {Array}  values   - Numeric values
 * @param {Array}  colors   - Array of hex color strings
 * @param {string} title    - Chart title
 */
function renderDoughnutChart(canvasId, labels, values, colors, title='') {
    destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    activeCharts[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data:            values,
                backgroundColor: colors || CHART_COLORS,
                borderWidth:     2,
                borderColor:     '#FFFFFF',
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            cutout:              '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels:   { font: { size: 11 }, padding: 10 }
                },
                title: {
                    display: !!title,
                    text:    title,
                    font:    { size: 13, weight: 'bold' },
                    padding: { bottom: 8 }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const total = ctx.dataset.data
                                .reduce((a, b) => a + b, 0);
                            const pct   = total > 0
                                ? Math.round(
                                    (ctx.parsed / total) * 100) : 0;
                            return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}


// ══════════════════════════════════════════════════════════════════════════════
// FUNNEL CHART — Pipeline Conversion
// ══════════════════════════════════════════════════════════════════════════════

/**
 * renderFunnelChart
 * Renders a horizontal funnel chart using stacked bars.
 * Chart.js does not have a native funnel type so we simulate it
 * using a horizontal bar chart with calculated offsets.
 *
 * @param {string} canvasId - ID of the <canvas> element
 * @param {Array}  stages   - Array of { name, count, color } objects
 * @param {string} title    - Chart title
 */
function renderFunnelChart(canvasId, stages, title='Pipeline Funnel') {
    destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (!stages || stages.length === 0) {
        canvas.parentElement.innerHTML =
            '<p class="text-muted text-center py-4 small">No data yet.</p>';
        return;
    }

    const ctx       = canvas.getContext('2d');
    const maxCount  = Math.max(...stages.map(s => s.count), 1);

    // Each bar is centred by adding a transparent offset on the left
    const offsets   = stages.map(s => (maxCount - s.count) / 2);
    const counts    = stages.map(s => s.count);
    const labels    = stages.map(s => `${s.name} (${s.count})`);
    const colors    = stages.map((s, i) =>
        s.color || CHART_COLORS[i % CHART_COLORS.length]);

    activeCharts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    // Invisible spacer to centre the bar
                    data:            offsets,
                    backgroundColor: 'transparent',
                    borderWidth:     0,
                    barPercentage:   0.5,
                },
                {
                    label:           'Leads',
                    data:            counts,
                    backgroundColor: colors,
                    borderRadius:    4,
                    barPercentage:   0.5,
                }
            ]
        },
        options: {
            indexAxis:           'y',
            responsive:          true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: !!title,
                    text:    title,
                    font:    { size: 13, weight: 'bold' },
                    padding: { bottom: 10 }
                },
                tooltip: {
                    filter: item => item.datasetIndex === 1,
                    callbacks: {
                        label: ctx => ` Leads: ${ctx.parsed.x}`
                    }
                }
            },
            scales: {
                x: {
                    stacked:     true,
                    display:     false,
                    grid:        { display: false },
                },
                y: {
                    stacked: true,
                    ticks:   {
                        font:      { size: 11 },
                        crossAlign: 'far',
                    },
                    grid: { display: false }
                }
            }
        }
    });
}


// ══════════════════════════════════════════════════════════════════════════════
// KPI TREND DATA BUILDER
// ══════════════════════════════════════════════════════════════════════════════

/**
 * buildWeeklyLabels
 * Returns an array of the last N week labels (e.g. ["Wk 1", "Wk 2", ...])
 */
function buildWeeklyLabels(count = 6) {
    const labels = [];
    for (let i = count - 1; i >= 0; i--) {
        labels.push(`Week -${i}`);
    }
    labels[labels.length - 1] = 'This Week';
    return labels;
}


/**
 * buildMonthlyLabels
 * Returns an array of the last N month labels
 */
function buildMonthlyLabels(count = 6) {
    const months  = ['Jan','Feb','Mar','Apr','May','Jun',
                     'Jul','Aug','Sep','Oct','Nov','Dec'];
    const now     = new Date();
    const labels  = [];
    for (let i = count - 1; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        labels.push(`${months[d.getMonth()]} ${d.getFullYear()}`);
    }
    return labels;
}


// ══════════════════════════════════════════════════════════════════════════════
// PIPELINE FUNNEL DATA FETCHER
// ══════════════════════════════════════════════════════════════════════════════

/**
 * fetchAndRenderPipelineFunnel
 * Fetches stage distribution data and renders a funnel chart.
 *
 * @param {string} canvasId   - ID of the canvas element
 * @param {string} apiUrl     - API endpoint to fetch stage counts
 */
async function fetchAndRenderPipelineFunnel(canvasId, apiUrl='/api/leads') {
    try {
        const response = await fetch(apiUrl);
        const data     = await response.json();

        if (!response.ok) return;

        const leads = data.leads || [];

        // Count leads per stage
        const stageCounts = {};
        leads.forEach(lead => {
            const stage = lead.stageName || lead.currentStage;
            stageCounts[stage] = (stageCounts[stage] || 0) + 1;
        });

        // Define the funnel order
        const funnelOrder = [
            { key: 'Qualified – Pending Outreach', color: '#1F4E79' },
            { key: 'Connection Request Sent',      color: '#2E75B6' },
            { key: 'Connected on LinkedIn',         color: '#6A1B9A' },
            { key: 'Initial Message Sent',          color: '#117A65' },
            { key: 'Initial Reply Received',        color: '#00695C' },
            { key: 'Interested – Ready for Meeting',color: '#1E8449' },
            { key: 'Warm Lead – Needs Nurturing',   color: '#F57F17' },
            { key: 'Meeting Scheduled',             color: '#9A7D0A' },
            { key: 'Meeting Completed',             color: '#1B5E20' },
        ];

        const stages = funnelOrder
            .filter(f => stageCounts[f.key] > 0)
            .map(f => ({
                name:  f.key,
                count: stageCounts[f.key],
                color: f.color
            }));

        if (stages.length === 0) {
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                canvas.parentElement.innerHTML =
                    '<p class="text-muted text-center py-4 small">'
                    + 'Add some leads to see the funnel.</p>';
            }
            return;
        }

        renderFunnelChart(canvasId, stages, 'Lead Pipeline Funnel');

    } catch (error) {
        console.error('Error building funnel chart:', error);
    }
}


// ══════════════════════════════════════════════════════════════════════════════
// TEAM KPI BAR CHART BUILDER
// ══════════════════════════════════════════════════════════════════════════════

/**
 * buildTeamKpiBarChart
 * Fetches team KPI data and renders a bar chart
 * comparing all employees on a selected KPI.
 *
 * @param {string} canvasId - ID of the canvas element
 * @param {string} kpiKey   - Which KPI to chart (e.g. 'outreachCount')
 * @param {string} period   - 'monthly' or 'weekly'
 */
async function buildTeamKpiBarChart(canvasId, kpiKey, period='monthly') {
    try {
        const response = await fetch(`/api/kpi/team?period=${period}`);
        const data     = await response.json();

        if (!response.ok || !data.teamKpis) return;

        const members  = data.teamKpis;
        const labels   = members.map(m => m.employeeName || 'Employee');

        const actuals  = members.map(m => {
            const all = { ...m.leadMeasures, ...m.lagMeasures };
            return all[kpiKey] || 0;
        });

        const targets  = members.map(m => {
            return m.targets?.[kpiKey] || 0;
        });

        const kpiDef = {
            outreachCount:         { label: 'Outreach Count',    unit: '' },
            connectionRate:        { label: 'Connection Rate',   unit: '%' },
            initialMessageCount:   { label: 'Messages Sent',     unit: '' },
            replyRate:             { label: 'Reply Rate',        unit: '%' },
            meetingConversionRate: { label: 'Meeting Conv. Rate',unit: '%' },
            meetingsScheduled:     { label: 'Meetings Scheduled',unit: '' },
            meetingsCompleted:     { label: 'Meetings Completed',unit: '' },
            interestedLeads:       { label: 'Interested Leads',  unit: '' },
            warmLeadsNurtured:     { label: 'Warm Leads',        unit: '' },
        };

        const def = kpiDef[kpiKey] || { label: kpiKey, unit: '' };

        renderBarChart(
            canvasId,
            labels,
            [
                {
                    label:  'Actual',
                    data:   actuals,
                    color:  '#2E75B633',
                    borderColor: '#2E75B6'
                },
                {
                    label:  'Target',
                    data:   targets,
                    color:  '#1E844933',
                    borderColor: '#1E8449'
                }
            ],
            `${def.label} — Team Comparison`,
            def.unit
        );

    } catch (error) {
        console.error('Error building team bar chart:', error);
    }
}