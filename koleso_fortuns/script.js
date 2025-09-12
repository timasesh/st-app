class WheelOfFortune {
    constructor() {
        this.wheel = document.getElementById('wheel');
        this.spinBtn = document.getElementById('spinBtn');
        this.result = document.getElementById('result');
        this.prizeDisplay = document.getElementById('prizeDisplay');
        this.particles = document.getElementById('particles');
        
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
    
    spin() {
        if (this.isSpinning) return;
        
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
            this.spinBtn.disabled = false;
            
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
            
            // Отправляем результат на сервер (если есть Django)
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
    
    // Отправка результата на сервер (для Django)
    sendResultToServer(prize) {
        // Здесь можно добавить AJAX запрос к Django
        console.log(`Отправка результата на сервер: ${prize}`);
        
        // Пример AJAX запроса:
        /*
        fetch('/spin_wheel/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                prize: prize,
                index: index,
                timestamp: Date.now()
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Результат сохранен:', data);
        })
        .catch(error => {
            console.error('Ошибка при отправке результата:', error);
        });
        */
    }
    
    createParticles() {
        setInterval(() => {
            if (!this.isSpinning) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDuration = (Math.random() * 2 + 2) + 's';
                particle.style.opacity = Math.random() * 0.5 + 0.5;
                
                this.particles.appendChild(particle);
                
                setTimeout(() => {
                    particle.remove();
                }, 5000);
            }
        }, 300);
    }
    
    createSpinParticles() {
        const interval = setInterval(() => {
            if (this.isSpinning) {
                for (let i = 0; i < 3; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = (50 + (Math.random() - 0.5) * 20) + '%';
                    particle.style.top = (50 + (Math.random() - 0.5) * 20) + '%';
                    particle.style.animationDuration = '1s';
                    particle.style.background = ['#ffd700', '#ff6b6b', '#4ecdc4'][Math.floor(Math.random() * 3)];
                    
                    this.particles.appendChild(particle);
                    
                    setTimeout(() => {
                        particle.remove();
                    }, 1000);
                }
            } else {
                clearInterval(interval);
            }
        }, 100);
    }
    
    createWinParticles() {
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = (50 + (Math.random() - 0.5) * 40) + '%';
                particle.style.top = (50 + (Math.random() - 0.5) * 40) + '%';
                particle.style.animationDuration = '2s';
                particle.style.background = '#ffd700';
                particle.style.width = '6px';
                particle.style.height = '6px';
                
                this.particles.appendChild(particle);
                
                setTimeout(() => {
                    particle.remove();
                }, 2000);
            }, i * 50);
        }
    }
    
    // Звуковые эффекты (используем Web Audio API)
    playHoverSound() {
        this.playTone(800, 0.1, 0.1);
    }
    
    playSpinSound() {
        this.playTone(400, 0.3, 4);
    }
    
    playWinSound() {
        this.playTone(600, 0.2, 0.5);
        setTimeout(() => this.playTone(800, 0.2, 0.5), 100);
        setTimeout(() => this.playTone(1000, 0.2, 0.5), 200);
    }
    
    playLoseSound() {
        this.playTone(200, 0.3, 1);
    }
    
    playTone(frequency, volume, duration) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(volume, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        } catch (error) {
            // Игнорируем ошибки аудио (например, если браузер не поддерживает)
        }
    }
}

// Функция для получения CSRF токена (для Django)
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

// Инициализация игры при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new WheelOfFortune();
    
    // Добавляем эффект параллакса для фона
    document.addEventListener('mousemove', (e) => {
        const moveX = (e.clientX - window.innerWidth / 2) * 0.01;
        const moveY = (e.clientY - window.innerHeight / 2) * 0.01;
        
        document.body.style.backgroundPosition = `${moveX}px ${moveY}px`;
    });
    
    // Добавляем эффект при клике на колесо
    document.getElementById('wheel').addEventListener('click', () => {
        if (!document.querySelector('.wheel').classList.contains('spinning')) {
            const ripple = document.createElement('div');
            ripple.style.position = 'absolute';
            ripple.style.width = '20px';
            ripple.style.height = '20px';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 215, 0, 0.6)';
            ripple.style.pointerEvents = 'none';
            ripple.style.animation = 'ripple 0.6s linear';
            
            document.querySelector('.wheel-container').appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        }
    });
});

// Добавляем CSS для эффекта ripple
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(20);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
