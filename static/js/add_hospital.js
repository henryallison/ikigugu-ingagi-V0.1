document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('hospitalForm');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const passwordStrength = document.querySelector('.password-strength');
    const passwordMatch = document.querySelector('.password-match');
    
    // Password strength checker
    password.addEventListener('input', function() {
        const value = password.value;
        let strength = 0;
        
        // Check length
        if (value.length >= 8) strength++;
        
        // Check for numbers
        if (/\d/.test(value)) strength++;
        
        // Check for special characters
        if (/[!@#$%^&*(),.?":{}|<>]/.test(value)) strength++;
        
        // Check for uppercase and lowercase
        if (/[a-z]/.test(value) && /[A-Z]/.test(value)) strength++;
        
        // Update strength indicator
        passwordStrength.className = 'password-strength';
        if (value.length > 0) {
            if (strength < 2) {
                passwordStrength.classList.add('weak');
            } else if (strength < 4) {
                passwordStrength.classList.add('medium');
            } else {
                passwordStrength.classList.add('strong');
            }
        }
    });
    
    // Password match checker
    confirmPassword.addEventListener('input', function() {
        passwordMatch.className = 'password-match';
        if (confirmPassword.value.length > 0) {
            if (confirmPassword.value === password.value) {
                passwordMatch.classList.add('valid');
            } else {
                passwordMatch.classList.add('invalid');
            }
        }
    });
    
    // Form submission validation
    form.addEventListener('submit', function(e) {
        // Check password match
        if (password.value !== confirmPassword.value) {
            e.preventDefault();
            alert('Passwords do not match!');
            return;
        }
        
        // Check password strength
        if (password.value.length < 8 || 
            !/\d/.test(password.value) || 
            !/[!@#$%^&*(),.?":{}|<>]/.test(password.value) ||
            !/[a-z]/.test(password.value) || 
            !/[A-Z]/.test(password.value)) {
            e.preventDefault();
            alert('Password must be at least 8 characters long and contain a mix of uppercase, lowercase, numbers, and special characters!');
            return;
        }
    });
    
    // Phone number format validation
    const phone = document.getElementById('phone');
    phone.addEventListener('blur', function() {
        if (!phone.value.startsWith('+250')) {
            phone.setCustomValidity('Phone number must start with +250');
        } else {
            phone.setCustomValidity('');
        }
    });
});

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