(function () {
  let chartInstance = null;
  let choicesRegion, choicesProduct, datePicker;
  let autoRefreshTimer = null;
  let debounceTimer = null;

  const chartLoadingEl = document.getElementById('chart-loading');
  const summaryEls = {
    total_sales: document.getElementById('summary-total-sales'),
    total_quantity: document.getElementById('summary-total-qty'),
    total_records: document.getElementById('summary-records'),
    avg_order_value: document.getElementById('summary-aov'),
  };

  function debounce(fn, delay = 300) {
    return function (...args) {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function paramsSerializer(params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((v) => usp.append(`${key}[]`, v));
      } else if (value !== undefined && value !== null && value !== '') {
        usp.append(key, value);
      }
    });
    return usp.toString();
  }

  function getSelectedFilters() {
    const regions = choicesRegion ? choicesRegion.getValue(true) : [];
    const products = choicesProduct ? choicesProduct.getValue(true) : [];
    const groupBy = document.getElementById('group-by').value;
    const autoRefresh = document.getElementById('auto-refresh').value;
    const dateRange = datePicker ? datePicker.selectedDates : [];

    let start_date = null;
    let end_date = null;
    if (dateRange.length === 2) {
      start_date = dayjs(dateRange[0]).format('YYYY-MM-DD');
      end_date = dayjs(dateRange[1]).format('YYYY-MM-DD');
    }

    return { regions, products, group_by: groupBy, start_date, end_date, auto_refresh: autoRefresh };
  }

  function updateSummary(summary = {}) {
    summaryEls.total_sales.textContent = summary.total_sales !== undefined ? `$${summary.total_sales.toLocaleString()}` : '-';
    summaryEls.total_quantity.textContent = summary.total_quantity !== undefined ? summary.total_quantity.toLocaleString() : '-';
    summaryEls.total_records.textContent = summary.total_records !== undefined ? summary.total_records.toLocaleString() : '-';
    summaryEls.avg_order_value.textContent = summary.avg_order_value !== undefined ? `$${summary.avg_order_value.toLocaleString()}` : '-';
  }

  function updateTable(preview = []) {
    const tbody = document.querySelector('#data-table tbody');
    tbody.innerHTML = '';
    if (!preview.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 5;
      td.textContent = 'No data';
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    preview.slice(0, 10).forEach((row) => {
      const tr = document.createElement('tr');
      ['date', 'region', 'product', 'sales_amount', 'quantity'].forEach((field) => {
        const td = document.createElement('td');
        let value = row[field];
        if (field === 'sales_amount') value = `$${Number(value).toFixed(2)}`;
        td.textContent = value;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function generateColor(index) {
    const colors = [
      '#2563eb',
      '#ea580c',
      '#16a34a',
      '#d946ef',
      '#facc15',
      '#06b6d4',
      '#ef4444',
      '#9333ea',
    ];
    return colors[index % colors.length];
  }

  function renderComparisonChart(data) {
    const ctx = document.getElementById('sales-chart').getContext('2d');
    const labels = data.labels || [];
    const datasets = (data.datasets || []).map((ds, idx) => ({
      label: ds.label,
      data: ds.data,
      borderColor: generateColor(idx),
      backgroundColor: generateColor(idx) + '33',
      tension: 0.2,
      fill: false,
      pointRadius: 3,
    }));

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', intersect: false },
        plugins: {
          legend: { display: true, position: 'bottom' },
          tooltip: { enabled: true },
          zoom: {
            zoom: {
              wheel: { enabled: true },
              pinch: { enabled: true },
              mode: 'x',
            },
            pan: { enabled: true, mode: 'x' },
          },
        },
        scales: {
          x: { title: { display: true, text: 'Date' } },
          y: { title: { display: true, text: 'Sales Amount' } },
        },
        onClick: handleChartClick,
      },
    });
  }

  function handleChartClick(evt, activeEls) {
    if (!chartInstance) return;
    const points = chartInstance.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
    if (points.length) {
      const firstPoint = points[0];
      const label = chartInstance.data.labels[firstPoint.index];
      const value = chartInstance.data.datasets[firstPoint.datasetIndex].data[firstPoint.index];
      console.log('Clicked:', { label, value, dataset: chartInstance.data.datasets[firstPoint.datasetIndex].label });
    }
  }

  async function fetchSalesData() {
    const filters = getSelectedFilters();

    chartLoadingEl.style.display = 'inline';
    try {
      const res = await axios.get('/api/sales', { params: filters, paramsSerializer });
      const data = res.data;
      renderComparisonChart(data);
      updateSummary(data.summary || {});
      updateTable(data.preview || []);
    } catch (err) {
      console.error('Failed to fetch sales data', err);
    } finally {
      chartLoadingEl.style.display = 'none';
    }
  }

  function startAutoRefresh() {
    const { auto_refresh } = getSelectedFilters();
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    const interval = Number(auto_refresh);
    if (interval > 0) {
      autoRefreshTimer = setInterval(fetchSalesData, interval);
    }
  }

  function bindEvents() {
    const debouncedFetch = debounce(() => {
      fetchSalesData();
      startAutoRefresh();
    }, 300);

    document.getElementById('group-by').addEventListener('change', debouncedFetch);
    document.getElementById('auto-refresh').addEventListener('change', () => {
      startAutoRefresh();
    });
    document.getElementById('export-btn').addEventListener('click', () => {
      const filters = getSelectedFilters();
      const qs = paramsSerializer(filters);
      window.location = `/api/export?${qs}`;
    });
  }

  async function initFilters() {
    const res = await axios.get('/api/filters');
    const { regions, products, date_range } = res.data;

    const regionSelect = document.getElementById('region-select');
    regions.forEach((r) => {
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = r;
      regionSelect.appendChild(opt);
    });
    choicesRegion = new Choices(regionSelect, { removeItemButton: true, placeholder: true, placeholderValue: 'All regions' });

    const productSelect = document.getElementById('product-select');
    products.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      productSelect.appendChild(opt);
    });
    choicesProduct = new Choices(productSelect, { removeItemButton: true, placeholder: true, placeholderValue: 'All products' });

    datePicker = flatpickr('#date-range', {
      mode: 'range',
      dateFormat: 'Y-m-d',
      minDate: date_range.min,
      maxDate: date_range.max,
      onClose: debounce(fetchSalesData, 300),
    });

    // initial fetch
    fetchSalesData();
  }

  window.addEventListener('blur', () => {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  });
  window.addEventListener('focus', () => {
    startAutoRefresh();
  });

  document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    initFilters();
  });
})();
