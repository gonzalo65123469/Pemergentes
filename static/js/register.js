// Función para alternar la visibilidad de la contraseña
function togglePasswordVisibility(id) {
    const passwordInput = document.getElementById(id);
    const eyeIcon = passwordInput.nextElementSibling;

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    } else {
        passwordInput.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
}

// Función para validar las contraseñas antes de enviar el formulario
function validatePasswords() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    if (password !== confirmPassword) {
        document.getElementById('error-message').style.display = 'block'; // Mostrar el mensaje de error
        return false; // Evitar el envío del formulario
    } else {
        document.getElementById('error-message').style.display = 'none'; // Ocultar el mensaje de error
        return true; // Permitir el envío del formulario
    }
}
