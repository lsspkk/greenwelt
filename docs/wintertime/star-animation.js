// Star Animation for Talvipukeutuminen

// Create and animate a flying star from a given position
function createFlyingStar(x, y) {
    const star = document.createElement('div');
    star.className = 'flying-star';
    star.textContent = '⭐';
    star.style.left = `${x}px`;
    star.style.top = `${y}px`;
    
    document.body.appendChild(star);
    
    // Remove after animation completes
    star.addEventListener('animationend', () => {
        star.remove();
    });
    
    // Fallback removal after 2 seconds
    setTimeout(() => {
        if (star.parentNode) {
            star.remove();
        }
    }, 2000);
}

// Create multiple stars explosion effect
function createStarExplosion(x, y, count = 5) {
    for (let i = 0; i < count; i++) {
        setTimeout(() => {
            const offsetX = (Math.random() - 0.5) * 100;
            const offsetY = (Math.random() - 0.5) * 100;
            createFlyingStarCustom(x + offsetX, y + offsetY, i);
        }, i * 100);
    }
}

// Create a custom animated star with more variety
function createFlyingStarCustom(x, y, index) {
    const star = document.createElement('div');
    star.className = 'flying-star';
    
    // Variety of star symbols
    const starSymbols = ['⭐', '🌟', '✨', '💫', '⭐'];
    star.textContent = starSymbols[index % starSymbols.length];
    
    star.style.left = `${x}px`;
    star.style.top = `${y}px`;
    
    // Random rotation and scale variation
    const rotationSpeed = 1 + Math.random() * 0.5;
    const scale = 0.8 + Math.random() * 0.4;
    star.style.setProperty('--rotation-speed', `${rotationSpeed}s`);
    star.style.transform = `scale(${scale})`;
    
    document.body.appendChild(star);
    
    // Remove after animation
    setTimeout(() => {
        if (star.parentNode) {
            star.remove();
        }
    }, 1500);
}

// Big celebration star effect
function createBigCelebrationStar() {
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 3;
    
    // Create multiple waves of stars
    for (let wave = 0; wave < 3; wave++) {
        setTimeout(() => {
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2;
                const distance = 50 + wave * 30;
                const x = centerX + Math.cos(angle) * distance;
                const y = centerY + Math.sin(angle) * distance;
                createFlyingStarCustom(x, y, i);
            }
        }, wave * 300);
    }
}
