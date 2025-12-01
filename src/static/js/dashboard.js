/**
 * Enhanced Sales Dashboard - Frontend Logic
 * Features:
 * - AJAX-based data fetching with 300ms debounce
 * - Interactive Chart.js visualizations with zoom/tooltips
 * - Multi-select filtering with Choices.js
 * - Custom date range with Flatpickr
 * - Auto-refresh with configurable intervals
 * - State preservation and error handling
 */

// Configuration
const CONFIG = {
    API_BASE: '/api/v1',
    DEBOUNCE_DELAY: 300,
    AUTO_REFRESH_INTERVAL: 60000, // 1 minute default
};

// State
const state = {
    selectedRegions: [],
    selectedProducts: [],
    startDate: null,
    endDate: null,
    groupBy: 'daily',
    autoRefreshInterval: 60,
    chart: null,
    autoRefreshTimer: null,
    isLoading: false,
    debounceTimer: null,
    filterOptions: {
        regions: [],
        products: [],
        dateRange: {}
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeFilters();
    loadFilterOptions();
    setupEventListeners();
    loadInitialData();
});

/**
 * Initialize filter UI components
 */
function initializeFilters() {
    // Initialize Choices.js for multi-select
    const regionSelect = new Choices('#regionSelect', {
        allowSearch: true,
        allowHTML: false,
        searchResultLimit: 10,
        placeholderValue: 'Select regions...',
        noResultsText: 'No regions found'
    });

    const productSelect = new Choices('#productSelect', {
        allowSearch: true,
        allowHTML: false,
        searchResultLimit: 10,
        placeholderValue: 'Select products...',
        noResultsText: 'No products found'
    });

    // Initialize Flatpickr for date selection
    flatpickr('#startDateInput', {
        mode: 'single',
        dateFormat: 'Y-m-d',
        onChange: handleFilterChange
    });

    flatpickr('#endDateInput', {
        mode: 'single',
        dateFormat: 'Y-m-d',
        onChange: handleFilterChange
    });

    // Initialize Chart.js chart
    initializeChart();
}

/**
 * Load filter options from API
 */
