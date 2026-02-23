/**
 * Multi-Agent Travel Planner — Frontend Application
 *
 * Handles form submission, API calls, dynamic result rendering,
 * agent status animations, and tab switching.
 */

// ─── DOM Elements ───
const travelForm = document.getElementById('travelForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const pipelineSection = document.getElementById('pipelineSection');
const resultsSection = document.getElementById('resultsSection');
const resultsSummary = document.getElementById('resultsSummary');

// Tab elements
const tabBtns = document.querySelectorAll('.tab-btn');
const flightsTab = document.getElementById('flightsTab');
const hotelsTab = document.getElementById('hotelsTab');
const trainsTab = document.getElementById('trainsTab');
const roadTab = document.getElementById('roadTab');
const itineraryTab = document.getElementById('itineraryTab');

const flightCount = document.getElementById('flightCount');
const hotelCount = document.getElementById('hotelCount');
const trainCount = document.getElementById('trainCount');
const roadCount = document.getElementById('roadCount');
const itineraryCount = document.getElementById('itineraryCount');

// Agent cards
const agentCards = {
    flight: document.getElementById('agent-flight'),
    hotel: document.getElementById('agent-hotel'),
    itinerary: document.getElementById('agent-itinerary'),
    train: document.getElementById('agent-train'),
    road: document.getElementById('agent-road'),
};

// Set default dates (departure: tomorrow, return: 5 days later)
const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 7);
const returnDate = new Date(tomorrow);
returnDate.setDate(returnDate.getDate() + 5);

document.getElementById('departure_date').value = formatDate(tomorrow);
document.getElementById('return_date').value = formatDate(returnDate);

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// ─── Tab Switching ───
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const tab = btn.dataset.tab;
        flightsTab.style.display = tab === 'flights' ? 'block' : 'none';
        hotelsTab.style.display = tab === 'hotels' ? 'block' : 'none';
        trainsTab.style.display = tab === 'trains' ? 'block' : 'none';
        roadTab.style.display = tab === 'road' ? 'block' : 'none';
        itineraryTab.style.display = tab === 'itinerary' ? 'block' : 'none';
    });
});

// ─── Agent Status Updates ───
function setAgentStatus(agent, status) {
    const card = agentCards[agent];
    if (!card) return;

    const dot = card.querySelector('.status-dot');
    const text = card.querySelector('.status-text');

    dot.className = 'status-dot ' + status;
    text.textContent = status.charAt(0).toUpperCase() + status.slice(1);

    if (status === 'working') {
        card.classList.add('active');
    } else {
        card.classList.remove('active');
    }
}

function resetAllAgents() {
    Object.keys(agentCards).forEach(key => setAgentStatus(key, 'ready'));
}

// ─── Pipeline Animation ───
function showPipeline() {
    pipelineSection.style.display = 'block';
    pipelineSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function updatePipelineStep(step, status) {
    const nodes = pipelineSection.querySelectorAll('.pipeline-node');
    nodes.forEach(node => {
        if (node.dataset.step === step) {
            node.className = 'pipeline-node ' + status;
        }
    });
}

async function animatePipeline(stepsCompleted) {
    const steps = ['collect_input', 'search_flights', 'search_hotels', 'search_trains', 'search_road', 'build_itinerary', 'compile_results'];
    const agentMapping = {
        'search_flights': 'flight',
        'search_hotels': 'hotel',
        'search_trains': 'train',
        'search_road': 'road',
        'build_itinerary': 'itinerary',
    };

    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];

        // Set current as active
        updatePipelineStep(step, 'active');

        // Update agent status
        if (agentMapping[step]) {
            setAgentStatus(agentMapping[step], 'working');
        }

        await sleep(600);

        // Mark as completed
        updatePipelineStep(step, 'completed');

        // Update agent status
        if (agentMapping[step]) {
            setAgentStatus(agentMapping[step], 'complete');
        }
    }
}

