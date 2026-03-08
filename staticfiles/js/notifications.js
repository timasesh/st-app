// notifications.js - Real-time notifications system

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.eventSource = null;
        this.init();
    }

    init() {
        // Check if user is authenticated
        if (typeof userId !== 'undefined' && userType === 'student') {
            this.connectToNotifications();
        }
    }

    connectToNotifications() {
        // Using Server-Sent Events for real-time notifications
        this.eventSource = new EventSource(`/notifications/stream/${userId}/`);

        this.eventSource.onopen = (event) => {
            console.log('Connected to notification stream');
        };

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleNewNotification(data);
        };

        this.eventSource.onerror = (event) => {
            console.error('Notification stream error:', event);
            // Reconnect after 5 seconds
            setTimeout(() => {
                this.connectToNotifications();
            }, 5000);
        };
    }

    handleNewNotification(notification) {
        // Add to notifications list
        this.notifications.unshift(notification);
        
        // Show browser notification if permission granted
        this.showBrowserNotification(notification);
        
        // Update UI
        this.updateNotificationBadge();
        this.updateNotificationList(notification);
        
        // Play sound (optional)
        this.playNotificationSound();
    }

    showBrowserNotification(notification) {
        // Check if browser supports notifications and permission is granted
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotification = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/Study_Task.png',
                badge: '/static/images/Study_Task.png',
                tag: notification.id,
                requireInteraction: true,
                actions: [
                    {
                        action: 'view',
                        title: 'Посмотреть'
                    },
                    {
                        action: 'dismiss',
                        title: 'Закрыть'
                    }
                ]
            });

            browserNotification.onclick = () => {
                window.focus();
                this.handleNotificationClick(notification);
                browserNotification.close();
            };

            browserNotification.onshow = () => {
                // Auto-close after 10 seconds
                setTimeout(() => {
                    browserNotification.close();
                }, 10000);
            };

            browserNotification.onaction = (event) => {
                if (event.action === 'view') {
                    this.handleNotificationClick(notification);
                }
                browserNotification.close();
            };
        }
    }

    handleNotificationClick(notification) {
        // Navigate to relevant page based on notification type
        switch (notification.type) {
            case 'quiz_assigned':
                window.location.href = '/student/quizzes/';
                break;
            case 'homework_assigned':
                window.location.href = '/student/homework/';
                break;
            case 'general':
            default:
                window.location.href = '/student/#notifications';
                break;
        }
    }

    updateNotificationBadge() {
        const badge = document.querySelector('.sidebar-notification-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            badge.textContent = currentCount + 1;
            badge.style.display = 'inline-block';
        }
    }

    updateNotificationList(notification) {
        const notificationsList = document.getElementById('notificationsList');
        if (notificationsList) {
            const notificationElement = this.createNotificationElement(notification);
            notificationsList.insertBefore(notificationElement, notificationsList.firstChild);
        }
    }

    createNotificationElement(notification) {
        const div = document.createElement('div');
        div.className = 'notification-item';
        div.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${this.formatTime(notification.created_at)}</div>
            </div>
            <div class="notification-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="notificationSystem.markAsRead(${notification.id})">
                    Прочитано
                </button>
            </div>
        `;
        return div;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds

        if (diff < 60) return 'только что';
        if (diff < 3600) return `${Math.floor(diff / 60)} мин. назад`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} ч. назад`;
        return date.toLocaleDateString('ru-RU');
    }

    playNotificationSound() {
        // Create and play notification sound
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Could not play sound:', e));
        } catch (e) {
            console.log('Sound file not available:', e);
        }
    }

    markAsRead(notificationId) {
        fetch(`/notifications/mark-read/${notificationId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationElement) {
                    notificationElement.classList.add('read');
                }
                this.updateNotificationBadge();
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }

    requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Notification permission granted');
                }
            });
        }
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Initialize notification system
let notificationSystem;

document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission on page load
    if ('Notification' in window && Notification.permission === 'default') {
        // Show a user-friendly prompt instead of immediate request
        const permissionButton = document.createElement('button');
        permissionButton.className = 'btn btn-primary notification-permission-btn';
        permissionButton.innerHTML = '<i class="fas fa-bell"></i> Включить уведомления';
        permissionButton.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        permissionButton.onclick = function() {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    permissionButton.remove();
                    notificationSystem = new NotificationSystem();
                }
            });
        };
        
        document.body.appendChild(permissionButton);
    } else {
        notificationSystem = new NotificationSystem();
    }
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
