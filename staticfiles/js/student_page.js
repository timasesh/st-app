// Ждем загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // JS для современных вкладок
    document.querySelectorAll('.nav-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.getAttribute('data-tab')).classList.add('active');
            
            // Если открыли вкладку уведомлений, маркируем все как прочитанные
            if (tab.getAttribute('data-tab') === 'notifications') {
                // Отправляем POST запрос для маркирования уведомлений как прочитанные
                const studentPageUrl = document.querySelector('meta[name="student-page-url"]').getAttribute('content');
                fetch(studentPageUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: 'mark_notifications_read=1'
                }).then(response => {
                    if (response.ok) {
                        // Убираем визуальные индикаторы непрочитанных уведомлений
                        document.querySelectorAll('.notification-card.unread').forEach(card => {
                            card.classList.remove('unread');
                        });
                        document.querySelectorAll('.unread-indicator').forEach(indicator => {
                            indicator.style.display = 'none';
                        });
                        // Убираем badge с количеством уведомлений
                        const badge = document.querySelector('.notification-badge');
                        if (badge) {
                            badge.style.display = 'none';
                        }
                    }
                }).catch(error => {
                    console.error('Ошибка при маркировании уведомлений:', error);
                });
            }
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
}); 