function resetPipeline() {
    const nodes = pipelineSection.querySelectorAll('.pipeline-node');
    nodes.forEach(node => node.className = 'pipeline-node');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── Form Submission ───
travelForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Collect form data
    const formData = {
        origin: document.getElementById('origin').value,
        destination: document.getElementById('destination').value,
        departure_date: document.getElementById('departure_date').value,
        return_date: document.getElementById('return_date').value,
        budget: document.getElementById('budget').value,
        travelers: parseInt(document.getElementById('travelers').value),
        interests: document.getElementById('interests').value,
        special_requests: document.getElementById('special_requests').value,
    };

    // UI: show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';
    submitBtn.disabled = true;
    resultsSection.style.display = 'none';

    resetAllAgents();
    resetPipeline();
    showPipeline();

    try {
        // Start pipeline animation concurrently
        const animationPromise = animatePipeline();

        // Call API
        const response = await fetch('/api/plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        // Wait for animation to finish
        await animationPromise;

        if (result.success) {
            renderResults(result.data, formData);
        } else {
            showError(result.error || 'An error occurred while planning your trip.');
        }

    } catch (error) {
        console.error('Planning error:', error);
        showError('Failed to connect to the planning server. Make sure the Flask server is running.');
    } finally {
        btnText.style.display = 'flex';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
    }
});

// ─── Render Results ───
function renderResults(data, formData) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Summary
    const flights = data.flights || [];
    const hotels = data.hotels || [];
    const trains = data.trains || [];
    const roadOptions = data.road_options || [];
    const itinerary = data.itinerary || [];

    resultsSummary.innerHTML = `
        <div style="display:flex; flex-wrap:wrap; gap:1.5rem;">
            <span><i class="fas fa-route" style="color:var(--accent-teal)"></i> <strong>${formData.origin}</strong> → <strong>${formData.destination}</strong></span>
            <span><i class="fas fa-calendar" style="color:var(--accent-purple)"></i> ${formData.departure_date} to ${formData.return_date}</span>
            <span><i class="fas fa-wallet" style="color:var(--accent-amber)"></i> ${formData.budget.charAt(0).toUpperCase() + formData.budget.slice(1)}</span>
            <span><i class="fas fa-users" style="color:var(--accent-blue)"></i> ${formData.travelers} traveler${formData.travelers > 1 ? 's' : ''}</span>
        </div>
        <div style="margin-top:0.5rem; font-size:0.8rem; color:var(--text-muted);">
            ${data.summary || ''}
        </div>
    `;

    // Update counts
    flightCount.textContent = flights.length;
    hotelCount.textContent = hotels.length;
    trainCount.textContent = trains.length;
    roadCount.textContent = roadOptions.length;
    itineraryCount.textContent = itinerary.length + (itinerary.length === 1 ? ' day' : ' days');

    // Render flights
    renderFlights(flights);

    // Render hotels
    renderHotels(hotels);

    // Render trains
    renderTrains(trains);

    // Render road options
    renderRoadOptions(roadOptions);

    // Render itinerary
    renderItinerary(itinerary);

    // Show flights tab by default
    tabBtns.forEach(b => b.classList.remove('active'));
    tabBtns[0].classList.add('active');
    flightsTab.style.display = 'block';
    hotelsTab.style.display = 'none';
    trainsTab.style.display = 'none';
    roadTab.style.display = 'none';
    itineraryTab.style.display = 'none';
}

function renderFlights(flights) {
    if (!flights.length) {
        flightsTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No flight data available.</p>';
        return;
    }

    // Check if the first result is a "No Airport" info card
    if (flights.length === 1 && flights[0].airline === 'No Airport') {
        const f = flights[0];
        flightsTab.innerHTML = `
        <div class="flight-card" style="grid-template-columns:1fr; text-align:center; padding:2rem;">
            <div>
                <div style="font-size:2rem; margin-bottom:0.75rem; color:var(--accent-amber);"><i class="fas fa-plane-slash"></i></div>
                <h4 style="margin-bottom:0.5rem; font-size:1rem;">No Airport at This Destination</h4>
                <p style="color:var(--text-secondary); font-size:0.85rem; line-height:1.5; max-width:500px; margin:0 auto;">
                    ${f.note || 'This city does not have an airport.'}
                </p>
            </div>
        </div>`;
        return;
    }

    flightsTab.innerHTML = flights.map(f => `
        <div class="flight-card">
            <div class="flight-airline">
                <div class="flight-airline-name">${f.airline || 'Unknown'}</div>
                <div class="flight-number">${f.flight_number || ''} &middot; ${f.class || 'Economy'}</div>
            </div>
            <div class="flight-route">
                <div class="flight-time">${f.departure_time || '--:--'}</div>
                <div class="flight-route-line">
                    <span>${f.origin || ''}</span>
                    <span class="line"></span>
                    <i class="fas fa-plane" style="font-size:0.6rem;"></i>
                    <span class="line"></span>
                    <span>${f.destination || ''}</span>
                </div>
                <div class="flight-stops">${f.stop_type || 'Non-stop'} &middot; ${f.duration || ''}</div>
            </div>
            <div></div>
            <div class="flight-price">
                <div class="flight-price-amount">&#8377;${(f.price_inr || 0).toLocaleString('en-IN')}</div>
                <div class="flight-class">per person</div>
            </div>
        </div>
    `).join('');
}