async function loadFilterOptions() {
    try {
        const response = await axios.get(`${CONFIG.API_BASE}/filters`);
        
        if (response.data.status === 'success') {
            state.filterOptions = response.data.data;

            // Populate region options
            const regionSelect = new Choices('#regionSelect').clearStore();
            state.filterOptions.regions.forEach(region => {
                regionSelect.setChoiceByValue(region);
            });

            // Populate product options
            const productSelect = new Choices('#productSelect').clearStore();
            state.filterOptions.products.forEach(product => {
                productSelect.setChoiceByValue(product);
            });

            // Set date range
            const dateRange = state.filterOptions.date_range;
            if (dateRange) {
                document.getElementById('startDateInput').placeholder = dateRange.min;
                document.getElementById('endDateInput').placeholder = dateRange.max;
            }
        }
    } catch (error) {
        console.error('Error loading filter options:', error);
        showError('Failed to load filter options');
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Filter change events with debounce
    document.getElementById('regionSelect').addEventListener('change', handleFilterChange);
    document.getElementById('productSelect').addEventListener('change', handleFilterChange);
    document.getElementById('aggregationSelect').addEventListener('change', handleFilterChange);
    document.getElementById('autoRefreshSelect').addEventListener('change', handleAutoRefreshChange);

    // Clear filters button
    document.getElementById('clearFiltersBtn').addEventListener('click', clearAllFilters);

    // Quick preset buttons
    document.querySelectorAll('[data-preset]').forEach(btn => {
        btn.addEventListener('click', handlePresetClick);
    });

    // Export and download buttons
    document.getElementById('downloadChartBtn').addEventListener('click', downloadChart);
    document.getElementById('exportCSVBtn').addEventListener('click', exportToCSV);
}

/**
 * Handle filter change with debounce
 */
function handleFilterChange() {
    // Clear existing debounce timer
    clearTimeout(state.debounceTimer);

    // Update state from form
    updateFilterState();

    // Debounce the data fetch (300ms)
    state.debounceTimer = setTimeout(() => {
        fetchSalesData();
    }, CONFIG.DEBOUNCE_DELAY);
}

/**
 * Update state from form controls
 */
function updateFilterState() {
    // Get selected regions
    const regionSelect = new Choices('#regionSelect');
    state.selectedRegions = regionSelect.getValue(true).filter(v => v !== '');

    // Get selected products
    const productSelect = new Choices('#productSelect');
    state.selectedProducts = productSelect.getValue(true).filter(v => v !== '');

    // Get dates
    state.startDate = document.getElementById('startDateInput').value;
    state.endDate = document.getElementById('endDateInput').value;

    // Get aggregation
    state.groupBy = document.getElementById('aggregationSelect').value;
}

/**
 * Fetch sales data from API
 */
async function fetchSalesData() {
    // Prevent duplicate requests
    if (state.isLoading) return;

    updateFilterState();
    showLoading(true);
    clearError();

    try {
        // Build query parameters
        const params = new URLSearchParams();

        if (state.selectedRegions.length > 0) {
            state.selectedRegions.forEach(region => params.append('regions[]', region));
        }

        if (state.selectedProducts.length > 0) {
            state.selectedProducts.forEach(product => params.append('products[]', product));
        }

        if (state.startDate) {
            params.append('start_date', state.startDate);
        }

        if (state.endDate) {
            params.append('end_date', state.endDate);
        }

        params.append('group_by', state.groupBy);

        // Fetch data
        const response = await axios.get(`${CONFIG.API_BASE}/sales?${params.toString()}`);

        if (response.data.status === 'success') {
            const data = response.data.data;

            // Update summary
            updateSummary(data.summary);

            // Update chart
            renderComparisonChart(data.chart);

            // Update table
            updateDataTable(data.records);

            // Show cache indicator
            if (data.from_cache) {
                showCacheIndicator();
            }

            console.log(`Data fetched: ${data.records} records, cached: ${data.from_cache}`);
        } else {
            showError(response.data.message || 'Failed to fetch data');
        }
    } catch (error) {
        console.error('Error fetching sales data:', error);
        showError('Failed to fetch sales data. Please try again.');
    } finally {
        showLoading(false);
    }
}

/**
 * Initialize Chart.js chart
 */
function initializeChart() {
    const ctx = document.getElementById('salesChart').getContext('2d');

    state.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#ddd',
                    borderWidth: 1
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'xy'
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy'
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Sales (USD)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Quantity'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

/**
 * Render comparison chart with data
 */
function renderComparisonChart(chartData) {
    if (!state.chart) return;

    state.chart.data.labels = chartData.labels;
    state.chart.data.datasets = chartData.datasets;
    state.chart.update();
}

/**
 * Update summary cards
 */
function updateSummary(summary) {
    document.getElementById('totalSalesValue').textContent = 
        '$' + summary.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    document.getElementById('totalQuantityValue').textContent = 
        summary.total_quantity.toLocaleString();
    
    document.getElementById('averageSalesValue').textContent = 
        '$' + summary.average_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    document.getElementById('recordCountValue').textContent = 
        summary.record_count.toLocaleString();
}

/**
 * Update data table
 */
function updateDataTable(recordCount) {
    const tableBody = document.getElementById('tableBody');
    
    // For now, show record count
    // In a full implementation, this would fetch and display actual records
    if (recordCount === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No records found</td></tr>';
    } else {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">${recordCount} records found (showing in aggregated chart above)</td></tr>`;
    }
}

/**
 * Handle preset date selection
 */
function handlePresetClick(event) {
    const preset = event.target.dataset.preset;
    const endDate = dayjs();
    let startDate;

    switch (preset) {
        case '7days':
            startDate = endDate.subtract(7, 'day');
            break;
        case '30days':
            startDate = endDate.subtract(30, 'day');
            break;
        case '90days':
            startDate = endDate.subtract(90, 'day');
            break;
        case 'all':
            startDate = dayjs(state.filterOptions.date_range.min);
            break;
        default:
            return;
    }

    // Update date inputs
    document.getElementById('startDateInput').value = startDate.format('YYYY-MM-DD');
    document.getElementById('endDateInput').value = endDate.format('YYYY-MM-DD');

    // Trigger data fetch
    handleFilterChange();
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    // Clear selections
    new Choices('#regionSelect').clearStore();
    new Choices('#productSelect').clearStore();
    
    document.getElementById('startDateInput').value = '';
    document.getElementById('endDateInput').value = '';
    document.getElementById('aggregationSelect').value = 'daily';

    // Reset state
    state.selectedRegions = [];
    state.selectedProducts = [];
    state.startDate = null;
    state.endDate = null;
    state.groupBy = 'daily';

    // Fetch fresh data
    fetchSalesData();
}

/**
 * Handle auto-refresh interval change
 */
function handleAutoRefreshChange() {
    const interval = parseInt(document.getElementById('autoRefreshSelect').value);
    state.autoRefreshInterval = interval;

    // Clear existing timer
    if (state.autoRefreshTimer) {
        clearInterval(state.autoRefreshTimer);
        state.autoRefreshTimer = null;
    }

    // Start new auto-refresh if interval > 0
    if (interval > 0) {
        startAutoRefresh();
    }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (state.autoRefreshTimer) {
        clearInterval(state.autoRefreshTimer);
    }

    state.autoRefreshTimer = setInterval(() => {
        // Only refresh if not currently loading
        if (!state.isLoading) {
            console.log(`Auto-refreshing data (interval: ${state.autoRefreshInterval}s)`);
            fetchSalesData();
        }
    }, state.autoRefreshInterval * 1000);
}

/**
 * Download chart as image
 */
function downloadChart() {
    if (!state.chart) return;

    const canvas = document.getElementById('salesChart');
    const image = canvas.toDataURL('image/png');

    const link = document.createElement('a');
    link.href = image;
    link.download = `sales_chart_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.png`;
    link.click();
}

/**
 * Export data as CSV
 */
async function exportToCSV() {
    updateFilterState();
    showLoading(true);

    try {
        // Build query parameters (same as fetch)
        const params = new URLSearchParams();

        if (state.selectedRegions.length > 0) {
            state.selectedRegions.forEach(region => params.append('regions[]', region));
        }

        if (state.selectedProducts.length > 0) {
            state.selectedProducts.forEach(product => params.append('products[]', product));
        }

        if (state.startDate) {
            params.append('start_date', state.startDate);
        }

        if (state.endDate) {
            params.append('end_date', state.endDate);
        }

        // Fetch CSV file
        const response = await axios.get(`${CONFIG.API_BASE}/export?${params.toString()}`, {
            responseType: 'blob'
        });

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `sales_export_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.csv`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showError('Failed to export data');
    } finally {
        showLoading(false);
    }
}

/**
 * UI Helper Functions
 */

function showLoading(isLoading) {
    state.isLoading = isLoading;
    const indicator = document.getElementById('loadingIndicator');
    if (isLoading) {
        indicator.style.display = 'block';
    } else {
        indicator.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorDiv.style.display = 'block';
}

function clearError() {
    document.getElementById('errorMessage').style.display = 'none';
}

function showCacheIndicator() {
    const indicator = document.getElementById('cacheIndicator');
    indicator.style.display = 'inline-block';
    setTimeout(() => {
        indicator.style.display = 'none';
    }, 2000);
}

/**
 * Load initial data on page load
 */
function loadInitialData() {
    // Set default date range to last 30 days
    const endDate = dayjs();
    const startDate = endDate.subtract(30, 'day');

    document.getElementById('startDateInput').value = startDate.format('YYYY-MM-DD');
    document.getElementById('endDateInput').value = endDate.format('YYYY-MM-DD');

    // Fetch data
    setTimeout(() => {
        fetchSalesData();
    }, 500);
}
