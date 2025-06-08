document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const searchBtn = document.getElementById('search-btn');
    const scanBtn = document.getElementById('scan-btn');
    const referralIdInput = document.getElementById('referral-id');
    const statusContainer = document.getElementById('status-container');
    const notFoundContainer = document.getElementById('not-found');
    const qrModal = document.getElementById('qr-modal');
    const closeModal = document.querySelector('.close-modal');
    const enterManually = document.getElementById('enter-manually');
    const retryBtn = document.querySelector('.btn-retry');
    const detailsBtn = document.querySelector('.btn-details');
    const contactBtn = document.querySelector('.btn-contact');

    // Sample referral data (replace with actual API calls)
    const sampleReferral = {
        id: "REF-2023-001",
        status: "in_transit",
        patient: {
            name: "Jean Uwimana",
            age: 32,
            gender: "Male",
            condition: "Severe Malaria"
        },
        timeline: [
            {
                event: "Referral Created",
                timestamp: "2023-05-15T09:30:00",
                location: "Ruhango Health Center",
                completed: true
            },
            {
                event: "In Transit",
                timestamp: "2023-05-15T10:45:00",
                details: "Ambulance: RHA-789",
                completed: true,
                active: true
            },
            {
                event: "Received at Facility",
                timestamp: "2023-05-15T12:30:00",
                location: "CHUK Hospital",
                completed: false
            }
        ]
    };

    // Status colors and text
    const statusMap = {
        pending: { text: "Pending", color: "#e67e22" },
        in_transit: { text: "In Transit", color: "#3498db" },
        completed: { text: "Completed", color: "#2ecc71" },
        cancelled: { text: "Cancelled", color: "#e74c3c" }
    };

    // Initialize the page
    function init() {
        setupEventListeners();
    }

    // Set up event listeners
    function setupEventListeners() {
        // Search button click
        searchBtn.addEventListener('click', handleSearch);
        
        // Enter key in search input
        referralIdInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
        
        // Scan QR button
        scanBtn.addEventListener('click', openQRScanner);
        
        // Close modal button
        closeModal.addEventListener('click', closeQRScanner);
        
        // Enter manually link
        enterManually.addEventListener('click', function(e) {
            e.preventDefault();
            closeQRScanner();
            referralIdInput.focus();
        });
        
        // Retry button
        retryBtn.addEventListener('click', function() {
            notFoundContainer.style.display = 'none';
            referralIdInput.value = '';
            referralIdInput.focus();
        });
        
        // View details button
        if (detailsBtn) {
            detailsBtn.addEventListener('click', function() {
                viewFullDetails(sampleReferral.id);
            });
        }
        
        // Contact facility button
        if (contactBtn) {
            contactBtn.addEventListener('click', contactFacility);
        }
    }

    // Handle search functionality
    function handleSearch() {
        const referralId = referralIdInput.value.trim();
        
        if (!referralId) {
            alert('Please enter a referral ID');
            return;
        }
        
        // In a real app, this would be an API call
        if (referralId === sampleReferral.id) {
            displayReferralStatus(sampleReferral);
        } else {
            showNotFound();
        }
    }

    // Display referral status
    function displayReferralStatus(referral) {
        // Update status text and color
        const statusInfo = statusMap[referral.status];
        const statusText = document.getElementById('status-text');
        statusText.textContent = statusInfo.text;
        statusText.style.color = statusInfo.color;
        
        // Update referral ID
        document.getElementById('display-id').textContent = referral.id;
        
        // Update patient info
        document.getElementById('patient-name').textContent = referral.patient.name;
        document.getElementById('patient-age').textContent = referral.patient.age;
        document.getElementById('patient-gender').textContent = referral.patient.gender;
        document.getElementById('patient-condition').textContent = referral.patient.condition;
        
        // Show the status container
        statusContainer.style.display = 'block';
        notFoundContainer.style.display = 'none';
    }

    // Show not found message
    function showNotFound() {
        statusContainer.style.display = 'none';
        notFoundContainer.style.display = 'block';
    }

    // Open QR scanner modal
    function openQRScanner() {
        qrModal.style.display = 'flex';
        
        // In a real app, you would initialize a QR scanner here
        console.log('QR scanner initialized');
    }

    // Close QR scanner modal
    function closeQRScanner() {
        qrModal.style.display = 'none';
    }

    // View full details (would redirect in real app)
    function viewFullDetails(referralId) {
        console.log('Viewing full details for:', referralId);
        // window.location.href = `/referrals/${referralId}/`;
    }

    // Contact facility
    function contactFacility() {
        console.log('Contacting facility...');
        // This could open a phone link or contact modal
    }

    // Initialize the page
    init();
});

