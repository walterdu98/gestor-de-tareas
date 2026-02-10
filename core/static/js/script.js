const trabajosBtn = document.getElementById('trabajos-btn');
const MobileMenu=document.getElementById('mobile-menu');
const userMenuButton = document.getElementById('user-menu-button');
const userMenuDropdown = document.getElementById('user-menu-dropdown');

if(trabajosBtn && MobileMenu){
    trabajosBtn.addEventListener('click', () => {
        MobileMenu.classList.toggle('hidden');
    });
}

if(userMenuButton && userMenuDropdown){
    userMenuButton.addEventListener('click', (event) => {
        event.stopPropagation();
        userMenuDropdown.classList.toggle('hidden');
    });
}

document.addEventListener('click', (event) => {
    if(userMenuDropdown &&userMenuButton) {
        if (!userMenuButton.contains(event.target) && !userMenuDropdown.contains(event.target)) {
            userMenuDropdown.classList.add('hidden');
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (userMenuDropdown) {
        userMenuDropdown.classList.add('hidden');
    }
});
