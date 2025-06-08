// Table actions
function openViewModal(event, adminId) {
    event.preventDefault();
    // Add your view modal logic here
    console.log('Viewing admin:', adminId);
}

function openEditModal(event, adminId) {
    event.preventDefault();
    // Add your edit modal logic here
    console.log('Editing admin:', adminId);
}

function confirmDelete(adminId, username, event) {
    event.preventDefault();
    if (confirm(`Are you sure you want to delete user ${username}? This action cannot be undone.`)) {
        // Add your delete logic here
        console.log('Deleting admin:', adminId);
    }
}

function updateTableRow(userId, data) {
    const row = document.querySelector(`tr[data-id="${userId}"]`);
    if (row) {
        const cells = row.cells;
        
        // Update each cell with new data
        cells[2].textContent = data.first_name;
        cells[3].textContent = data.last_name;
        cells[4].textContent = data.email;
        cells[5].textContent = data.phone;
        cells[6].textContent = data.address;
        cells[7].textContent = data.date_of_birth;
        cells[8].textContent = data.gender;
        cells[9].textContent = data.role;
        cells[10].textContent = data.license_number;
        
        // Update status badge
        const statusCell = cells[11];
        const badge = statusCell.querySelector('.badge');
        if (badge) {
            badge.className = `badge ${data.is_active ? 'badge-success' : 'badge-danger'}`;
            badge.textContent = data.is_active ? 'Active' : 'Inactive';
        }
    }
}

// Add this function to check if user data exists
function checkUserData() {
    const debugDiv = document.getElementById('debug-info');
    const debugData = document.getElementById('debug-data');
    
    // Get all user data from the table
    const users = [];
    document.querySelectorAll('tr[data-id]').forEach(row => {
        const user = {
            id: row.dataset.id,
            email: row.querySelector('td:nth-child(4)').textContent,
            firstName: row.querySelector('td:nth-child(2)').textContent,
            lastName: row.querySelector('td:nth-child(3)').textContent,
            role: row.querySelector('td:nth-child(9)').textContent,
            status: row.querySelector('td:nth-child(11)').textContent.trim()
        };
        users.push(user);
    });
    
    if (users.length > 0) {
        debugData.textContent = JSON.stringify(users, null, 2);
        debugDiv.style.display = 'block';
    }
}

// Function to format modal content
function formatModalContent(details) {
    return `
        <div class="modal-section">
            <h3>Personal Information</h3>
            <p><strong>First Name:</strong> ${details.firstName}</p>
            <p><strong>Last Name:</strong> ${details.lastName}</p>
            <p><strong>Email:</strong> ${details.email}</p>
            <p><strong>Phone:</strong> ${details.phone}</p>
            <p><strong>Address:</strong> ${details.address}</p>
            <p><strong>Date of Birth:</strong> ${details.dateOfBirth}</p>
            <p><strong>Gender:</strong> ${details.gender}</p>
        </div>
        
        <div class="modal-section">
            <h3>Account Information</h3>
            <p><strong>Role:</strong> ${details.role}</p>
            <p><strong>Status:</strong> ${details.status}</p>
            <p><strong>License Number:</strong> ${details.licenseNumber}</p>
        </div>
    `;
}

// Save user changes
function saveUserChanges() {
    const form = document.getElementById('editForm');
    if (!form) {
        showAlert('error', 'Form not found');
        return;
    }

    const formData = new FormData(form);
    
    // Get CSRF token from the form
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    if (!csrfToken) {
        showAlert('error', 'CSRF token not found');
        return;
    }

    // Get user ID
    const userId = formData.get('id');
    if (!userId) {
        showAlert('error', 'User ID not found');
        return;
    }

    // Validate required fields
    const requiredFields = ['first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth', 'gender', 'role'];
    let hasError = false;
    
    for (const field of requiredFields) {
        const value = formData.get(field);
        if (!value || value.trim() === '') {
            showAlert('error', `Please fill in all required fields`);
            hasError = true;
            break;
        }
    }
    
    if (hasError) return;

    // Validate date format
    const dateOfBirth = formData.get('date_of_birth');
    if (dateOfBirth) {
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(dateOfBirth)) {
            showAlert('error', 'Date of birth must be in YYYY-MM-DD format');
            return;
        }
    }

    // Add CSRF token to form data
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Submit form data
    fetch('/manage_hospital/update_user/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Show success message
            showAlert('success', `User updated successfully`);
            
            // Close the modal
            closeModal('editModal');
            
            // Redirect to admin details page
            setTimeout(() => {
                window.location.href = '/manage_hospital/admin_details/';
            }, 1000);
        } else {
            showAlert('error', data.message || 'Failed to update user');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('error', 'Error updating user: ' + error.message);
    });
}

// Add event listener for form submission
if (document.getElementById('editForm')) {
    document.getElementById('editForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveUserChanges();
    });
}

// Function to show alert messages
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Add to a specific container or the body
    document.body.appendChild(alertDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// Add event listeners for table actions
function initializeTableActions() {
    // Add any additional table initialization code here
    console.log('Table actions initialized');
    
    // Add click handlers for action buttons
    document.querySelectorAll('.btn-view').forEach(button => {
        button.addEventListener('click', function(e) {
            const adminId = this.closest('tr').dataset.id;
            openViewModal(e, adminId);
        });
    });
    
    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', function(e) {
            const adminId = this.closest('tr').dataset.id;
            openEditModal(e, adminId);
        });
    });
    
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(e) {
            const adminId = this.closest('tr').dataset.id;
            const email = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            confirmDelete(adminId, email, e);
        });
    });
}
