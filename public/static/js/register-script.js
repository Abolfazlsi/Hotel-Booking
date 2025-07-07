let accountIcon = document.querySelector(".user-account")
accountIcon.addEventListener(("mouseenter"), () => {
    accountIcon.innerHTML = ""
    accountIcon.innerHTML = "<div class='signup-text'><p>ثبت نام / ورود</p></div>"

})

accountIcon.addEventListener("mouseleave", () => {
    accountIcon.innerHTML = ""
    accountIcon.innerHTML = '<i class="fa fa-user"></i>'
})


// Add floating animation to form elements
const formInputs = document.querySelectorAll('.form-control');
formInputs.forEach(input => {
    input.addEventListener('focus', function () {
        this.parentElement.style.transform = 'translateY(-2px)';
        this.parentElement.style.transition = 'transform 0.3s ease';
    });

    input.addEventListener('blur', function () {
        this.parentElement.style.transform = 'translateY(0)';
    });
});