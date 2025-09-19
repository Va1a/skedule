// Enhanced button interactions for auth modals
document.addEventListener('DOMContentLoaded', function() {
  const authButton = document.querySelector('.btn-auth');
  const authForm = document.querySelector('form');
  const inputs = document.querySelectorAll('.form-floating input');
  
  if (!authButton || !authForm) return;
  
  // Button loading state
  authForm.addEventListener('submit', function() {
    const isLogin = authButton.textContent.includes('Log In');
    const loadingText = isLogin ? 'Signing in...' : 'Creating account...';
    authButton.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>${loadingText}`;
    authButton.disabled = true;
  });
  
  // Input focus effects
  inputs.forEach(input => {
    input.addEventListener('focus', function() {
      this.parentElement.style.transform = 'scale(1.02)';
    });
    
    input.addEventListener('blur', function() {
      this.parentElement.style.transform = 'scale(1)';
    });
    
    // Remove error styling on input
    input.addEventListener('input', function() {
      if (this.classList.contains('is-invalid')) {
        this.classList.remove('is-invalid');
        const feedback = this.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
          feedback.style.display = 'none';
        }
      }
    });
    
    // Enter key handling
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        authForm.submit();
      }
    });
  });
  
  // Button ripple effect
  authButton.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    this.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  });
  
  // Auto-focus first input (now name input since external_id was removed)
  if (inputs.length > 0) {
    inputs[0].focus();
  }
});