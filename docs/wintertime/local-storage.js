// Local Storage Management for Talvipukeutuminen

const STORAGE_KEY = 'talvipukeutuminen';

// Default state
const defaultState = {
    completionCount: 0,
    lastCompleted: null
};

// Get stored state
function getStoredState() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch (e) {
        console.error('Error reading from localStorage:', e);
    }
    return { ...defaultState };
}

// Save state to storage
function saveState(state) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

// Increment completion count
function incrementCompletionCount() {
    const state = getStoredState();
    state.completionCount += 1;
    state.lastCompleted = new Date().toISOString();
    saveState(state);
    return state.completionCount;
}

// Get completion count
function getCompletionCount() {
    const state = getStoredState();
    return state.completionCount;
}

// Update the kids icons display on home screen
function updateKidsIcons() {
    const count = getCompletionCount();
    const container = document.getElementById('kids-icons');
    
    if (container) {
        container.innerHTML = '';
        
        // Kid emoji options for variety
        const kidEmojis = ['👧', '👶', '🧒', '👦', '🧒'];
        
        // Show up to 10 kids icons, cycle through emojis
        const displayCount = Math.min(count, 10);
        for (let i = 0; i < displayCount; i++) {
            const icon = document.createElement('span');
            icon.className = 'kid-icon';
            icon.textContent = kidEmojis[i % kidEmojis.length];
            icon.style.animationDelay = `${i * 0.1}s`;
            container.appendChild(icon);
        }
        
        // If more than 10, show more emoji
        if (count > 10) {
            const more = document.createElement('span');
            more.className = 'kid-icon';
            more.textContent = '🌟';
            container.appendChild(more);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', updateKidsIcons);
