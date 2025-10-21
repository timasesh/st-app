// Колесо Фортуны
class WheelOfFortune {
    constructor() {
        this.wheel = document.getElementById('wheel');
        this.spinBtn = document.getElementById('spinBtn');
        this.result = document.getElementById('result');
        this.prizeDisplay = document.getElementById('prizeDisplay');
        this.particles = document.getElementById('particles');
        this.userStars = document.getElementById('userStars');
        this.spinStatus = document.getElementById('spinStatus');
        
        this.isSpinning = false;
        this.currentRotation = 0; // Текущий угол поворота колеса
        
        // Определяем секторы с точными углами (против часовой стрелки)
        this.sectors = [
            { center: 0, range: [-25.7, 25.7], prize: "1⭐" },      // 1 звезда
            { center: 51.43, range: [25.7, 77.1], prize: "4⭐" },   // 4 звезды
            { center: 102.86, range: [77.1, 128.6], prize: "0⭐" }, // пусто
            { center: 154.29, range: [128.6, 180.0], prize: "3⭐" }, // 3 звезды
            { center: 205.71, range: [180.0, 231.4], prize: "0⭐" }, // пусто
            { center: 257.14, range: [231.4, 282.9], prize: "0⭐" }, // пусто
            { center: 308.57, range: [282.9, 334.3], prize: "2⭐" }  // 2 звезды
        ];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.createParticles();
        this.checkSpinAvailability();
    }
    
    // Проверяем доступность вращения (1 раз в день)
    async checkSpinAvailability() {
        try {
            const response = await fetch('/api/check-wheel-status/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.canSpin = data.can_spin;
                this.nextSpinTime = data.next_spin_time;
                this.updateSpinStatus();
                return data.can_spin;
            } else {
                console.error('Ошибка проверки статуса:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Ошибка при проверке статуса спина:', error);
            return false;
        }
    }
    
    // Обновляем статус спина
    updateSpinStatus() {
        if (!this.canSpin) {
            this.spinBtn.disabled = true;
            this.spinBtn.innerHTML = '<i class="fas fa-clock"></i><span>24ч!</span>';
            this.spinStatus.textContent = 'Уже крутили недавно';
            this.spinStatus.style.color = '#ff6b6b';
            
            // Показываем время следующего спина
            if (this.nextSpinTime) {
                const nextSpinDate = new Date(this.nextSpinTime);
                const now = new Date();
                const timeDiff = nextSpinDate - now;
                
                if (timeDiff > 0) {
                    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                    this.spinStatus.textContent = `Следующий спин через ${hours}ч ${minutes}м`;
                }
            }
        } else {
            this.spinBtn.disabled = false;
            this.spinBtn.innerHTML = '<i class="fas fa-play"></i><span>Крутить!</span>';
            this.spinStatus.textContent = 'Готово к вращению';
            this.spinStatus.style.color = '#28a745';
        }
    }
    
    // Определяем приз по углу остановки
    getPrizeByAngle(angle) {
        // Нормализуем угол до 0-360
        const normalizedAngle = ((angle % 360) + 360) % 360;
        
        for (let sector of this.sectors) {
            let [start, end] = sector.range;
            
            // Обрабатываем случай, когда диапазон пересекает 0°
            if (start < 0) {
                if (normalizedAngle >= start + 360 || normalizedAngle <= end) {
                    return sector.prize;
                }
            } else {
                if (normalizedAngle >= start && normalizedAngle <= end) {
                    return sector.prize;
                }
            }
        }
        
        // Если не попали ни в один сектор, возвращаем первый (1 звезда)
        return "1⭐";
    }
    
    bindEvents() {
        this.spinBtn.addEventListener('click', () => this.spin());
        
        // Добавляем звуковые эффекты при наведении
        this.spinBtn.addEventListener('mouseenter', () => {
            this.playHoverSound();
        });
    }
    
    async spin() {
        if (this.isSpinning) return;
        
        // Проверяем доступность спина
        const canSpin = await this.checkSpinAvailability();
        if (!canSpin) {
            alert('Вы уже крутили колесо недавно. Следующий спин будет доступен через 24 часа.');
            return;
        }
        
        this.isSpinning = true;
        this.spinBtn.disabled = true;
        this.result.classList.remove('show');
        
        // Генерируем случайный угол от 0 до 360
        const randomAngle = Math.random() * 360;
        
        // Колесо делает 5 полных оборотов + случайный угол
        const fullRotations = 5 * 360; // 5 полных оборотов
        const totalRotation = fullRotations + randomAngle;
        
        // Финальный угол = текущий + полные обороты + случайный угол
        const finalRotation = this.currentRotation + totalRotation;
        
        // Определяем приз по финальному углу
        const finalAngle = (finalRotation % 360);
        const selectedPrize = this.getPrizeByAngle(finalAngle);
        
        // Анимация вращения
        this.wheel.style.transition = 'transform 4s cubic-bezier(0.23, 1, 0.32, 1)';
        this.wheel.style.transform = `rotate(${finalRotation}deg)`;
        
        // Звуковой эффект вращения
        this.playSpinSound();
        
        // Эффект частиц во время вращения
        this.createSpinParticles();
        
        setTimeout(() => {
            this.isSpinning = false;
            
            // Обновляем текущий угол поворота (абсолютный угол)
            this.currentRotation = finalRotation;
            
            // Показываем результат
            this.showResult(selectedPrize);
            
            // Звуковой эффект результата
            if (selectedPrize === "0⭐") {
                this.playLoseSound();
            } else {
                this.playWinSound();
                this.createWinParticles();
            }
            
            // Отправляем результат на сервер Django
            this.sendResultToServer(selectedPrize);
            
        }, 4000);
    }
    
    showResult(prize) {
        let resultText = '';
        let resultClass = '';
        
        switch (prize) {
            case "0⭐":
                resultText = 'К сожалению, ничего не выиграли 😔';
                resultClass = 'lose';
                break;
            case "1⭐":
                resultText = 'Поздравляем! Вы выиграли 1 звезду! 🎉';
                resultClass = 'win';
                break;
            case "2⭐":
                resultText = 'Поздравляем! Вы выиграли 2 звезды! 🎉';
                resultClass = 'win';
                break;
            case "3⭐":
                resultText = 'Поздравляем! Вы выиграли 3 звезды! 🎉';
                resultClass = 'win';
                break;
            case "4⭐":
                resultText = 'Поздравляем! Вы выиграли 4 звезды! 🎉';
                resultClass = 'win';
                break;
            default:
                const starCount = prize.replace('⭐', '');
                resultText = `Поздравляем! Вы выиграли ${starCount} ${this.getStarWord(parseInt(starCount))}! 🎉`;
                resultClass = 'win';
                break;
        }
        
        this.prizeDisplay.innerHTML = resultText;
        this.prizeDisplay.className = resultClass;
        this.result.classList.add('show');
        
        // Добавляем анимацию к кнопке
        this.spinBtn.classList.add('win-animation');
        setTimeout(() => {
            this.spinBtn.classList.remove('win-animation');
        }, 500);
    }
    
    getStarWord(count) {
        if (count === 1) return 'звезду';
        if (count >= 2 && count <= 4) return 'звезды';
        return 'звезд';
    }
    
    // Отправка результата на сервер Django
    async sendResultToServer(prize) {
        try {
            console.log('Отправка результата на сервер:', prize);
            
            const requestBody = {
                prize: prize,
                timestamp: Date.now()
            };
            console.log('Request body:', requestBody);
            
            const response = await fetch('/api/spin-wheel/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            console.log('Response from server:', data);
            
            if (data.success) {
                console.log('Результат сохранен:', data);
                // Обновляем отображение звезд пользователя
                if (this.userStars) {
                    this.userStars.textContent = data.total_stars;
                }
                
                // Обновляем статус спина
                await this.checkSpinAvailability();
            } else {
                console.error('Ошибка при сохранении результата:', data.error);
                // Если студент уже крутил недавно, обновляем статус
                if (data.error && data.error.includes('уже крутили колесо недавно')) {
                    await this.checkSpinAvailability();
                }
                alert('Ошибка при сохранении результата: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка при отправке результата:', error);
            alert('Ошибка при отправке результата');
        }
    }
    
    // Получение CSRF токена из cookies
    getCookie(name) {
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
    
    createParticles() {
        setInterval(() => {
            if (!this.isSpinning) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDuration = (Math.random() * 2 + 1) + 's';
                
                this.particles.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.parentNode.removeChild(particle);
                    }
                }, 3000);
            }
        }, 2000);
    }
    
