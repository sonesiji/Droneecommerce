// Form validation functions
function validatePhoneNumber(value) {
    const phoneRegex = /^\+?1?\d{9,15}$/;
    if (!phoneRegex.test(value)) {
        showAlert('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.');
        return false;
    }
    return true;
}

function validatePassword(value) {
    if (value.length < 8) {
        showAlert('Password must be at least 8 characters long.');
        return false;
    }
    if (!/\d/.test(value)) {
        showAlert('Password must contain at least one digit.');
        return false;
    }
    if (!/[A-Z]/.test(value)) {
        showAlert('Password must contain at least one uppercase letter.');
        return false;
    }
    return true;
}

function validateRPCNumber(value) {
    const rpcRegex = /^RPC-\d{6}$/;
    if (!rpcRegex.test(value)) {
        showAlert('RPC number must be in the format RPC-XXXXXX where X is a digit.');
        return false;
    }
    return true;
}

function validateFutureDate(value) {
    const selectedDate = new Date(value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
        showAlert('Date cannot be in the past.');
        return false;
    }
    return true;
}

function validateBusinessHours(value) {
    const time = new Date(`1970-01-01T${value}`);
    const hours = time.getHours();
    const minutes = time.getMinutes();
    
    if (hours < 9 || (hours === 17 && minutes > 0) || hours > 17) {
        showAlert('Booking time must be between 9:00 AM and 5:00 PM.');
        return false;
    }
    return true;
}

// Show alert using SweetAlert2
function showAlert(message) {
    Swal.fire({
        title: 'Validation Error',
        text: message,
        icon: 'error',
        confirmButtonText: 'OK',
        customClass: {
            confirmButton: 'btn btn-primary'
        }
    });
}

// Form submission handler
document.addEventListener('DOMContentLoaded', function() {
    const instructorForm = document.getElementById('instructor-form');
    if (instructorForm) {
        instructorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            let isValid = true;

            // Validate all fields
            if (!validatePhoneNumber(formData.get('phone_number'))) isValid = false;
            if (formData.get('password') && !validatePassword(formData.get('password'))) isValid = false;
            if (!validateRPCNumber(formData.get('rpc_number'))) isValid = false;
            if (!validateFutureDate(formData.get('issued_date'))) isValid = false;

            // If all validations pass, submit the form
            if (isValid) {
                this.submit();
            }
        });
    }
});
