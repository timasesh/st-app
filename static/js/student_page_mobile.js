// student_page_mobile.js - Mobile-specific JavaScript for student page

document.addEventListener('DOMContentLoaded', function() {
    initializeMobileSpecificFeatures();
});

function initializeMobileSpecificFeatures() {
    // Mobile-specific functionality
    const mobileBackBtn = document.getElementById('mobileBackBtn');
    
    if (mobileBackBtn) {
        mobileBackBtn.addEventListener('click', function() {
            // Go back to previous page or home
            window.history.back();
        });
    }
    
    // Handle mobile sidebar
    handleMobileSidebar();
    
    // Handle mobile navigation
    handleMobileNavigation();
}

function handleMobileSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('studentSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (window.innerWidth <= 768) {
        if (sidebarToggle && sidebar && sidebarOverlay) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('open');
                sidebarOverlay.classList.toggle('active');
                document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
            });
            
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('active');
                document.body.style.overflow = '';
            });
        }
    }
}

function handleMobileNavigation() {
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    
    mobileNavItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all items
            mobileNavItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Navigate to the tab
            if (targetTab) {
                window.location.hash = targetTab;
            }
        });
    });
}

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        // Close mobile sidebar on desktop
        const sidebar = document.getElementById('studentSidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});
