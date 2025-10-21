// Мобильная навигация для student_page

document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, является ли устройство мобильным
    const isMobile = window.innerWidth <= 768;
    
    
    if (isMobile) {
        initializeMobileNavigation();
    }
    
    // Обработчик изменения размера окна
    window.addEventListener('resize', function() {
        const newIsMobile = window.innerWidth <= 768;
        if (newIsMobile !== isMobile) {
            location.reload(); // Перезагружаем страницу при изменении типа устройства
        }
    });
});

// Функция переключения вкладок для мобильных устройств
function switchTab(tabName) {
    // Используем глобальную функцию switchTab из основного файла
    if (window.switchTab) {
        window.switchTab(tabName);
    }
    
    // Прокручиваем к началу контента
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    // Добавляем тактильную обратную связь на мобильных
    if ('vibrate' in navigator) {
        navigator.vibrate(50);
    }
}

function initializeMobileNavigation() {
    // Улучшенная обработка карточек на мобильных
    const cards = document.querySelectorAll('.course-card-modern, .rating-card, .quiz-card, .request-card');
    
    cards.forEach(card => {
        card.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        card.addEventListener('touchend', function() {
            this.style.transform = '';
        });
    });
    
    // Оптимизация производительности для мобильных
    let ticking = false;
    
    function updateOnScroll() {
        // Здесь можно добавить дополнительные оптимизации при скролле
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateOnScroll);
            ticking = true;
        }
    });
    
    // Добавляем поддержку pull-to-refresh (базовая версия)
    let pullStartY = 0;
    let pullDistance = 0;
    const pullThreshold = 100;
    
    document.addEventListener('touchstart', function(e) {
        if (window.scrollY === 0) {
            pullStartY = e.touches[0].clientY;
        }
    });
    
    document.addEventListener('touchmove', function(e) {
        if (window.scrollY === 0 && pullStartY > 0) {
            pullDistance = e.touches[0].clientY - pullStartY;
            
            if (pullDistance > 0) {
                e.preventDefault();
                
                // Добавляем визуальный эффект pull-to-refresh
                const mainContent = document.querySelector('.main-content');
                if (mainContent) {
                    mainContent.style.transform = `translateY(${Math.min(pullDistance * 0.5, 50)}px)`;
                }
            }
        }
    });
    
    document.addEventListener('touchend', function() {
        if (pullDistance > pullThreshold) {
            // Обновляем страницу при достаточном pull
            location.reload();
        } else {
            // Возвращаем в исходное положение
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.style.transform = '';
            }
        }
        
        pullStartY = 0;
        pullDistance = 0;
    });
}

// Функция для определения типа устройства
function getDeviceType() {
    const ua = navigator.userAgent;
    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
        return 'tablet';
    }
    if (/mobile|android|iphone|ipod|blackberry|opera mini|iemobile/i.test(ua)) {
        return 'mobile';
    }
    return 'desktop';
}

// Функция для оптимизации изображений на мобильных
function optimizeImagesForMobile() {
    if (getDeviceType() === 'mobile') {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // Добавляем lazy loading для изображений
            img.loading = 'lazy';
            
            // Оптимизируем размеры изображений
            if (img.width > 300) {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            }
        });
    }
}

// Инициализация оптимизации изображений
document.addEventListener('DOMContentLoaded', optimizeImagesForMobile);

// Функция инициализации сайдбара
function initializeSidebar() {
    const sidebar = document.getElementById('studentSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (!sidebar || !sidebarToggle) return;
    
    // Обработчик открытия/закрытия сайдбара
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('closed');
        if (sidebarOverlay) {
            sidebarOverlay.classList.toggle('active');
        }
    });
    
    // Обработчик закрытия сайдбара по клику на оверлей
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.add('closed');
            this.classList.remove('active');
        });
    }
    
    // Обработчик закрытия сайдбара по клику на ссылки навигации (на мобильных)
    const navLinks = document.querySelectorAll('.sidebar-nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.add('closed');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
            }
        });
    });
}

// Инициализация сайдбара
document.addEventListener('DOMContentLoaded', initializeSidebar);
