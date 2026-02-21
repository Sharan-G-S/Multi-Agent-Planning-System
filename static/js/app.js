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
const itineraryTab = document.getElementById('itineraryTab');

const flightCount = document.getElementById('flightCount');
const hotelCount = document.getElementById('hotelCount');
const trainCount = document.getElementById('trainCount');
const itineraryCount = document.getElementById('itineraryCount');

// Agent cards
const agentCards = {
    flight: document.getElementById('agent-flight'),
    hotel: document.getElementById('agent-hotel'),
    itinerary: document.getElementById('agent-itinerary'),
    train: document.getElementById('agent-train'),
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
    const steps = ['collect_input', 'search_flights', 'search_hotels', 'search_trains', 'build_itinerary', 'compile_results'];
    const agentMapping = {
        'search_flights': 'flight',
        'search_hotels': 'hotel',
        'search_trains': 'train',
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
    itineraryCount.textContent = itinerary.length + (itinerary.length === 1 ? ' day' : ' days');

    // Render flights
    renderFlights(flights);

    // Render hotels
    renderHotels(hotels);

    // Render trains
    renderTrains(trains);

    // Render itinerary
    renderItinerary(itinerary);

    // Show flights tab by default
    tabBtns.forEach(b => b.classList.remove('active'));
    tabBtns[0].classList.add('active');
    flightsTab.style.display = 'block';
    hotelsTab.style.display = 'none';
    trainsTab.style.display = 'none';
    itineraryTab.style.display = 'none';
}

function renderFlights(flights) {
    if (!flights.length) {
        flightsTab.innerHTML = '<p style="color:var(--text-muted); padding:1rem;">No flight data available.</p>';
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
                <div class="flight-price-amount">$${(f.price_usd || 0).toFixed(2)}</div>
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
                <div class="hotel-price-amount">$${(h.price_per_night_usd || 0).toFixed(2)}</div>
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

    trainsTab.innerHTML = trains.map(t => {
        const availClass = (t.availability || '').toLowerCase().replace(' ', '');
        let availCss = 'avail-available';
        if (availClass === 'rac') availCss = 'avail-rac';
        if (availClass === 'waitlist') availCss = 'avail-waitlist';

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
                <div class="train-fare-usd">~$${(t.fare_usd || 0).toFixed(2)} USD</div>
                <div class="train-fare-class">${t.class || ''}</div>
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
    itineraryTab.innerHTML = '';
}
