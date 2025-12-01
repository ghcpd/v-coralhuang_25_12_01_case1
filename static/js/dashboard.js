// Dashboard JS: AJAX and Chart.js logic

const debounce = (fn, ms) => {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), ms);
  };
};

let chart = null;
let chartConfig = null;
let autoRefreshTimer = null;

function getSelectedFilters() {
  const regionSelect = document.querySelector('#regions');
  const productSelect = document.querySelector('#products');
  const regions = Array.from(regionSelect.selectedOptions).map(o => o.value);
  const products = Array.from(productSelect.selectedOptions).map(o => o.value);
  const range = document.querySelector('#date_range').value.split(' to ');
  const groupBy = document.querySelector('#group_by').value;
  return { regions, products, start_date: range[0] || null, end_date: range[1] || null, group_by: groupBy };
}

async function fetchSalesData() {
  const f = getSelectedFilters();
  const params = new URLSearchParams();
  for (const r of f.regions) params.append('regions[]', r);
  for (const p of f.products) params.append('products[]', p);
  if (f.start_date) params.set('start_date', f.start_date);
  if (f.end_date) params.set('end_date', f.end_date);
  params.set('group_by', f.group_by || 'date');

  const url = '/api/sales?' + params.toString();
  const res = await axios.get(url);
  return res.data;
}

function renderComparisonChart(data) {
  const ctx = document.getElementById('salesChart').getContext('2d');
  if (chart) chart.destroy();
  chartConfig = {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: data.datasets.map((d, i) => ({ label: d.label || `Series ${i+1}`, data: d.data, borderWidth: 1 }))
    },
    options: {
      responsive: true,
      plugins: {
        zoom: false,
        tooltip: { mode: 'index', intersect: false }
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false }
    }
  };
  chart = new Chart(ctx, chartConfig);
  const summary = document.getElementById('summary');
  summary.innerHTML = `<strong>Total Sales:</strong> ${data.summary.total_sales} | <strong>Points:</strong> ${data.summary.count}`;
}

async function updateUI() {
  const data = await fetchSalesData();
  renderComparisonChart(data);
}

function handleChartClick(evt) {
  if (!chart) return;
  const points = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, false);
  if (!points.length) return;
  const firstPoint = points[0];
  const label = chart.data.labels[firstPoint.index];
  // Drill-down: adjust date range to label
  const [start] = label.split(' to ');
  document.querySelector('#date_range')._flatpickr.setDate([start, start]);
}

function startAutoRefresh() {
  const interval = parseInt(document.querySelector('#refresh_interval').value, 10);
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  if (interval > 0) {
    autoRefreshTimer = setInterval(updateUI, interval * 1000);
  }
}

async function init() {
  // Load filters
  const res = await axios.get('/api/filters');
  const regions = res.data.regions;
  const products = res.data.products;

  const regionSelect = document.querySelector('#regions');
  const productSelect = document.querySelector('#products');
  for (const r of regions) regionSelect.append(new Option(r, r));
  for (const p of products) productSelect.append(new Option(p, p));
  const choiceRegions = new Choices('#regions', { removeItemButton: true, shouldSort: false });
  const choiceProducts = new Choices('#products', { removeItemButton: true, shouldSort: false });

  // Initialize flatpickr
  flatpickr('#date_range', { mode: 'range', dateFormat: 'Y-m-d', onChange: debounce(updateUI, 300) });
  document.querySelector('#group_by').addEventListener('change', debounce(updateUI, 300));
  document.querySelector('#regions').addEventListener('change', debounce(updateUI, 300));
  document.querySelector('#products').addEventListener('change', debounce(updateUI, 300));
  document.querySelector('#export').addEventListener('click', () => {
    const f = getSelectedFilters();
    const params = new URLSearchParams();
    for (const r of f.regions) params.append('regions[]', r);
    for (const p of f.products) params.append('products[]', p);
    if (f.start_date) params.set('start_date', f.start_date);
    if (f.end_date) params.set('end_date', f.end_date);
    window.location.href = '/api/export?' + params.toString();
  });

  document.querySelector('#refresh_interval').addEventListener('change', startAutoRefresh);
  document.getElementById('salesChart').addEventListener('click', handleChartClick);

  // Initial update
  await updateUI();
}

if (document.readyState !== 'loading') init(); else document.addEventListener('DOMContentLoaded', init);
