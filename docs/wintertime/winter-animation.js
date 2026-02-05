// Main Application Logic for Talvipukeutuminen

// Clothing steps configuration
const clothingSteps = [
    {
        id: 1,
        title: 'Pitkähihainen paita',
        images: [
            { src: 'images/01_long_sleeve_shirt_1.jpg', label: 'Paita 1' },
            { src: 'images/01_long_sleeve_shirt_2.jpg', label: 'Paita 2' },
            { src: 'images/01_long_sleeve_shirt_3.jpg', label: 'Paita 3' }
        ],
        isChoice: false
    },
    {
        id: 2,
        title: 'Sisähousut',
        images: [
            { src: 'images/02_indoor_pants_1.jpg', label: 'Housut 1' },
            { src: 'images/02_indoor_pants_2.jpg', label: 'Housut 2' },
            { src: 'images/02_indoor_pants_3.jpg', label: 'Housut 3' }
        ],
        isChoice: false
    },
    {
        id: 3,
        title: 'Sukat',
        images: [
            { src: 'images/03_socks_1.jpg', label: 'Sukat 1' },
            { src: 'images/03_socks_2.jpg', label: 'Sukat 2' },
            { src: 'images/03_socks_3.jpg', label: 'Sukat 3' }
        ],
        isChoice: false
    },
    {
        id: 4,
        title: 'Villavaatteet',
        isChoice: true,
        choices: [
            {
                name: 'Villahaalari',
                images: [
                    { src: 'images/04a_wool_overalls_1.jpg', label: 'Haalari 1' },
                    { src: 'images/04a_wool_overalls_2.jpg', label: 'Haalari 2' },
                    { src: 'images/04a_wool_overalls_3.jpg', label: 'Haalari 3' }
                ]
            },
            {
                name: 'Villahousut + Villapaita',
                images: [
                    { src: 'images/04b_wool_pants_1.jpg', label: 'Housut 1' },
                    { src: 'images/04b_wool_pants_2.jpg', label: 'Housut 2' },
                    { src: 'images/04b_wool_pants_3.jpg', label: 'Housut 3' },
                    { src: 'images/04c_wool_sweater_1.jpg', label: 'Paita 1' },
                    { src: 'images/04c_wool_sweater_2.jpg', label: 'Paita 2' },
                    { src: 'images/04c_wool_sweater_3.jpg', label: 'Paita 3' }
                ]
            }
        ]
    },
    {
        id: 5,
        title: 'Ulkovaatteet',
        isChoice: true,
        choices: [
            {
                name: 'Toppahaalari',
                images: [
                    { src: 'images/05a_winter_overalls_1.jpg', label: 'Haalari 1' },
                    { src: 'images/05a_winter_overalls_2.jpg', label: 'Haalari 2' },
                    { src: 'images/05a_winter_overalls_3.jpg', label: 'Haalari 3' }
                ]
            },
            {
                name: 'Toppahousut + Toppatakki',
                images: [
                    { src: 'images/05b_winter_pants_1.jpg', label: 'Housut 1' },
                    { src: 'images/05b_winter_pants_2.jpg', label: 'Housut 2' },
                    { src: 'images/05b_winter_pants_3.jpg', label: 'Housut 3' },
                    { src: 'images/05c_winter_jacket_1.jpg', label: 'Takki 1' },
                    { src: 'images/05c_winter_jacket_2.jpg', label: 'Takki 2' },
                    { src: 'images/05c_winter_jacket_3.jpg', label: 'Takki 3' }
                ]
            }
        ]
    },
    {
        id: 6,
        title: 'Kauluri',
        images: [
            { src: 'images/06_neck_scarf_1.jpg', label: 'Kauluri 1' },
            { src: 'images/06_neck_scarf_2.jpg', label: 'Kauluri 2' },
            { src: 'images/06_neck_scarf_3.jpg', label: 'Kauluri 3' }
        ],
        isChoice: false
    },
    {
        id: 7,
        title: 'Pipo',
        images: [
            { src: 'images/07_skiing_cap_1.jpg', label: 'Pipo 1' },
            { src: 'images/07_skiing_cap_2.jpg', label: 'Pipo 2' },
            { src: 'images/07_skiing_cap_3.jpg', label: 'Pipo 3' }
        ],
        isChoice: false
    },
    {
        id: 8,
        title: 'Villasukat',
        images: [
            { src: 'images/08_woollen_socks_1.jpg', label: 'Sukat 1' },
            { src: 'images/08_woollen_socks_2.jpg', label: 'Sukat 2' },
            { src: 'images/08_woollen_socks_3.jpg', label: 'Sukat 3' }
        ],
        isChoice: false
    },
    {
        id: 9,
        title: 'Talvikengät',
        images: [
            { src: 'images/09_winter_boots_1.jpg', label: 'Kengät 1' },
            { src: 'images/09_winter_boots_2.jpg', label: 'Kengät 2' },
            { src: 'images/09_winter_boots_3.jpg', label: 'Kengät 3' }
        ],
        isChoice: false
    },
    {
        id: 10,
        title: 'Sisälapaset (kylmällä)',
        images: [
            { src: 'images/10_inner_wool_mittens_1.jpg', label: 'Lapaset 1' },
            { src: 'images/10_inner_wool_mittens_2.jpg', label: 'Lapaset 2' },
            { src: 'images/10_inner_wool_mittens_3.jpg', label: 'Lapaset 3' }
        ],
        isChoice: false
    },
    {
        id: 11,
        title: 'Ulkokäsineet',
        images: [
            { src: 'images/11_outer_gloves_1.jpg', label: 'Käsineet 1' },
            { src: 'images/11_outer_gloves_2.jpg', label: 'Käsineet 2' },
            { src: 'images/11_outer_gloves_3.jpg', label: 'Käsineet 3' }
        ],
        isChoice: false
    }
];