    createSpinParticles() {
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = '50%';
                particle.style.top = '50%';
                particle.style.transform = 'translate(-50%, -50%)';
                particle.style.animationDuration = (Math.random() * 1 + 0.5) + 's';
                
                this.particles.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.parentNode.removeChild(particle);
                    }
                }, 1500);
            }, i * 100);
        }
    }
    
    createWinParticles() {
        for (let i = 0; i < 30; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.background = '#ffd700';
                particle.style.left = '50%';
                particle.style.top = '50%';
                particle.style.transform = 'translate(-50%, -50%)';
                particle.style.animationDuration = (Math.random() * 2 + 1) + 's';
                
                this.particles.appendChild(particle);
                
                setTimeout(() => {
                    if (particle.parentNode) {
                        particle.parentNode.removeChild(particle);
                    }
                }, 3000);
            }, i * 50);
        }
    }
    
    // Звуковые эффекты
    playHoverSound() {
        this.playTone(800, 0.1, 0.1);
    }
    
    playSpinSound() {
        this.playTone(600, 0.2, 4);
    }
    
    playWinSound() {
        this.playTone(1000, 0.3, 0.5);
        setTimeout(() => this.playTone(1200, 0.2, 0.3), 200);
        setTimeout(() => this.playTone(1400, 0.1, 0.2), 400);
    }
    
    playLoseSound() {
        this.playTone(400, 0.2, 0.5);
        setTimeout(() => this.playTone(300, 0.1, 0.3), 200);
    }
    
    playTone(frequency, volume, duration) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
            gainNode.gain.setValueAtTime(volume, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        } catch (e) {
            console.log('Звук недоступен:', e);
        }
    }
}

// Инициализация колеса фортуны при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('Инициализация колеса фортуны...');
    new WheelOfFortune();
});
