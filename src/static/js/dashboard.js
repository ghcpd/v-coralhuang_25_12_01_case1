/**
 * Interactive Sales Dashboard - Main JavaScript
 * Features: AJAX updates, chart rendering, filter management, auto-refresh
 */

const DashboardApp = (function() {
    'use strict';

    // Application state
    let state = {
        chart: null,
        chartType: 'line',
        autoRefreshTimer: null,
        filterChoices: {},
        dateRangePicker: null,
        lastFetchTime: 0,
        debounceTimer: null
    };

    // Configuration
    const config = {
        apiBaseUrl: '',  // Same origin
        debounceDelay: 300,  // 300ms debounce
        chartColors: [
            'rgb(54, 162, 235)',
            'rgb(255, 99, 132)',
            'rgb(75, 192, 192)',
            'rgb(255, 159, 64)',
            'rgb(153, 102, 255)',
            'rgb(255, 205, 86)',
            'rgb(201, 203, 207)'
        ]
    };

    /**
     * Initialize the dashboard application
     */
    function init() {
        console.log('🚀 Initializing Dashboard...');
        
        initializeComponents();
        loadFilterOptions();
        setupEventListeners();
        
        // Initial data load
        fetchSalesData();
        
        console.log('✓ Dashboard initialized successfully');
    }

    /**
     * Initialize UI components (Choices.js, Flatpickr)
     */
    function initializeComponents() {
        // Initialize multi-select dropdowns with Choices.js
        const regionSelect = document.getElementById('regionSelect');
        const productSelect = document.getElementById('productSelect');

        if (regionSelect) {
            state.filterChoices.regions = new Choices(regionSelect, {
                removeItemButton: true,
                placeholder: true,
                placeholderValue: 'Select regions...',
                searchEnabled: true,
                searchPlaceholderValue: 'Search regions...'
            });
        }

        if (productSelect) {
            state.filterChoices.products = new Choices(productSelect, {
                removeItemButton: true,
                placeholder: true,
                placeholderValue: 'Select products...',
                searchEnabled: true,
                searchPlaceholderValue: 'Search products...'
            });
        }

        // Initialize date range picker with Flatpickr
        const dateRangeInput = document.getElementById('dateRange');
        if (dateRangeInput) {
            state.dateRangePicker = flatpickr(dateRangeInput, {
                mode: 'range',
                dateFormat: 'Y-m-d',
                maxDate: 'today',
                onChange: function(selectedDates) {
                    if (selectedDates.length === 2) {
                        document.getElementById('quickRange').value = 'custom';
                        debouncedFetchSalesData();
                    }
                }
            });
        }

        // Set default date range (last 30 days)
        setQuickDateRange('30days');
    }

    /**
     * Setup event listeners for all interactive elements
     */
    function setupEventListeners() {
        // Filter change events
        document.getElementById('quickRange').addEventListener('change', handleQuickRangeChange);
        document.getElementById('groupBy').addEventListener('change', debouncedFetchSalesData);
        document.getElementById('compareBy').addEventListener('change', debouncedFetchSalesData);

        // Region and product filters (via Choices.js)
        const regionSelect = document.getElementById('regionSelect');
        const productSelect = document.getElementById('productSelect');
        
        if (regionSelect) {
            regionSelect.addEventListener('change', debouncedFetchSalesData);
        }
        if (productSelect) {
            productSelect.addEventListener('change', debouncedFetchSalesData);
        }

        // Auto-refresh controls
        document.getElementById('autoRefreshToggle').addEventListener('change', handleAutoRefreshToggle);
        document.getElementById('refreshInterval').addEventListener('change', handleRefreshIntervalChange);

        // Action buttons
        document.getElementById('resetFilters').addEventListener('click', resetFilters);
        document.getElementById('exportCsv').addEventListener('click', exportToCSV);
        document.getElementById('downloadChart').addEventListener('click', downloadChartImage);
        document.getElementById('toggleChartType').addEventListener('click', toggleChartType);
    }

    /**
     * Load available filter options from API
     */
    async function loadFilterOptions() {
        try {
            const response = await axios.get('/api/filters');
            const data = response.data;

            // Populate region choices
            if (state.filterChoices.regions) {
                state.filterChoices.regions.setChoices(
                    data.regions.map(region => ({ value: region, label: region })),
                    'value',
                    'label',
                    true
                );
            }

            // Populate product choices
            if (state.filterChoices.products) {
                state.filterChoices.products.setChoices(
                    data.products.map(product => ({ value: product, label: product })),
                    'value',
                    'label',
                    true
                );
            }

            console.log('✓ Filter options loaded');
        } catch (error) {
            console.error('Error loading filter options:', error);
            showError('Failed to load filter options');
        }
    }

    /**
     * Get currently selected filter values
     */
    function getSelectedFilters() {
        const regions = Array.from(document.getElementById('regionSelect').selectedOptions).map(o => o.value);
        const products = Array.from(document.getElementById('productSelect').selectedOptions).map(o => o.value);
        const groupBy = document.getElementById('groupBy').value;
        const compareBy = document.getElementById('compareBy').value;

        // Get date range
        let startDate, endDate;
        const dateRangeValue = state.dateRangePicker.selectedDates;
        
        if (dateRangeValue.length === 2) {
            startDate = dayjs(dateRangeValue[0]).format('YYYY-MM-DD');
            endDate = dayjs(dateRangeValue[1]).format('YYYY-MM-DD');
        } else {
            // Use default if no range selected
            endDate = dayjs().format('YYYY-MM-DD');
            startDate = dayjs().subtract(30, 'day').format('YYYY-MM-DD');
        }

        return {
            regions,
            products,
            start_date: startDate,
            end_date: endDate,
            group_by: groupBy,
            compare_by: compareBy
        };
    }

    /**
     * Fetch sales data from API with debouncing
     */
    function debouncedFetchSalesData() {
        // Clear existing timer
        if (state.debounceTimer) {
            clearTimeout(state.debounceTimer);
        }

        // Set new timer
        state.debounceTimer = setTimeout(() => {
            fetchSalesData();
        }, config.debounceDelay);
    }

    /**
     * Fetch sales data from API
     */
    async function fetchSalesData() {
        const startTime = performance.now();
        showLoading(true);
        hideError();

        try {
            const filters = getSelectedFilters();
            
            // Build query parameters
            const params = new URLSearchParams();
            filters.regions.forEach(r => params.append('regions[]', r));
            filters.products.forEach(p => params.append('products[]', p));
            params.append('start_date', filters.start_date);
            params.append('end_date', filters.end_date);
            params.append('group_by', filters.group_by);
            params.append('compare_by', filters.compare_by);

            const response = await axios.get(`/api/sales?${params.toString()}`);
            const data = response.data;

            // Measure response time
            const responseTime = Math.round(performance.now() - startTime);
            document.getElementById('apiResponseTime').textContent = `API: ${responseTime}ms`;

            // Update cache status
            const cacheStatus = response.headers['x-cache-hit'] || 'unknown';
            document.getElementById('cacheStatus').textContent = `Cache: ${cacheStatus}`;

            // Update UI
            updateSummaryCards(data.summary);
            renderComparisonChart(data);
            updateLastUpdatedTime();

            state.lastFetchTime = Date.now();

        } catch (error) {
            console.error('Error fetching sales data:', error);
            showError(error.response?.data?.message || 'Failed to load sales data');
        } finally {
            showLoading(false);
        }
    }

    /**
     * Render chart with comparison data
     */
    function renderComparisonChart(data) {
        const ctx = document.getElementById('salesChart').getContext('2d');

        // Destroy existing chart
        if (state.chart) {
            state.chart.destroy();
        }

        // Prepare chart configuration
        const chartConfig = {
            type: state.chartType,
            data: {
                labels: data.labels,
                datasets: data.datasets.map((dataset, index) => ({
                    ...dataset,
                    backgroundColor: dataset.backgroundColor || config.chartColors[index % config.chartColors.length].replace('rgb', 'rgba').replace(')', ', 0.2)'),
                    borderColor: dataset.borderColor || config.chartColors[index % config.chartColors.length],
                    borderWidth: 2,
                    tension: 0.4,
                    fill: state.chartType === 'line' ? false : true
                }))
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
                        position: 'top',
                        onClick: handleChartLegendClick
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += '$' + context.parsed.y.toLocaleString('en-US', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                });
                                return label;
                            }
                        }
                    },
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString('en-US');
                            }
                        }
                    }
                },
                onClick: handleChartClick
            }
        };

        // Create new chart
        state.chart = new Chart(ctx, chartConfig);

        console.log('✓ Chart rendered');
    }

    /**
     * Handle chart click events
     */
    function handleChartClick(event, activeElements) {
        if (activeElements.length > 0) {
            const element = activeElements[0];
            const datasetLabel = state.chart.data.datasets[element.datasetIndex].label;
            const label = state.chart.data.labels[element.index];
            const value = state.chart.data.datasets[element.datasetIndex].data[element.index];
            
            console.log(`Clicked: ${datasetLabel} - ${label}: $${value}`);
            // Could implement drill-down functionality here
        }
    }

    /**
     * Handle chart legend click events
     */
    function handleChartLegendClick(e, legendItem, legend) {
        const index = legendItem.datasetIndex;
        const chart = legend.chart;
        const meta = chart.getDatasetMeta(index);

        // Toggle dataset visibility
        meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;
        chart.update();
    }

    /**
     * Update summary cards with data
     */
    function updateSummaryCards(summary) {
        document.getElementById('totalSales').textContent = 
            '$' + summary.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2 });
        document.getElementById('totalQuantity').textContent = 
            summary.total_quantity.toLocaleString('en-US');
        document.getElementById('averageSale').textContent = 
            '$' + summary.average_sale.toLocaleString('en-US', { minimumFractionDigits: 2 });
        document.getElementById('recordCount').textContent = 
            summary.record_count.toLocaleString('en-US');

        // Show summary section
        document.getElementById('summarySection').style.display = 'grid';
    }

    /**
     * Handle quick date range selection
     */
    function handleQuickRangeChange(event) {
        const value = event.target.value;
        if (value !== 'custom') {
            setQuickDateRange(value);
            debouncedFetchSalesData();
        }
    }

    /**
     * Set date range based on quick select value
     */
    function setQuickDateRange(value) {
        let startDate, endDate;
        endDate = dayjs();

        switch (value) {
            case '7days':
                startDate = dayjs().subtract(7, 'day');
                break;
            case '30days':
                startDate = dayjs().subtract(30, 'day');
                break;
            case '90days':
                startDate = dayjs().subtract(90, 'day');
                break;
            default:
                return;
        }

        state.dateRangePicker.setDate([startDate.toDate(), endDate.toDate()]);
    }

    /**
     * Start auto-refresh
     */
    function startAutoRefresh() {
        const interval = parseInt(document.getElementById('refreshInterval').value) * 1000;
        
        state.autoRefreshTimer = setInterval(() => {
            console.log('⟳ Auto-refreshing...');
            fetchSalesData();
        }, interval);

        console.log(`✓ Auto-refresh started (${interval / 1000}s interval)`);
    }

    /**
     * Stop auto-refresh
     */
    function stopAutoRefresh() {
        if (state.autoRefreshTimer) {
            clearInterval(state.autoRefreshTimer);
            state.autoRefreshTimer = null;
            console.log('✓ Auto-refresh stopped');
        }
    }

    /**
     * Handle auto-refresh toggle
     */
    function handleAutoRefreshToggle(event) {
        const enabled = event.target.checked;
        document.getElementById('refreshInterval').disabled = !enabled;

        if (enabled) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    }

    /**
     * Handle refresh interval change
     */
    function handleRefreshIntervalChange() {
        if (document.getElementById('autoRefreshToggle').checked) {
            stopAutoRefresh();
            startAutoRefresh();
        }
    }

    /**
     * Reset all filters to default
     */
    function resetFilters() {
        // Clear multi-selects
        if (state.filterChoices.regions) {
            state.filterChoices.regions.removeActiveItems();
        }
        if (state.filterChoices.products) {
            state.filterChoices.products.removeActiveItems();
        }

        // Reset selects
        document.getElementById('quickRange').value = '30days';
        document.getElementById('groupBy').value = 'day';
        document.getElementById('compareBy').value = 'none';

        // Reset date range
        setQuickDateRange('30days');

        // Fetch fresh data
        fetchSalesData();

        console.log('✓ Filters reset');
    }

    /**
     * Export data to CSV
     */
    async function exportToCSV() {
        try {
            const filters = getSelectedFilters();
            
            // Build query parameters
            const params = new URLSearchParams();
            filters.regions.forEach(r => params.append('regions[]', r));
            filters.products.forEach(p => params.append('products[]', p));
            params.append('start_date', filters.start_date);
            params.append('end_date', filters.end_date);

            // Download file
            window.location.href = `/api/export?${params.toString()}`;

            console.log('✓ CSV export initiated');
        } catch (error) {
            console.error('Error exporting CSV:', error);
            showError('Failed to export CSV');
        }
    }

    /**
     * Download chart as image
     */
    function downloadChartImage() {
        if (state.chart) {
            const link = document.createElement('a');
            link.download = `sales-chart-${dayjs().format('YYYY-MM-DD')}.png`;
            link.href = state.chart.toBase64Image();
            link.click();

            console.log('✓ Chart image downloaded');
        }
    }

    /**
     * Toggle chart type between line and bar
     */
    function toggleChartType() {
        state.chartType = state.chartType === 'line' ? 'bar' : 'line';
        
        // Re-fetch to re-render with new type
        fetchSalesData();

        console.log(`✓ Chart type changed to: ${state.chartType}`);
    }

    /**
     * Update last updated timestamp
     */
    function updateLastUpdatedTime() {
        const now = dayjs();
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${now.format('HH:mm:ss')}`;
    }

    /**
     * Show/hide loading indicator
     */
    function showLoading(show) {
        document.getElementById('loadingIndicator').style.display = show ? 'flex' : 'none';
    }

    /**
     * Show error message
     */
    function showError(message) {
        const errorDiv = document.getElementById('chartError');
        errorDiv.querySelector('.error-text').textContent = message;
        errorDiv.style.display = 'block';
    }

    /**
     * Hide error message
     */
    function hideError() {
        document.getElementById('chartError').style.display = 'none';
    }

    // Public API
    return {
        init,
        fetchSalesData,
        getSelectedFilters,
        renderComparisonChart,
        handleChartClick,
        startAutoRefresh,
        stopAutoRefresh
    };
})();

// Export for use in HTML
window.DashboardApp = DashboardApp;
