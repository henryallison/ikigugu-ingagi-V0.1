document.addEventListener('DOMContentLoaded', function() {
    // Initialize all list functionality
    initReferralList();
});

function initReferralList() {
    // Initialize search functionality
    initSearch();
    
    // Initialize table interactions
    initTableInteractions();
    
    // Initialize pagination
    initPagination();
    
    // Initialize export functionality
    initExport();
}

// Search functionality
function initSearch() {
    const searchInput = document.querySelector('.search-box input');
    const searchBtn = document.querySelector('.search-box button');
    const tableRows = document.querySelectorAll('.referral-table tbody tr');
    
    if (searchInput && searchBtn) {
        // Search when button is clicked
        searchBtn.addEventListener('click', function() {
            performSearch(searchInput.value.trim().toLowerCase());
        });
        
        // Search when Enter key is pressed
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                performSearch(searchInput.value.trim().toLowerCase());
            }
        });
        
        // Real-time search as user types (optional)
        searchInput.addEventListener('input', function() {
            if (this.value.length === 0 || this.value.length > 2) {
                performSearch(this.value.trim().toLowerCase());
            }
        });
    }
    
    function performSearch(query) {
        tableRows.forEach(row => {
            const rowText = row.textContent.toLowerCase();
            if (rowText.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

// Table row interactions
function initTableInteractions() {
    const tableRows = document.querySelectorAll('.referral-table tbody tr');
    
    tableRows.forEach(row => {
        // Highlight row on hover
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
        
        // Click on view button
        const viewBtn = row.querySelector('.btn-view');
        if (viewBtn) {
            viewBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const referralId = this.closest('tr').querySelector('td:first-child').textContent;
                viewReferralDetails(referralId);
            });
        }
        
        // Click on edit button
        const editBtn = row.querySelector('.btn-edit');
        if (editBtn) {
            editBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const referralId = this.closest('tr').querySelector('td:first-child').textContent;
                editReferral(referralId);
            });
        }
        
        // Click on entire row (optional)
        row.addEventListener('click', function() {
            const referralId = this.querySelector('td:first-child').textContent;
            viewReferralDetails(referralId);
        });
    });
}

// View referral details
function viewReferralDetails(referralId) {
    console.log('Viewing referral:', referralId);
    // In a real implementation, this would redirect to the details page or show a modal
    // window.location.href = `/referrals/${referralId}/`;
}

// Edit referral
function editReferral(referralId) {
    console.log('Editing referral:', referralId);
    // In a real implementation, this would redirect to the edit page
    // window.location.href = `/referrals/${referralId}/edit/`;
}

// Pagination functionality
function initPagination() {
    const prevBtn = document.querySelector('.btn-prev');
    const nextBtn = document.querySelector('.btn-next');
    const pageNumbers = document.querySelectorAll('.page-numbers span');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            navigateToPage('prev');
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            navigateToPage('next');
        });
    }
    
    pageNumbers.forEach(page => {
        page.addEventListener('click', function() {
            const pageNum = parseInt(this.textContent);
            navigateToPage(pageNum);
        });
    });
    
    function navigateToPage(directionOrPage) {
        let currentPage = parseInt(document.querySelector('.page-numbers span.active').textContent);
        let newPage = currentPage;
        
        if (directionOrPage === 'prev' && currentPage > 1) {
            newPage = currentPage - 1;
        } else if (directionOrPage === 'next') {
            newPage = currentPage + 1;
        } else if (typeof directionOrPage === 'number') {
            newPage = directionOrPage;
        }
        
        if (newPage !== currentPage) {
            console.log('Navigating to page:', newPage);
            // In a real implementation, this would fetch new data or reload the page
            // window.location.href = `?page=${newPage}`;
            
            // For demo purposes, just update the active page
            document.querySelector('.page-numbers span.active').classList.remove('active');
            document.querySelectorAll('.page-numbers span')[newPage - 1].classList.add('active');
        }
    }
}

// Export functionality
function initExport() {
    const exportBtn = document.querySelector('.btn-export');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportReferrals();
        });
    }
    
    function exportReferrals() {
        console.log('Exporting referrals...');
        // In a real implementation, this would:
        // 1. Make an API call to get export data
        // 2. Convert to CSV/Excel
        // 3. Trigger download
        
        // Demo implementation (would need a proper export library in production)
        const table = document.querySelector('.referral-table');
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = [], cols = rows[i].querySelectorAll('td, th');
            
            for (let j = 0; j < cols.length; j++) {
                // Clean text of any commas or quotes
                const text = cols[j].textContent.replace(/"/g, '""').replace(/'/g, "''");
                row.push('"' + text + '"');
            }
            
            csv.push(row.join(','));
        }
        
        // Download CSV file
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'referrals_export.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Make functions available globally if needed
window.initReferralList = initReferralList;