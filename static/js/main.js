document.addEventListener('DOMContentLoaded', function() {
    // Initialize all dashboard functionality
    initDashboard();
});

function initDashboard() {
    // Initialize search functionality
    initSearch();
    
    // Initialize charts
    initCharts();
    
    // Initialize dropdown menus
    initDropdowns();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize activity feed interactions
    initActivityFeed();
    
    // Add any other initialization functions here
}

// Search functionality
function initSearch() {
    const searchBtn = document.querySelector('.btn-search');
    const searchInput = document.querySelector('.search-box .form-control');
    
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', function() {
            performSearch(searchInput.value);
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(searchInput.value);
            }
        });
    }
}

function performSearch(query) {
    if (query.trim() !== '') {
        console.log('Searching for:', query);
        // Here you would typically make an AJAX request to your backend
        // For now we'll just show a notification
        showNotification(`Search results for: ${query}`, 'info');
    }
}

// Chart initialization
function initCharts() {
    // Check if chart containers exist
    if (document.getElementById('apexcharts-area')) {
        initReferralTrendsChart();
    }
    
    if (document.getElementById('bar')) {
        initCompletionRateChart();
    }
}

function initReferralTrendsChart() {
    // Sample data for the referral trends chart
    const options = {
        series: [{
            name: 'Referrals',
            data: [31, 40, 28, 51, 42, 109, 100]
        }],
        chart: {
            height: 350,
            type: 'area',
            toolbar: {
                show: false
            }
        },
        colors: ['#4f81a4'],
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        xaxis: {
            type: 'datetime',
            categories: [
                "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", 
                "2023-01-05", "2023-01-06", "2023-01-07"
            ]
        },
        tooltip: {
            x: {
                format: 'dd/MM/yy'
            },
        },
    };

    const chart = new ApexCharts(document.querySelector("#apexcharts-area"), options);
    chart.render();
}

function initCompletionRateChart() {
    // Sample data for the completion rate chart
    const options = {
        series: [{
            name: 'Completion Rate',
            data: [44, 55, 57, 56, 61, 58, 63]
        }],
        chart: {
            type: 'bar',
            height: 350,
            toolbar: {
                show: false
            }
        },
        colors: ['#00b894'],
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '55%',
                endingShape: 'rounded'
            },
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['transparent']
        },
        xaxis: {
            categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        },
        yaxis: {
            title: {
                text: 'Completion Rate (%)'
            }
        },
        fill: {
            opacity: 1
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + "%"
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector("#bar"), options);
    chart.render();
}

// Dropdown initialization
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.amount-spent-select select');
    
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', function() {
            const selectedValue = this.value;
            const cardTitle = this.closest('.card-header').querySelector('.card-title').textContent;
            
            console.log(`${cardTitle} filter changed to: ${selectedValue}`);
            showNotification(`Filter applied: ${selectedValue}`, 'success');
            
            // Here you would typically reload chart data based on the selected filter
            // For now we'll just log the change
        });
    });
}

// Activity feed interactions
function initActivityFeed() {
    const activityItems = document.querySelectorAll('.activity-feed .feed-item');
    
    activityItems.forEach(item => {
        item.addEventListener('click', function() {
            const date = this.querySelector('.feed-date').textContent;
            const text = this.querySelector('.feed-text').textContent;
            
            console.log(`Activity clicked: ${date} - ${text}`);
            // You could add functionality to show more details about the activity
        });
    });
}

// Tooltip initialization
function initTooltips() {
    // Initialize tooltips using Bootstrap's tooltip component
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add tooltips to status badges
    const statusBadges = document.querySelectorAll('.badge');
    statusBadges.forEach(badge => {
        badge.setAttribute('data-bs-toggle', 'tooltip');
        
        if (badge.classList.contains('bg-success-light')) {
            badge.setAttribute('title', 'Completed referral');
        } else if (badge.classList.contains('bg-warning-light')) {
            badge.setAttribute('title', 'Referral in transit');
        } else if (badge.classList.contains('bg-danger-light')) {
            badge.setAttribute('title', 'Urgent referral');
        } else if (badge.classList.contains('bg-info-light')) {
            badge.setAttribute('title', 'Pending referral');
        }
    });
}

// Notification system
function showNotification(message, type = 'info') {
    // In a real implementation, you might use a proper notification library
    // Here's a simple implementation using console and alert
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // You could replace this with a toast notification
    alert(`${type.toUpperCase()}: ${message}`);
}

// Make functions available globally if needed
window.initDashboard = initDashboard;
window.performSearch = performSearch;
window.showNotification = showNotification;

 
        document.addEventListener('DOMContentLoaded', function() {
            // Dropdown functionality for sidebar items (toggle sub-menus)
            const dropdownTriggers = document.querySelectorAll('.submenu > a');

            dropdownTriggers.forEach(trigger => {
                trigger.addEventListener('click', function(e) {
                    e.preventDefault(); // Prevent default link behavior for dropdowns

                    const parentLi = this.closest('li');

                    // Toggle 'active' class on the clicked submenu
                    parentLi.classList.toggle('active');

                    // Close other open submenus
                    document.querySelectorAll('.submenu').forEach(menu => {
                        if (menu !== parentLi) { // If it's not the clicked submenu
                            menu.classList.remove('active'); // Close it
                        }
                    });
                });
            });

            // Close dropdowns when clicking outside
            document.addEventListener('click', function(e) {
                // Check if the click is outside any .submenu or inside a .sub-menu itself
                // (Clicking inside sub-menu should not close it, handled by stopPropagation below)
                if (!e.target.closest('.submenu') && !e.target.closest('.sub-menu')) {
                    document.querySelectorAll('.submenu').forEach(li => {
                        li.classList.remove('active');
                    });
                }
            });

            // Prevent dropdown from closing when clicking inside its sub-menu
            document.querySelectorAll('.sub-menu').forEach(menu => {
                menu.addEventListener('click', function(e) {
                    e.stopPropagation(); // Stop propagation to prevent the document click listener from closing it
                });
            });
        });
    