function renderHotels(hotels) {
    if (!hotels.length) {
        hotelsTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No hotel data available.</p>';
        return;
    }

    hotelsTab.innerHTML = hotels.map(h => `
        <div class="hotel-card">
            <div class="hotel-details">
                <h3>${h.name || 'Unknown Hotel'}</h3>
                <div class="hotel-meta">
                    <span class="stars">${'&#9733;'.repeat(h.stars || 3)}</span>
                    <span><i class="fas fa-star" style="color:var(--accent-amber); font-size:0.7rem;"></i> ${h.rating || 'N/A'} (${(h.reviews_count || 0).toLocaleString()} reviews)</span>
                    <span><i class="fas fa-location-dot" style="color:var(--accent-teal); font-size:0.7rem;"></i> ${h.distance_to_center || ''}</span>
                    <span><i class="fas fa-map-pin" style="color:var(--accent-purple); font-size:0.7rem;"></i> ${h.location || ''}</span>
                </div>
                <div class="hotel-amenities">
                    ${(h.amenities || []).slice(0, 6).map(a => `<span class="amenity-tag">${a}</span>`).join('')}
                </div>
            </div>
            <div class="hotel-price">
                <div class="hotel-price-amount">&#8377;${(h.price_per_night_inr || 0).toLocaleString('en-IN')}</div>
                <div class="hotel-price-label">per night</div>
                ${h.breakfast_included ? '<div style="font-size:0.7rem; color:var(--accent-teal); margin-top:0.15rem;"><i class="fas fa-mug-hot"></i> Breakfast included</div>' : ''}
                <div class="hotel-cancel">${h.cancellation || ''}</div>
            </div>
        </div>
    `).join('');
}

function renderTrains(trains) {
    if (!trains.length) {
        trainsTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No Indian Railways data available. Try searching between Indian cities (e.g. Delhi to Mumbai).</p>';
        return;
    }

    // Check if the first result is a "No Direct Trains" info card
    if (trains.length === 1 && trains[0].train_name === 'No Direct Trains') {
        const t = trains[0];
        trainsTab.innerHTML = `
        <div class="train-card" style="grid-template-columns:1fr; text-align:center; padding:2rem;">
            <div>
                <div style="font-size:2rem; margin-bottom:0.75rem; color:var(--accent-amber);"><i class="fas fa-exclamation-triangle"></i></div>
                <h4 style="margin-bottom:0.5rem; font-size:1rem;">No Direct Train Service</h4>
                <p style="color:var(--text-secondary); font-size:0.85rem; line-height:1.5; max-width:500px; margin:0 auto;">
                    ${t.note || 'No direct trains available on this route.'}
                </p>
            </div>
        </div>`;
        return;
    }

    trainsTab.innerHTML = trains.map(t => {
        const availClass = (t.availability || '').toLowerCase().replace(' ', '');
        let availCss = 'avail-available';
        if (availClass === 'rac') availCss = 'avail-rac';
        if (availClass === 'waitlist') availCss = 'avail-waitlist';

        const noteHtml = t.note ? `<div style="grid-column:1/-1; font-size:0.75rem; color:var(--accent-teal); padding-top:0.5rem; border-top:1px solid var(--border-glass);"><i class="fas fa-info-circle"></i> ${t.note}</div>` : '';

        return `
        <div class="train-card">
            <div class="train-info">
                <h4>${t.train_name || 'Unknown Train'}</h4>
                <div class="train-number">${t.train_number || ''} &middot; ${t.train_type || ''}</div>
                <div class="train-meta">
                    <span class="train-meta-tag class-tag">${t.class || t.class_code || ''}</span>
                    <span class="train-meta-tag ${availCss}">${t.availability || 'Available'}</span>
                    ${t.pantry ? '<span class="train-meta-tag class-tag"><i class="fas fa-utensils" style="font-size:0.5rem"></i> Pantry</span>' : ''}
                </div>
            </div>
            <div class="train-route">
                <div class="flight-time">${t.departure_time || '--:--'}</div>
                <div class="route-stations">
                    <span>${t.origin_code || ''}</span>
                    <span class="line"></span>
                    <i class="fas fa-train" style="font-size:0.5rem; color:var(--accent-amber)"></i>
                    <span class="line"></span>
                    <span>${t.destination_code || ''}</span>
                </div>
                <div style="font-size:0.65rem; color:var(--text-muted);">${t.duration || ''} &middot; ${t.distance_km || ''}km</div>
            </div>
            <div style="font-size:0.65rem; color:var(--text-muted); text-align:center;">
                <div style="margin-bottom:0.2rem;"><i class="fas fa-calendar-day"></i> ${t.runs_on || 'Daily'}</div>
            </div>
            <div class="train-fare">
                <div class="train-fare-inr">&#8377;${(t.fare_inr || 0).toLocaleString('en-IN')}</div>
                <div class="train-fare-class">${t.class || ''}</div>
            </div>
            ${noteHtml}
        </div>
        `;
    }).join('');
}

