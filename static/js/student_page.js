// student_page.js - JavaScript functionality for student page

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    initializeTabs();
    
    // Initialize sidebar
    initializeSidebar();
    
    // Initialize mobile navigation
    initializeMobileNav();
});

function initializeTabs() {
    // Tab switching functionality
    const navLinks = document.querySelectorAll('.nav-link[data-tab]');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and panes
            navLinks.forEach(l => l.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding pane
            this.classList.add('active');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
}

function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('studentSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (sidebarToggle && sidebar && sidebarOverlay) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            sidebarOverlay.classList.toggle('active');
        });
        
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
        });
    }
}

function initializeMobileNav() {
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    
    mobileNavItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all items
            mobileNavItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Switch to corresponding tab
            if (typeof switchTab === 'function') {
                switchTab(targetTab);
            }
        });
    });
}

// Tab switching function (global)
function switchTab(tabName) {
    // Hide all tab panes
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => pane.classList.remove('active'));
    
    // Remove active class from all nav links
    const navLinks = document.querySelectorAll('.nav-link, .sidebar-nav-link, .mobile-nav-item');
    navLinks.forEach(link => link.classList.remove('active'));
    
    // Show selected tab pane
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to selected nav link
    const selectedNavLink = document.querySelector(`[data-tab="${tabName}"], [href="#${tabName}"]`);
    if (selectedNavLink) {
        selectedNavLink.classList.add('active');
    }
    
    // Update mobile navigation
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    mobileNavItems.forEach(item => item.classList.remove('active'));
    
    const selectedMobileNav = document.querySelector(`[data-tab="${tabName}"]`);
    if (selectedMobileNav) {
        selectedMobileNav.classList.add('active');
    }
}
