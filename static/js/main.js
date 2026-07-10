// SmartBite Interactive Scripts

document.addEventListener('DOMContentLoaded', function() {
    // ----------------------------------------------------
    // 1. Mobile Sidebar Toggle
    // ----------------------------------------------------
    const mobileToggle = document.getElementById('mobileNavToggle');
    const sidebarNav = document.getElementById('sidebarNav');
    if (mobileToggle && sidebarNav) {
        mobileToggle.addEventListener('click', function() {
            sidebarNav.classList.toggle('show');
            const icon = mobileToggle.querySelector('i');
            if (sidebarNav.classList.contains('show')) {
                icon.classList.replace('fa-bars', 'fa-times');
            } else {
                icon.classList.replace('fa-times', 'fa-bars');
            }
        });
    }

    // ----------------------------------------------------
    // 2. BMI Calculator Widget
    // ----------------------------------------------------
    const bmiWeight = document.getElementById('bmiWeight');
    const bmiHeight = document.getElementById('bmiHeight');
    const btnCalcBmi = document.getElementById('btnCalcBmi');
    const bmiResult = document.getElementById('bmiResult');
    const bmiCategory = document.getElementById('bmiCategory');
    const bmiIndicator = document.getElementById('bmiIndicator');

    function calculateBMI() {
        if (!bmiWeight || !bmiHeight) return;
        const w = parseFloat(bmiWeight.value);
        const h = parseFloat(bmiHeight.value) / 100; // convert cm to meters

        if (w > 0 && h > 0) {
            const bmi = (w / (h * h)).toFixed(1);
            let category = '';
            let pct = 0; // percentage for spectrum display

            if (bmi < 18.5) {
                category = 'Underweight';
                pct = Math.max(5, (bmi / 18.5) * 25);
            } else if (bmi >= 18.5 && bmi < 25) {
                category = 'Normal weight';
                pct = 25 + ((bmi - 18.5) / 6.5) * 30; // 18.5 to 25 mapping to 25%-55%
            } else if (bmi >= 25 && bmi < 30) {
                category = 'Overweight';
                pct = 55 + ((bmi - 25) / 5) * 25; // 25 to 30 mapping to 55%-80%
            } else {
                category = 'Obese';
                pct = Math.min(95, 80 + ((bmi - 30) / 15) * 15); // 30+ mapping to 80%-95%
            }

            if (bmiResult) bmiResult.textContent = bmi;
            if (bmiCategory) {
                bmiCategory.textContent = category;
                // Style category label
                bmiCategory.className = 'font-weight-bold';
                if (category === 'Underweight') bmiCategory.style.color = '#3b82f6';
                if (category === 'Normal weight') bmiCategory.style.color = '#10b981';
                if (category === 'Overweight') bmiCategory.style.color = '#f59e0b';
                if (category === 'Obese') bmiCategory.style.color = '#ef4444';
            }
            if (bmiIndicator) {
                bmiIndicator.style.left = pct + '%';
            }
        }
    }

    if (btnCalcBmi) {
        btnCalcBmi.addEventListener('click', calculateBMI);
        // Calculate initially if inputs have values
        calculateBMI();
    }

    // ----------------------------------------------------
    // 3. Water Intake Tracker
    // ----------------------------------------------------
    const btnAddWater = document.getElementById('btnAddWater');
    const waterIntakeEl = document.getElementById('waterIntake');
    const waterProgressPctEl = document.getElementById('waterProgressPct');
    const waterWave = document.getElementById('waterWave');
    const waterGoal = 3000; // 3 Liters target

    // Load saved water value or default to 0
    let currentWater = parseInt(localStorage.getItem('smartbite_water') || '0');
    // Check if new day, reset if necessary
    const savedDate = localStorage.getItem('smartbite_water_date');
    const todayStr = new Date().toDateString();
    if (savedDate !== todayStr) {
        currentWater = 0;
        localStorage.setItem('smartbite_water', '0');
        localStorage.setItem('smartbite_water_date', todayStr);
    }

    function updateWaterUI() {
        if (!waterIntakeEl || !waterProgressPctEl || !waterWave) return;
        waterIntakeEl.textContent = currentWater;
        const pct = Math.min(100, Math.round((currentWater / waterGoal) * 100));
        waterProgressPctEl.textContent = pct + '%';
        waterWave.style.height = pct + '%';
    }

    if (btnAddWater) {
        btnAddWater.addEventListener('click', function() {
            currentWater += 250; // Add 250ml (one glass)
            localStorage.setItem('smartbite_water', currentWater);
            updateWaterUI();
        });
    }

    // Initialize water display
    updateWaterUI();

    // ----------------------------------------------------
    // 4. AJAX Chat Assistant
    // ----------------------------------------------------
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');

    function appendMessage(text, isUser = false) {
        if (!chatMessages) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'message-user' : 'message-agent'}`;
        msgDiv.innerHTML = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (chatForm && chatInput) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = chatInput.value.strip ? chatInput.value.strip() : chatInput.value.trim();
            if (!message) return;

            // Append user message
            appendMessage(message, true);
            chatInput.value = '';

            // Show typing indicator
            if (typingIndicator) {
                typingIndicator.style.display = 'flex';
                chatMessages.appendChild(typingIndicator); // move to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Send POST request
            fetch('/chat_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            })
            .then(res => res.json())
            .then(data => {
                // Hide typing indicator
                if (typingIndicator) typingIndicator.style.display = 'none';
                
                if (data.status === 'success') {
                    appendMessage(data.response, false);
                } else {
                    appendMessage(`<p style="color: var(--accent-red)"><i class="fas fa-exclamation-triangle"></i> Error: ${data.message}</p>`, false);
                }
            })
            .catch(err => {
                if (typingIndicator) typingIndicator.style.display = 'none';
                appendMessage(`<p style="color: var(--accent-red)"><i class="fas fa-exclamation-triangle"></i> Failed to communicate with server.</p>`, false);
                console.error(err);
            });
        });
    }

    // Quick prompt helper buttons
    const quickButtons = document.querySelectorAll('.btn-quick');
    if (quickButtons && chatInput && chatForm) {
        quickButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                chatInput.value = btn.getAttribute('data-prompt');
                chatForm.dispatchEvent(new Event('submit'));
            });
        });
    }

    // ----------------------------------------------------
    // 5. Smart Swap pantry interaction
    // ----------------------------------------------------
    const swapSearch = document.getElementById('swapSearch');
    const swapResults = document.getElementById('swapResults');

    if (swapSearch && swapResults) {
        swapSearch.addEventListener('input', function() {
            const query = swapSearch.value.trim().toLowerCase();
            const items = swapResults.querySelectorAll('.swap-comparison-card');
            
            items.forEach(card => {
                const itemName = card.getAttribute('data-name').toLowerCase();
                const healthySwap = card.getAttribute('data-swap').toLowerCase();
                if (itemName.includes(query) || healthySwap.includes(query)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});