function renderRoadOptions(roadOptions) {
    if (!roadOptions.length) {
        roadTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No road travel data available. Try searching between Indian cities (e.g. Coimbatore to Chennai).</p>';
        return;
    }

    roadTab.innerHTML = roadOptions.map(r => {
        const mode = (r.mode || 'Bus').toLowerCase();
        let modeIcon = 'fas fa-bus';
        let modeCss = 'mode-bus';
        if (mode === 'cab') { modeIcon = 'fas fa-taxi'; modeCss = 'mode-cab'; }
        if (mode === 'self-drive') { modeIcon = 'fas fa-car'; modeCss = 'mode-self-drive'; }

        const opType = (r.operator_type || '').toLowerCase();
        const opTypeCss = opType === 'government' ? 'govt' : 'private';
        const opTypeLabel = opType === 'government' ? 'Govt' : (mode === 'self-drive' ? 'Self-Drive' : (mode === 'cab' ? 'Cab' : 'Private'));

        return `
        <div class="road-card">
            <div class="road-mode-badge ${modeCss}">
                <i class="${modeIcon}"></i>
            </div>
            <div class="road-operator">
                <h4>${r.operator || 'Unknown'}</h4>
                <div class="road-vehicle">${r.vehicle_type || ''}</div>
                <span class="road-operator-type ${opTypeCss}">${opTypeLabel}</span>
            </div>
            <div class="road-route-info">
                <div class="time-depart">${r.departure_time || 'Flexible'}</div>
                <div class="route-detail">${r.duration || ''}</div>
                <div class="route-detail">${r.distance_km || ''}km &middot; ${r.origin || ''} → ${r.destination || ''}</div>
            </div>
            <div class="road-amenities">
                ${(r.amenities || []).slice(0, 5).map(a => `<span class="amenity-tag">${a}</span>`).join('')}
            </div>
            <div class="road-fare">
                <div class="road-fare-inr">&#8377;${(r.fare_inr || 0).toLocaleString('en-IN')}</div>
                <div class="road-seats"><i class="fas fa-chair"></i> ${r.seats_available || 0} seats</div>
            </div>
        </div>
        `;
    }).join('');
}

function renderItinerary(itinerary) {
    if (!itinerary.length) {
        itineraryTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No itinerary data available.</p>';
        return;
    }

    itineraryTab.innerHTML = itinerary.map(day => `
        <div class="itinerary-day">
            <div class="day-header">
                <div class="day-number">${day.day || '?'}</div>
                <div class="day-theme">${day.theme || 'Day ' + day.day}</div>
            </div>
            <div class="time-slot">
                <div class="time-label">Morning</div>
                <div>
                    <div class="time-activity">${day.morning?.activity || 'Free time'}</div>
                    <div class="time-detail"><i class="fas fa-clock"></i> ${day.morning?.time || ''}</div>
                    ${day.morning?.tip ? `<div class="time-detail" style="color:var(--accent-teal);"><i class="fas fa-lightbulb"></i> ${day.morning.tip}</div>` : ''}
                </div>
            </div>
            <div class="time-slot">
                <div class="time-label">Afternoon</div>
                <div>
                    <div class="time-activity">${day.afternoon?.activity || 'Free time'}</div>
                    <div class="time-detail"><i class="fas fa-clock"></i> ${day.afternoon?.time || ''}</div>
                    ${day.afternoon?.tip ? `<div class="time-detail" style="color:var(--accent-teal);"><i class="fas fa-lightbulb"></i> ${day.afternoon.tip}</div>` : ''}
                </div>
            </div>
            <div class="time-slot">
                <div class="time-label">Evening</div>
                <div>
                    <div class="time-activity">${day.evening?.activity || 'Free time'}</div>
                    <div class="time-detail"><i class="fas fa-clock"></i> ${day.evening?.time || ''}</div>
                    ${day.evening?.tip ? `<div class="time-detail" style="color:var(--accent-teal);"><i class="fas fa-lightbulb"></i> ${day.evening.tip}</div>` : ''}
                </div>
            </div>
            <div class="day-dining">
                <span><i class="fas fa-utensils"></i> Lunch: ${day.dining?.lunch || 'Local restaurant'}</span>
                <span><i class="fas fa-wine-glass-alt"></i> Dinner: ${day.dining?.dinner || 'Local restaurant'}</span>
            </div>
        </div>
    `).join('');
}

