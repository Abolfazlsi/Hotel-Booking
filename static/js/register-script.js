        // Form validation and submission
        document.getElementById('registrationForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = this.querySelector('input[type="email"]').value;
            const password = this.querySelector('input[type="password"]').value;
            const termsAccepted = this.querySelector('#termsCheck').checked;
            
            // Basic validation
            if (!email || !password) {
                alert('لطفاً تمام فیلدها را پر کنید.');
                return;
            }
            
            if (!termsAccepted) {
                alert('لطفاً شرایط خدمات را بپذیرید.');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('لطفاً یک آدرس ایمیل معتبر وارد کنید.');
                return;
            }
            
            // Password validation
            if (password.length < 6) {
                alert('گذرواژه باید حداقل ۶ کاراکتر باشد.');
                return;
            }
            
            // Simulate registration process
            const submitBtn = this.querySelector('.btn-register');
            const originalText = submitBtn.textContent;
            
            submitBtn.textContent = 'در حال پردازش...';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                alert('ثبت نام با موفقیت انجام شد!');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                this.reset();
            }, 2000);
        });
        
        // Login link handler
        document.getElementById('loginLink').addEventListener('click', function(e) {
            e.preventDefault();
            alert('انتقال به صفحه ورود...');
        });
        
        // Add floating animation to form elements
        const formInputs = document.querySelectorAll('.form-control');
        formInputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.style.transform = 'translateY(-2px)';
                this.parentElement.style.transition = 'transform 0.3s ease';
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.style.transform = 'translateY(0)';
            });
        });
        
        // Add ripple effect to button
        document.querySelector('.btn-register').addEventListener('click', function(e) {
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