// Application state
let currentStep = 0;
const totalSteps = clothingSteps.length;

// Screen elements
const homeScreen = document.getElementById('home-screen');
const dressingScreen = document.getElementById('dressing-screen');
const celebrationScreen = document.getElementById('celebration-screen');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Set up button listeners
    const startBtn = document.getElementById('start-btn');
    const homeBtn = document.getElementById('home-btn');
    
    if (startBtn) {
        startBtn.addEventListener('click', startDressing);
    }
    
    if (homeBtn) {
        homeBtn.addEventListener('click', goToHome);
    }
    
    // Update kids icons on home screen
    updateKidsIcons();
}

// Navigate to home screen
function goToHome() {
    hideAllScreens();
    homeScreen.classList.add('active');
    clearAllFish();
    updateKidsIcons();
}

// Start the dressing process
function startDressing() {
    currentStep = 0;
    hideAllScreens();
    dressingScreen.classList.add('active');
    clearAllFish();
    showCurrentStep();
}

// Hide all screens
function hideAllScreens() {
    homeScreen.classList.remove('active');
    dressingScreen.classList.remove('active');
    celebrationScreen.classList.remove('active');
}

// Track clicked stars for two-item choices (top and bottom on right side)
let choiceStarsClicked = { top: false, bottom: false };

// Show the current clothing step
function showCurrentStep() {
    const step = clothingSteps[currentStep];
    const container = document.getElementById('clothes-container');
    const starButtons = document.getElementById('star-buttons');
    const progressBar = document.getElementById('progress-bar');
    
    // Reset choice tracking
    choiceStarsClicked = { top: false, bottom: false };
    
    // Update progress
    progressBar.style.width = `${((currentStep) / totalSteps) * 100}%`;
    
    // Clear previous content
    container.innerHTML = '';
    starButtons.innerHTML = '';
    container.classList.remove('choice-layout');
    
    if (step.isChoice) {
        // Show choice options - 3 columns: [single item] | [item 1] | [item 2]
        container.classList.add('choice-layout');
        renderChoiceStep(step, container, starButtons);
    } else {
        // Show regular step - single image with big star
        renderRegularStep(step, container, starButtons);
    }
}

// Render a regular (non-choice) step - single large image with big star
function renderRegularStep(step, container, starButtons) {
    // Show just the first image, large
    const img = step.images[0];
    const item = createClothesItem(img);
    container.appendChild(item);
    
    // Single big star button
    const starBtn = createStarButton(() => {
        completeStep(starBtn);
    }, 'big');
    starButtons.appendChild(starBtn);
}

// Render a choice step: 2 columns layout
// Left: single item (overalls) with 1 big star
// Right: two items stacked - top (sweater/jacket) + bottom (pants), each with small star
function renderChoiceStep(step, container, starButtons) {
    const choiceContainer = document.createElement('div');
    choiceContainer.className = 'choice-container-two';
    
    // Left column: Single item (e.g., overalls)
    const singleChoice = step.choices[0];
    const leftColumn = document.createElement('div');
    leftColumn.className = 'choice-column left-single';
    
    const singleImg = createClothesItem(singleChoice.images[0]);
    leftColumn.appendChild(singleImg);
    
    const singleStar = createStarButton(() => {
        completeStep(singleStar);
    }, 'big');
    leftColumn.appendChild(singleStar);
    
    choiceContainer.appendChild(leftColumn);
    
    // Right column: Two items stacked vertically
    const twoItemChoice = step.choices[1];
    const rightColumn = document.createElement('div');
    rightColumn.className = 'choice-column right-double';
    
    // Images: first 3 are pants, last 3 are sweater/jacket
    const pantsImages = twoItemChoice.images.slice(0, 3);
    const topImages = twoItemChoice.images.slice(3, 6); // sweater/jacket on TOP
    
    // Top item: sweater/jacket
    const topBox = document.createElement('div');
    topBox.className = 'stacked-item';
    const topImg = createClothesItem(topImages[0]);
    topBox.appendChild(topImg);
    const topStar = createStarButton(() => {
        handleTwoItemStar('top', topStar);
    }, 'small');
    topStar.id = 'star-top';
    topBox.appendChild(topStar);
    rightColumn.appendChild(topBox);
    
    // Bottom item: pants
    const bottomBox = document.createElement('div');
    bottomBox.className = 'stacked-item';
    const bottomImg = createClothesItem(pantsImages[0]);
    bottomBox.appendChild(bottomImg);
    const bottomStar = createStarButton(() => {
        handleTwoItemStar('bottom', bottomStar);
    }, 'small');
    bottomStar.id = 'star-bottom';
    bottomBox.appendChild(bottomStar);
    rightColumn.appendChild(bottomBox);
    
    choiceContainer.appendChild(rightColumn);
    
    container.appendChild(choiceContainer);
}