function showError(message) {
    resultsSection.style.display = 'block';
    resultsSummary.innerHTML = `
        <div style="color:var(--accent-red); display:flex; align-items:center; gap:0.5rem;">
            <i class="fas fa-exclamation-circle"></i>
            <strong>Error:</strong> ${message}
        </div>
    `;
    flightsTab.innerHTML = '';
    hotelsTab.innerHTML = '';
    trainsTab.innerHTML = '';
    roadTab.innerHTML = '';
    itineraryTab.innerHTML = '';
}

// ─── Chat Widget ───
const chatToggle = document.getElementById('chatToggle');
const chatPanel = document.getElementById('chatPanel');
const chatClose = document.getElementById('chatClose');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const chatSuggestions = document.getElementById('chatSuggestions');
const chatChips = document.querySelectorAll('.chat-chip');

let chatOpen = false;

chatToggle.addEventListener('click', () => {
    chatOpen = true;
    chatPanel.classList.add('open');
    chatToggle.classList.add('active');
    chatInput.focus();
});

chatClose.addEventListener('click', () => {
    chatOpen = false;
    chatPanel.classList.remove('open');
    chatToggle.classList.remove('active');
});

// Send message on Enter
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

chatSend.addEventListener('click', sendChatMessage);

// Suggestion chips
chatChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const msg = chip.dataset.msg;
        chatInput.value = msg;
        sendChatMessage();
    });
});

function addChatMsg(type, html) {
    const iconClass = type === 'bot' ? 'fa-robot' : 'fa-user';
    const div = document.createElement('div');
    div.className = `chat-msg ${type}`;
    div.innerHTML = `
        <div class="chat-msg-avatar"><i class="fas ${iconClass}"></i></div>
        <div class="chat-msg-bubble">${html}</div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.id = 'chatTyping';
    div.innerHTML = `
        <div class="chat-msg-avatar"><i class="fas fa-robot"></i></div>
        <div class="chat-msg-bubble">
            <div class="chat-typing"><span></span><span></span><span></span></div>
            <div style="font-size:0.65rem; color:var(--text-muted); margin-top:0.2rem;">Agents working...</div>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
    const t = document.getElementById('chatTyping');
    if (t) t.remove();
}

function formatReply(text) {
    // Simple markdown-like formatting
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/₹/g, '&#8377;');
}

async function sendChatMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Add user message
    addChatMsg('user', msg);
    chatInput.value = '';
    chatSend.disabled = true;

    // Hide suggestions after first use
    chatSuggestions.style.display = 'none';

    // Show typing indicator
    showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });

        const result = await response.json();
        removeTyping();

        if (result.reply) {
            addChatMsg('bot', formatReply(result.reply));
        }

        // If pipeline returned results, render them in the main UI too
        if (result.has_results && result.data && result.params) {
            // Fill form with parsed params
            document.getElementById('origin').value = result.params.origin || '';
            document.getElementById('destination').value = result.params.destination || '';
            document.getElementById('departure_date').value = result.params.departure_date || '';
            document.getElementById('return_date').value = result.params.return_date || '';
            document.getElementById('budget').value = result.params.budget || 'moderate';
            document.getElementById('travelers').value = result.params.travelers || 2;
            document.getElementById('interests').value = result.params.interests || '';

            // Show pipeline & results
            resetAllAgents();
            resetPipeline();
            showPipeline();
            await animatePipeline();
            renderResults(result.data, result.params);
        }

    } catch (err) {
        removeTyping();
        addChatMsg('bot', 'Sorry, I couldn\'t connect to the server. Please make sure it\'s running.');
    } finally {
        chatSend.disabled = false;
        chatInput.focus();
    }
}
