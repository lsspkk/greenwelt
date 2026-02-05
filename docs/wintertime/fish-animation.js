// Fish Animation for Talvipukeutuminen

// Array to track all swimming fish
let swimmingFish = [];

// Fish emojis for variety
const fishEmojis = ['🐟', '🐠', '🐡', '🦈', '🐳', '🐋', '🐬'];

// Create a new swimming fish
function addSwimmingFish() {
    const container = document.getElementById('fish-container');
    if (!container) return;
    
    const fish = document.createElement('div');
    fish.className = 'swimming-fish';
    fish.textContent = fishEmojis[swimmingFish.length % fishEmojis.length];
    
    // Random starting position and speed
    const startY = 10 + Math.random() * 40;
    fish.style.bottom = `${startY}px`;
    fish.style.left = '-50px';
    
    // Vary the animation duration for different speeds
    const duration = 6 + Math.random() * 6;
    fish.style.animationDuration = `${duration}s`;
    
    // Random delay so fish don't all start at same time
    const delay = Math.random() * 2;
    fish.style.animationDelay = `${delay}s`;
    
    container.appendChild(fish);
    swimmingFish.push(fish);
    
    return fish;
}

// Remove all swimming fish
function clearAllFish() {
    const container = document.getElementById('fish-container');
    if (container) {
        container.innerHTML = '';
    }
    swimmingFish = [];
}

// Create celebration fish explosion
function createFishCelebration() {
    const container = document.getElementById('fish-container');
    if (!container) return;
    
    // Add many fish at once
    for (let i = 0; i < 10; i++) {
        setTimeout(() => {
            const fish = document.createElement('div');
            fish.className = 'swimming-fish';
            fish.textContent = fishEmojis[i % fishEmojis.length];
            
            const startY = 5 + Math.random() * 60;
            fish.style.bottom = `${startY}px`;
            fish.style.left = '-50px';
            
            const duration = 4 + Math.random() * 4;
            fish.style.animationDuration = `${duration}s`;
            
            // Random size variation
            const size = 1.5 + Math.random() * 1.5;
            fish.style.fontSize = `${size}rem`;
            
            container.appendChild(fish);
        }, i * 200);
    }
}

// Make fish swim into the snow scene (for celebration)
function fishSwimInSnow() {
    const snowOverlay = document.getElementById('snow-overlay');
    if (!snowOverlay) return;
    
    // Create fish swimming in the snow overlay
    for (let i = 0; i < 8; i++) {
        const fish = document.createElement('div');
        fish.className = 'swimming-fish';
        fish.textContent = fishEmojis[i % fishEmojis.length];
        fish.style.position = 'absolute';
        fish.style.bottom = `${10 + i * 10}%`;
        fish.style.zIndex = '55';
        fish.style.fontSize = '2.5rem';
        
        const duration = 5 + Math.random() * 5;
        fish.style.animationDuration = `${duration}s`;
        fish.style.animationDelay = `${i * 0.3}s`;
        
        snowOverlay.appendChild(fish);
    }
}
