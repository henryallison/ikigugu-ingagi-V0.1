document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const printBtn = document.querySelector('.btn-print');
    const contactBtn = document.querySelector('.btn-contact');
    const backBtn = document.querySelector('.btn-back');
    
    // Initialize the page
    function init() {
        setupEventListeners();
        // In a real app, you would fetch the referral data here
        // fetchReferralDetails();
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // Print button
        if (printBtn) {
            printBtn.addEventListener('click', printReferral);
        }
        
        // Contact facility button
        if (contactBtn) {
            contactBtn.addEventListener('click', contactFacility);
        }
        
        // Back button
        if (backBtn) {
            backBtn.addEventListener('click', goBackToList);
        }
    }
    
    // Print referral function
    function printReferral() {
        console.log('Printing referral...');
        // In a real app, this would open the print dialog
        // window.print();
        
        // For demo purposes, show an alert
        alert('Print functionality would open the print dialog in a real application');
    }
    
    // Contact facility function
    function contactFacility() {
        console.log('Contacting facility...');
        // This could open a phone link or contact modal
        alert('This would initiate contact with the receiving facility in a real application');
    }
    
    // Go back to referral list
    function goBackToList() {
        console.log('Going back to referral list...');
        // In a real app, this would navigate back
        // window.location.href = '/referrals/';
        
        // For demo purposes, show an alert
        alert('This would navigate back to the referral list in a real application');
    }
    
    // Fetch referral details (example)
    function fetchReferralDetails() {
        // In a real app, you would make an API call here
        // const referralId = window.location.pathname.split('/').pop();
        // fetch(`/api/referrals/${referralId}/`)
        //     .then(response => response.json())
        //     .then(data => updateUI(data))
        //     .catch(error => console.error('Error:', error));
        
        console.log('Fetching referral details...');
    }
    
    // Update UI with referral data (example)
    function updateUI(data) {
        // This function would update the page with the fetched data
        console.log('Updating UI with:', data);
    }
    
    // Initialize the page
    init();
});