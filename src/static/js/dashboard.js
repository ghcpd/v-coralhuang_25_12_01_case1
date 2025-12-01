/*
Frontend JS for improved dashboard.
Provides AJAX-based fetch, Chart.js rendering, filter management, auto-refresh.
*/
const API_BASE = '/api';
let chart = null;
let autoInterval = null;
let autoRunning = false;
let debounceTimeout = null;

function getSelectedFilters() {
    const regionsEl = document.getElementById('regions');
    const productsEl = document.getElementById('products');
    const regions = Array.from(regionsEl.selectedOptions).map(o => o.value);
    const products = Array.from(productsEl.selectedOptions).map(o => o.value);
    const daterange = document.getElementById('daterange').value;
    let start_date = null, end_date = null;
    if (daterange) {
        const parts = daterange.split(' to ');
        start_date = parts[0];
        end_date = parts[1];
    }
    const group_by = document.getElementById('group_by').value;
    return { regions, products, start_date, end_date, group_by };
}

function showSpinner(show) {
    document.getElementById('spinner').classList.toggle('hidden', !show);
}

function fetchSalesData(debounce=true) {
    if (debounce) {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => fetchSalesData(false), 300);
        return;
    }
    showSpinner(true);
    const f = getSelectedFilters();
    const params = new URLSearchParams();
    if (f.regions.length > 0) f.regions.forEach(r => params.append('regions[]', r));
    if (f.products.length > 0) f.products.forEach(p => params.append('products[]', p));
    if (f.start_date) params.set('start_date', f.start_date);
    if (f.end_date) params.set('end_date', f.end_date);
    if (f.group_by) params.set('group_by', f.group_by);
    axios.get(`${API_BASE}/sales?${params.toString()}`)
        .then(resp => {
            renderComparisonChart(resp.data);
            updateRecordsTable(resp.data);
        })
        .catch(err => {
            console.error('Error fetching sales', err);
        })
        .finally(() => showSpinner(false));
}

function renderComparisonChart(data) {
    const ctx = document.getElementById('salesChart').getContext('2d');
    if (chart) {
        chart.data.labels = data.labels;
        chart.data.datasets = data.datasets.map((d, i) => ({ ...d, borderWidth: 2, fill: false }));
        chart.update();
        return;
    }
    chart = new Chart(ctx, {
        type: 'line',
        data: { labels: data.labels, datasets: data.datasets.map((d, i) => ({ ...d, borderWidth: 2, fill: false })), },
        options: {
            responsive: true,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                tooltip: { enabled: true }
            },
            onClick: (evt, items) => handleChartClick(evt, items)
        }
    });
}

function handleChartClick(evt, items) {
    if (!items || items.length === 0) return;
    const item = items[0];
    const label = chart.data.labels[item.index];
    // Drill-down: show daily details via export or table update
    const f = getSelectedFilters();
    // For simplicity, set date filter to clicked label and fetch
    document.getElementById('daterange').value = `${label} to ${label}`;
    fetchSalesData(false);
}

function updateRecordsTable(data) {
    const tbody = document.querySelector('#recordsTable tbody');
    tbody.innerHTML = '';
    // Not all endpoints return records; show sample by re-querying export endpoint? For now show top dataset rows.
    if (!data || !data.labels || data.labels.length === 0) {
        tbody.innerHTML = `<tr><td colspan=5 style="text-align:center">No data</td></tr>`;
        return;
    }
    // Create simple rows by taking the first dataset values per label
    const rows = [];
    const labels = data.labels.slice(-10);
    const ds = data.datasets && data.datasets.length > 0 ? data.datasets[0] : null;
    for (let i = 0; i < labels.length; i++) {
        const label = labels[i];
        const val = ds ? ds.data[ds.data.length - labels.length + i] : 0;
        rows.push({ date: label, region: ds ? ds.label : 'All', product: '', sales_amount: val, quantity: '' });
    }
    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.date}</td><td>${r.region}</td><td>${r.product}</td><td>$${r.sales_amount.toFixed(2)}</td><td>${r.quantity}</td>`;
        document.querySelector('#recordsTable tbody').appendChild(tr);
    });
}

function startAutoRefresh(intervalSeconds = 60) {
    if (autoRunning) return;
    autoInterval = setInterval(() => fetchSalesData(false), intervalSeconds * 1000);
    autoRunning = true;
    document.getElementById('btnToggleAuto').innerText = 'Auto: On';
}

function stopAutoRefresh() {
    if (autoInterval) clearInterval(autoInterval);
    autoInterval = null; autoRunning = false;
    document.getElementById('btnToggleAuto').innerText = 'Auto: Off';
}

function init() {
    // Populate filters from API
    axios.get(`${API_BASE}/filters`).then(resp => {
        const data = resp.data;
        const regions = document.getElementById('regions');
        const products = document.getElementById('products');
        data.regions.forEach(r => {
            const o = document.createElement('option'); o.value = r; o.text = r; regions.appendChild(o);
        });
        data.products.forEach(p => {
            const o = document.createElement('option'); o.value = p; o.text = p; products.appendChild(o);
        });
        // Init flatpickr
        flatpickr('#daterange', { mode: 'range', dateFormat: 'Y-m-d', defaultDate: [data.min_date, data.max_date] });
        // Init choices
        const choicesR = new Choices('#regions', { removeItemButton: true, maxItemCount: 5 });
        const choicesP = new Choices('#products', { removeItemButton: true, maxItemCount: 10 });
        document.getElementById('btnFetch').addEventListener('click', () => fetchSalesData());
        document.getElementById('btnExport').addEventListener('click', () => {
            const f = getSelectedFilters();
            const params = new URLSearchParams();
            if (f.regions.length > 0) f.regions.forEach(r => params.append('regions[]', r));
            if (f.products.length > 0) f.products.forEach(p => params.append('products[]', p));
            if (f.start_date) params.set('start_date', f.start_date);
            if (f.end_date) params.set('end_date', f.end_date);
            window.open(`/api/export?${params.toString()}`, '_blank');
        });
        document.getElementById('btnToggleAuto').addEventListener('click', () => {
            if (autoRunning) stopAutoRefresh(); else startAutoRefresh(60);
        });
        // Initial fetch
        fetchSalesData(false);
    });
}

document.addEventListener('DOMContentLoaded', init);

// Expose functions for tests
window.dashboard = { getSelectedFilters, fetchSalesData, renderComparisonChart, handleChartClick, startAutoRefresh, stopAutoRefresh };
