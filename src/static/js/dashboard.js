// Dashboard front-end logic
let salesChart = null;
let debounceTimeout = null;
let autoRefreshTimer = null;

function getSelectedFilters() {
    const choicesRegions = document.querySelector('#regions');
    const choicesProducts = document.querySelector('#products');
    const startDate = document.querySelector('#start_date').value;
    const endDate = document.querySelector('#end_date').value;
    const regions = Array.from(choicesRegions.selectedOptions).map(o => o.value);
    const products = Array.from(choicesProducts.selectedOptions).map(o => o.value);
    return {regions, products, startDate, endDate};
}

function fetchSalesData() {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(async () => {
        const s = getSelectedFilters();
        const params = {};
        if (s.regions.length) params['regions'] = s.regions.join(',');
        if (s.products.length) params['products'] = s.products.join(',');
        if (s.startDate) params['start_date'] = s.startDate;
        if (s.endDate) params['end_date'] = s.endDate;
        try {
            const r = await axios.get(API_SALES, {params});
            renderComparisonChart(r.data);
        } catch (err) {
            console.error('Failed to fetch sales data', err);
        }
    }, 300);
}

function renderComparisonChart(data) {
    const ctx = document.getElementById('salesChart').getContext('2d');
    if (!data || !data.labels) {
        document.getElementById('summary').innerText = 'No data available';
        if (salesChart) salesChart.destroy();
        return;
    }
    const config = {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: data.datasets.map(ds => ({
                label: ds.label,
                data: ds.data,
                fill: true,
                tension: 0.2,
                backgroundColor: ds.backgroundColor,
                borderColor: ds.borderColor
            }))
        },
        options: {
            plugins: {
                tooltip: {enabled: true}
            },
            responsive: true,
            interaction: {mode: 'nearest', intersect: false}
        }
    };
    if (salesChart) salesChart.destroy();
    salesChart = new Chart(ctx, config);
    // update summary
    const summaryEl = document.getElementById('summary');
    summaryEl.innerText = `Total Sales: $${data.summary.total_sales.toFixed(2)} · Total Qty: ${data.summary.total_quantity}`;
}

function handleChartClick() {
    document.getElementById('salesChart').addEventListener('click', function(evt) {
        if (!salesChart) return;
        const p = salesChart.getElementsAtEventForMode(evt, 'nearest', {intersect: true}, true);
        if (p.length) {
            const idx = p[0].index;
            const label = salesChart.data.labels[idx];
            alert('Clicked date: ' + label + '\n(Implement drilldown in future version)');
        }
    });
}

function startAutoRefresh(intervalMs = 60000) {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    autoRefreshTimer = setInterval(fetchSalesData, intervalMs);
}

// Initialize choices and flatpickr
async function init() {
    const regionsSel = document.getElementById('regions');
    const productsSel = document.getElementById('products');
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    try {
        const r = await axios.get(API_FILTERS);
        const data = r.data;
        data.regions.forEach(x => {
            const o = document.createElement('option'); o.value = x; o.text = x; regionsSel.appendChild(o);
        });
        data.products.forEach(x => {
            const o = document.createElement('option'); o.value = x; o.text = x; productsSel.appendChild(o);
        });
        // init date pickers
        flatpickr(startInput, {dateFormat: 'Y-m-d', defaultDate: data.min_date});
        flatpickr(endInput, {dateFormat: 'Y-m-d', defaultDate: data.max_date});
    } catch (err) {
        console.error('Failed to initialize filter options', err);
    }

    regionsSel.addEventListener('change', fetchSalesData);
    productsSel.addEventListener('change', fetchSalesData);
    startInput.addEventListener('change', fetchSalesData);
    endInput.addEventListener('change', fetchSalesData);

    handleChartClick();
    fetchSalesData();
    startAutoRefresh(60000);

    document.getElementById('exportBtn').addEventListener('click', async () => {
        const s = getSelectedFilters();
        const params = new URLSearchParams();
        if (s.regions.length) params.append('regions', s.regions.join(','));
        if (s.products.length) params.append('products', s.products.join(','));
        if (s.startDate) params.append('start_date', s.startDate);
        if (s.endDate) params.append('end_date', s.endDate);
        window.open(API_EXPORT + '?' + params.toString(), '_blank');
    });
}

document.addEventListener('DOMContentLoaded', init);
