// wheel_of_fortune.js - Wheel of Fortune functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('Инициализация колеса фортуны...');
    initializeWheelOfFortune();
});

function initializeWheelOfFortune() {
    const wheel = document.getElementById('wheelOfFortune');
    const spinButton = document.getElementById('spinButton');
    const resultDisplay = document.getElementById('wheelResult');
    
    if (!wheel || !spinButton) {
        console.log('Элементы колеса фортуны не найдены');
        return;
    }
    
    let isSpinning = false;
    let currentRotation = 0;
    
    spinButton.addEventListener('click', function() {
        if (isSpinning) {
            return;
        }
        
        // Check if user can spin (you might want to add server-side validation)
        if (!canSpin()) {
            showMessage('Вы можете крутить колесо только раз в 24 часа!', 'warning');
            return;
        }
        
        spinWheel();
    });
}

function spinWheel() {
    const wheel = document.getElementById('wheelOfFortune');
    const spinButton = document.getElementById('spinButton');
    
    if (!wheel || !spinButton) return;
    
    isSpinning = true;
    spinButton.disabled = true;
    spinButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Крутим...';
    
    // Generate random rotation
    const spins = Math.floor(Math.random() * 5) + 5; // 5-10 full rotations
    const finalAngle = Math.floor(Math.random() * 360);
    const totalRotation = currentRotation + (spins * 360) + finalAngle;
    
    // Apply rotation animation
    wheel.style.transition = 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)';
    wheel.style.transform = `rotate(${totalRotation}deg)`;
    
    // Update current rotation
    currentRotation = totalRotation % 360;
    
    // Show result after animation
    setTimeout(() => {
        showWheelResult(finalAngle);
        isSpinning = false;
        spinButton.disabled = false;
        spinButton.innerHTML = '<i class="fas fa-dice"></i> Крутить';
        
        // Save spin attempt to server (you might want to add this)
        saveSpinAttempt();
    }, 4000);
}

function showWheelResult(angle) {
    const segments = [
        { text: '⭐ 5 звезд', value: 5, color: '#FFD700' },
        { text: '⭐ 10 звезд', value: 10, color: '#FFA500' },
        { text: '⭐ 15 звезд', value: 15, color: '#FF6B35' },
        { text: '⭐ 20 звезд', value: 20, color: '#FF8C00' },
        { text: '🎁 Сюрприз', value: 25, color: '#9C27B0' },
        { text: '💎 30 звезд', value: 30, color: '#2196F3' },
        { text: '🍀 Повторная попытка', value: 0, color: '#6C757D' }
    ];
    
    // Calculate which segment the pointer is on
    const segmentAngle = 360 / segments.length;
    const normalizedAngle = (angle + segmentAngle / 2) % 360;
    const segmentIndex = Math.floor(normalizedAngle / segmentAngle);
    const result = segments[segmentIndex];
    
    // Display result
    const resultDisplay = document.getElementById('wheelResult');
    if (resultDisplay) {
        resultDisplay.innerHTML = `
            <div class="wheel-result">
                <h3>Поздравляем!</h3>
                <p style="color: ${result.color}; font-size: 1.5rem; font-weight: bold;">
                    ${result.text}
                </p>
                <p>Вы получили ${result.value} звезд!</p>
            </div>
        `;
        resultDisplay.style.display = 'block';
    }
    
    // Show celebration animation
    showCelebration();
}

function showCelebration() {
    // Add celebration effects
    const wheel = document.getElementById('wheelOfFortune');
    if (wheel) {
        wheel.style.boxShadow = '0 0 50px rgba(255, 215, 0, 0.8)';
        setTimeout(() => {
            wheel.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.2)';
        }, 1000);
    }
}

function canSpin() {
    // Check if user can spin (server-side validation recommended)
    // For now, return true (you can add server-side check)
    return true;
}

function saveSpinAttempt() {
    // Save spin attempt to server
    fetch('/api/save-wheel-spin/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Spin attempt saved:', data);
    })
    .catch(error => {
        console.error('Error saving spin attempt:', error);
    });
}

function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        max-width: 300px;
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

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