// Handle clicking on a two-item choice star (top or bottom)
function handleTwoItemStar(position, button) {
    // Mark this star as clicked
    choiceStarsClicked[position] = true;
    button.classList.add('selected');
    button.disabled = true;
    
    // Create star animation at button position
    const rect = button.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    createStarExplosion(centerX, centerY, 3);
    
    // Check if both stars are clicked (top AND bottom)
    if (choiceStarsClicked.top && choiceStarsClicked.bottom) {
        // Both clicked - complete the step
        setTimeout(() => {
            // Add fish
            if (currentStep > 0) {
                addSwimmingFish();
            }
            
            // Update progress
            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = `${((currentStep + 1) / totalSteps) * 100}%`;
            
            // Move to next step
            currentStep++;
            if (currentStep >= totalSteps) {
                showCelebration();
            } else {
                showCurrentStep();
            }
        }, 500);
    }
}

// Create a clothes item element (no label - kids can't read)
function createClothesItem(img) {
    const item = document.createElement('div');
    item.className = 'clothes-item';
    
    const image = document.createElement('img');
    image.className = 'clothes-image';
    image.src = img.src;
    image.alt = '';
    image.loading = 'lazy';
    
    item.appendChild(image);
    
    return item;
}

// Create a star button with size option
function createStarButton(onClick, size = 'normal') {
    const btn = document.createElement('button');
    btn.className = `star-button ${size}`;
    btn.textContent = '★';
    btn.addEventListener('click', onClick);
    return btn;
}

// Complete the current step
function completeStep(clickedButton) {
    // Disable the button and mark as selected
    clickedButton.classList.add('selected');
    clickedButton.disabled = true;
    
    // Get button position for star animation
    const rect = clickedButton.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Create star explosion
    createStarExplosion(centerX, centerY, 5);
    
    // Add a fish if step > 1
    if (currentStep > 0) {
        addSwimmingFish();
    }
    
    // Update progress bar
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${((currentStep + 1) / totalSteps) * 100}%`;
    
    // Move to next step after a short delay
    setTimeout(() => {
        currentStep++;
        
        if (currentStep >= totalSteps) {
            // All done! Show celebration
            showCelebration();
        } else {
            showCurrentStep();
        }
    }, 800);
}

// Show celebration screen
function showCelebration() {
    hideAllScreens();
    celebrationScreen.classList.add('active');
    
    // Increment completion count
    incrementCompletionCount();
    
    // Create celebration effects
    createBigCelebrationStar();
    createFishCelebration();
    
    // After 3 seconds, show snow overlay
    setTimeout(() => {
        showSnowOverlay();
    }, 3000);
    
    // After 5 seconds, show rainbow
    setTimeout(() => {
        showRainbowOverlay();
    }, 5000);
    
    // After 10 seconds, go back to home
    setTimeout(() => {
        hideOverlays();
        goToHome();
    }, 10000);
}

// Show snow overlay with dots
function showSnowOverlay() {
    const snowOverlay = document.getElementById('snow-overlay');
    snowOverlay.classList.add('active');
    
    // Add snow dots
    for (let i = 0; i < 100; i++) {
        const dot = document.createElement('div');
        dot.className = 'snow-dot';
        dot.style.left = `${Math.random() * 100}%`;
        dot.style.top = `${Math.random() * 100}%`;
        dot.style.animationDelay = `${Math.random() * 2}s`;
        snowOverlay.appendChild(dot);
    }
    
    // Add fish swimming in snow
    fishSwimInSnow();
}

// Show rainbow overlay
function showRainbowOverlay() {
    const rainbowOverlay = document.getElementById('rainbow-overlay');
    rainbowOverlay.classList.add('active');
}

// Hide all overlays
function hideOverlays() {
    const snowOverlay = document.getElementById('snow-overlay');
    const rainbowOverlay = document.getElementById('rainbow-overlay');
    
    snowOverlay.classList.remove('active');
    snowOverlay.innerHTML = '';
    rainbowOverlay.classList.remove('active');
}
