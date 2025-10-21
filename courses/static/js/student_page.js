// Ждем загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Проверяем наличие элементов
    const navLinks = document.querySelectorAll('.sidebar-nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    
    // Проверяем сайдбар
    const sidebarElement = document.getElementById('studentSidebar');
    
    // JS для современных вкладок (обновленная версия)
    navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetTab = this.getAttribute('data-tab');
            if (!targetTab) return; // Пропускаем ссылки без data-tab
            
            // Используем глобальную функцию switchTab
            switchTab(targetTab);
        });
    });

    // Функция для обновления прогресс-баров звезд
    function updateStarsProgressBars() {
        document.querySelectorAll('.rating-group-card-modern').forEach(function(groupCard) {
            const progressBars = groupCard.querySelectorAll('.stars-progress-bar');
            let maxStars = 0;
            
            // Находим максимальное количество звезд в группе
            progressBars.forEach(function(bar) {
                const stars = parseInt(bar.getAttribute('data-stars')) || 0;
                if (stars > maxStars) {
                    maxStars = stars;
                }
            });
            
            // Устанавливаем ширину прогресс-баров
            progressBars.forEach(function(bar) {
                const stars = parseInt(bar.getAttribute('data-stars')) || 0;
                const percentage = maxStars > 0 ? (stars / maxStars) * 100 : 0;
                bar.style.width = percentage + '%';
            });
        });
    }

    // Функция для анимации круговых прогресс-баров курсов
    function initCourseProgressCircles() {
        document.querySelectorAll('.progress-circle').forEach(function(circle) {
            const progress = parseInt(circle.getAttribute('data-progress')) || 0;
            const progressRing = circle.querySelector('.progress-ring-circle');
            const circumference = 2 * Math.PI * 26; // r=26
            
            progressRing.style.strokeDasharray = circumference;
            progressRing.style.strokeDashoffset = circumference;
            
            // Анимация с задержкой
            setTimeout(function() {
                const offset = circumference - (progress / 100) * circumference;
                progressRing.style.strokeDashoffset = offset;
            }, 500);
        });
    }

    // Инициализируем функции
    updateStarsProgressBars();
    initCourseProgressCircles();
    
    // Инициализируем активную вкладку по умолчанию
    const defaultTab = 'home';
    const defaultLink = document.querySelector(`.sidebar-nav-link[data-tab="${defaultTab}"]`);
    const defaultPane = document.getElementById(defaultTab);
    
    
    // Убираем активный класс у всех вкладок и ссылок
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sidebar-nav-link').forEach(l => l.classList.remove('active'));
    
    if (defaultLink && defaultPane) {
        defaultLink.classList.add('active');
        defaultPane.classList.add('active');
        console.log('Инициализирована вкладка по умолчанию:', defaultTab);
        
        // Убеждаемся, что кнопка "Назад" скрыта на главной вкладке
        const mobileBackBtn = document.getElementById('mobileBackBtn');
        if (mobileBackBtn) {
            mobileBackBtn.classList.add('hidden');
        }
    } else {
        console.error('Не удалось инициализировать вкладку по умолчанию');
        // Если не удалось найти элементы, попробуем найти активную вкладку
        const activePane = document.querySelector('.tab-pane.active');
        if (activePane) {
            const activeTabName = activePane.id;
            const activeLink = document.querySelector(`.sidebar-nav-link[data-tab="${activeTabName}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
                console.log('Найдена активная вкладка:', activeTabName);
            }
        }
    }
    
    // Глобальная функция для переключения вкладок
    window.switchTab = function(tabName) {
        const navTabs = document.querySelectorAll('.sidebar-nav-link');
        const tabPanes = document.querySelectorAll('.tab-pane');
        const mobileBackBtn = document.getElementById('mobileBackBtn');
        
        // Убираем активный класс у всех ссылок
        navTabs.forEach(t => t.classList.remove('active'));
        
        // Добавляем активный класс к выбранной ссылке
        const targetLink = document.querySelector(`.sidebar-nav-link[data-tab="${tabName}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
        }
        
        // Убираем активный класс у всех вкладок
        tabPanes.forEach(p => p.classList.remove('active'));
        
        // Добавляем активный класс к выбранной вкладке
        const targetPane = document.getElementById(tabName);
        if (targetPane) {
            targetPane.classList.add('active');
            
            // Управляем кнопкой "Назад" на мобильных устройствах
            if (mobileBackBtn) {
                if (tabName === 'home') {
                    mobileBackBtn.classList.add('hidden');
                } else {
                    mobileBackBtn.classList.remove('hidden');
                }
            }
            
            // Плавная анимация появления
            targetPane.style.opacity = '0';
            targetPane.style.transform = 'translateY(20px)';
            
                         setTimeout(() => {
                 targetPane.style.transition = 'all 0.3s ease';
                 targetPane.style.opacity = '1';
                 targetPane.style.transform = 'translateY(0)';
                 
                 // Инициализируем обработчики уведомлений при переключении на вкладку уведомлений
                 if (tabName === 'notifications') {
                     setTimeout(() => {
                         initializeNotificationHandlers();
                     }, 100);
                 }
             }, 50);
        }
    };
    
    // Функциональность для показа полного текста сообщений
    document.querySelectorAll('.show-full-message').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const fullMessage = this.getAttribute('data-message');
            const messageElement = this.previousElementSibling;
            
            if (this.textContent.includes('Показать полностью')) {
                messageElement.textContent = fullMessage;
                this.innerHTML = '<i class="fas fa-compress me-1"></i>Свернуть';
            } else {
                // Обрезаем до 20 слов
                const words = fullMessage.split(' ');
                const truncated = words.slice(0, 20).join(' ') + (words.length > 20 ? '...' : '');
                messageElement.textContent = truncated;
                this.innerHTML = '<i class="fas fa-expand me-1"></i>Показать полностью';
            }
        });
    });
    
    // Функциональность сайдбара
    const sidebar = document.getElementById('studentSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.querySelector('.modern-student-main');
    
    // Переключение сайдбара
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('closed');
            if (mainContent) {
                mainContent.classList.toggle('sidebar-closed');
            }
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });
    }
    
    // Закрытие сайдбара при клике на оверлей
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.add('closed');
            if (mainContent) {
                mainContent.classList.add('sidebar-closed');
            }
            sidebarOverlay.classList.remove('active');
        });
    }
    
         // Dropdown функциональность
     const userDropdownBtn = document.getElementById('userDropdownBtn');
     const userDropdown = document.getElementById('userDropdown');
     
     // User dropdown
     if (userDropdownBtn && userDropdown) {
         userDropdownBtn.addEventListener('click', function(e) {
             e.stopPropagation();
             userDropdown.classList.toggle('show');
         });
     }
     
     // Закрытие dropdown'ов при клике вне их
     document.addEventListener('click', function(e) {
         if (!userDropdownBtn?.contains(e.target) && !userDropdown?.contains(e.target)) {
             userDropdown?.classList.remove('show');
         }
     });
    
         // Фильтрация домашних заданий
     const filterBtns = document.querySelectorAll('.filter-btn');
     const homeworkCards = document.querySelectorAll('.homework-card');
     
     filterBtns.forEach(btn => {
         btn.addEventListener('click', function() {
             const filter = this.getAttribute('data-filter');
             
             // Убираем активный класс у всех кнопок
             filterBtns.forEach(b => b.classList.remove('active'));
             
             // Добавляем активный класс к выбранной кнопке
             this.classList.add('active');
             
             // Фильтруем карточки
             homeworkCards.forEach(card => {
                 const status = card.getAttribute('data-status');
                 
                 if (filter === 'all' || status === filter) {
                     card.style.display = 'block';
                     card.style.opacity = '0';
                     setTimeout(() => {
                         card.style.opacity = '1';
                     }, 50);
                 } else {
                     card.style.opacity = '0';
                     setTimeout(() => {
                         card.style.display = 'none';
                     }, 300);
                 }
             });
         });
     });
     
     // Логика уведомлений
     const notificationFilterBtns = document.querySelectorAll('.notification-filter-btn');
     const notificationCards = document.querySelectorAll('.notification-card');
     const markAllReadBtn = document.getElementById('markAllReadBtn');
     const markReadBtns = document.querySelectorAll('.mark-read-btn');
     const deleteNotificationBtns = document.querySelectorAll('.delete-notification-btn');
     
     // Функция для инициализации обработчиков событий уведомлений
     function initializeNotificationHandlers() {
         // Обработчики для кнопок "отметить как прочитанное"
         document.querySelectorAll('.mark-read-btn').forEach(btn => {
             if (!btn.hasAttribute('data-initialized')) {
                 btn.setAttribute('data-initialized', 'true');
                 btn.addEventListener('click', function() {
                     const notificationId = this.getAttribute('data-notification-id');
                     const card = this.closest('.notification-card');
                     
                     fetch('/api/notifications/mark-read/', {
                         method: 'POST',
                         headers: {
                             'Content-Type': 'application/json',
                             'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                         },
                         body: JSON.stringify({ notification_id: notificationId })
                     })
                     .then(response => response.json())
                     .then(data => {
                         if (data.success) {
                             card.classList.remove('unread');
                             this.remove();
                             updateUnreadCount();
                         }
                     })
                     .catch(error => {
                         console.error('Ошибка при отметке уведомления как прочитанного:', error);
                     });
                 });
             }
         });
         
         // Обработчики для кнопок удаления
         document.querySelectorAll('.delete-notification-btn').forEach(btn => {
             if (!btn.hasAttribute('data-initialized')) {
                 btn.setAttribute('data-initialized', 'true');
                 btn.addEventListener('click', function() {
                     const notificationId = this.getAttribute('data-notification-id');
                     const card = this.closest('.notification-card');
                     
                     if (confirm('Вы уверены, что хотите удалить это уведомление?')) {
                         fetch('/api/notifications/delete/', {
                             method: 'POST',
                             headers: {
                                 'Content-Type': 'application/json',
                                 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                             },
                             body: JSON.stringify({ notification_id: notificationId })
                         })
                         .then(response => response.json())
                         .then(data => {
                             if (data.success) {
                                 card.style.opacity = '0';
                                 setTimeout(() => {
                                     card.remove();
                                     updateUnreadCount();
                                 }, 300);
                             }
                         })
                         .catch(error => {
                             console.error('Ошибка при удалении уведомления:', error);
                         });
                     }
                 });
             }
         });
     }
     
     // Инициализируем обработчики при загрузке страницы
     initializeNotificationHandlers();
     
     // Обработчик для кнопки "Загрузить еще" уведомлений
     const loadMoreNotificationsBtn = document.getElementById('loadMoreNotifications');
     if (loadMoreNotificationsBtn) {
         loadMoreNotificationsBtn.addEventListener('click', function() {
             // После загрузки новых уведомлений переинициализируем обработчики
             setTimeout(() => {
                 initializeNotificationHandlers();
             }, 100);
         });
     }
     
     // Фильтрация уведомлений
     notificationFilterBtns.forEach(btn => {
         btn.addEventListener('click', function() {
             const filter = this.getAttribute('data-filter');
             
             // Убираем активный класс у всех кнопок
             notificationFilterBtns.forEach(b => b.classList.remove('active'));
             
             // Добавляем активный класс к выбранной кнопке
             this.classList.add('active');
             
             // Фильтруем уведомления
             notificationCards.forEach(card => {
                 const isUnread = card.classList.contains('unread');
                 
                 if (filter === 'all' || 
                     (filter === 'unread' && isUnread) || 
                     (filter === 'read' && !isUnread)) {
                     card.style.display = 'flex';
                     card.style.opacity = '0';
                     setTimeout(() => {
                         card.style.opacity = '1';
                     }, 50);
                 } else {
                     card.style.opacity = '0';
                     setTimeout(() => {
                         card.style.display = 'none';
                     }, 300);
                 }
             });
         });
     });
     
     // Отметить все как прочитанные
     if (markAllReadBtn) {
         markAllReadBtn.addEventListener('click', function() {
             // Отправляем запрос на сервер для отметки всех уведомлений как прочитанных
             fetch('/api/notifications/mark-all-read/', {
                 method: 'POST',
                 headers: {
                     'Content-Type': 'application/json',
                     'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                 }
             })
             .then(response => response.json())
             .then(data => {
                 if (data.success) {
                     // Обновляем все непрочитанные карточки
                     const unreadCards = document.querySelectorAll('.notification-card.unread');
                     unreadCards.forEach(card => {
                         card.classList.remove('unread');
                         
                         // Убираем кнопку "отметить как прочитанное"
                         const markReadBtn = card.querySelector('.mark-read-btn');
                         if (markReadBtn) {
                             markReadBtn.remove();
                         }
                     });
                     
                     // Обновляем счетчик непрочитанных
                     updateUnreadCount();
                     
                     // Скрываем кнопку "отметить все как прочитанные"
                     this.style.display = 'none';
                 }
             })
             .catch(error => {
                 console.error('Ошибка при отметке всех уведомлений как прочитанных:', error);
             });
         });
     }
     
     // Отметить отдельное уведомление как прочитанное
     markReadBtns.forEach(btn => {
         btn.addEventListener('click', function() {
             const notificationId = this.getAttribute('data-notification-id');
             const card = this.closest('.notification-card');
             
             fetch('/api/notifications/mark-read/', {
                 method: 'POST',
                 headers: {
                     'Content-Type': 'application/json',
                     'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                 },
                 body: JSON.stringify({ notification_id: notificationId })
             })
             .then(response => response.json())
             .then(data => {
                 if (data.success) {
                     card.classList.remove('unread');
                     this.remove();
                     updateUnreadCount();
                 }
             })
             .catch(error => {
                 console.error('Ошибка при отметке уведомления как прочитанного:', error);
             });
         });
     });
     
     // Удалить уведомление
     deleteNotificationBtns.forEach(btn => {
         btn.addEventListener('click', function() {
             const notificationId = this.getAttribute('data-notification-id');
             const card = this.closest('.notification-card');
             
             if (confirm('Вы уверены, что хотите удалить это уведомление?')) {
                 fetch('/api/notifications/delete/', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                         'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                     },
                     body: JSON.stringify({ notification_id: notificationId })
                 })
                 .then(response => response.json())
                 .then(data => {
                     if (data.success) {
                         card.style.opacity = '0';
                         setTimeout(() => {
                             card.remove();
                             updateUnreadCount();
                         }, 300);
                     }
                 })
                 .catch(error => {
                     console.error('Ошибка при удалении уведомления:', error);
                 });
             }
         });
     });
     
     // Функция обновления счетчика непрочитанных уведомлений
     function updateUnreadCount() {
         const unreadCards = document.querySelectorAll('.notification-card.unread');
         const unreadCount = unreadCards.length;
         
         // Обновляем бейдж в сайдбаре
         const sidebarBadge = document.querySelector('.sidebar-notification-badge');
         if (sidebarBadge) {
             if (unreadCount > 0) {
                 sidebarBadge.textContent = unreadCount;
                 sidebarBadge.style.display = 'flex';
             } else {
                 sidebarBadge.style.display = 'none';
             }
         }
         
         // Обновляем бейдж в фильтре
         const filterBadge = document.querySelector('.unread-badge');
         if (filterBadge) {
             if (unreadCount > 0) {
                 filterBadge.textContent = unreadCount;
                 filterBadge.style.display = 'flex';
             } else {
                 filterBadge.style.display = 'none';
             }
         }
         

         
         // Скрываем кнопку "отметить все как прочитанные" если нет непрочитанных
         if (unreadCount === 0) {
             const markAllReadBtn = document.getElementById('markAllReadBtn');
             if (markAllReadBtn) {
                 markAllReadBtn.style.display = 'none';
             }
         } else {
             // Показываем кнопку если есть непрочитанные уведомления
             const markAllReadBtn = document.getElementById('markAllReadBtn');
             if (markAllReadBtn) {
                 markAllReadBtn.style.display = 'inline-flex';
             }
         }
     }
     
     // Автоматически открываем вкладку "Главная" по умолчанию
     setTimeout(() => {
         if (typeof switchTab === 'function') {
             switchTab('home');
         }
     }, 100);
}); 