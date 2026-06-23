const pageType = document.body.dataset.page;
const isAdmin = document.body.dataset.admin === 'true';

window.addEventListener('DOMContentLoaded', () => {
    if (pageType === 'dashboard') {
        initDashboard();
    }
});

function initDashboard() {
    const searchInput = document.getElementById('searchHospital');
    const bedsOnly = document.getElementById('bedsOnly');
    const doctorsOnly = document.getElementById('doctorsOnly');
    const emergencyOnly = document.getElementById('emergencyOnly');
    const resetFilters = document.getElementById('resetFilters');
    const hospitalGrid = document.getElementById('hospitalGrid');

    const refreshList = debounce(async () => {
        showLoading(true);
        const hospitals = await fetchHospitals();
        renderHospitalList(hospitals);
        showLoading(false);
    }, 250);

    searchInput?.addEventListener('input', refreshList);
    bedsOnly?.addEventListener('change', refreshList);
    doctorsOnly?.addEventListener('change', refreshList);
    emergencyOnly?.addEventListener('change', refreshList);
    resetFilters?.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        if (bedsOnly) bedsOnly.checked = false;
        if (doctorsOnly) doctorsOnly.checked = false;
        if (emergencyOnly) emergencyOnly.checked = false;
        refreshList();
    });

    hospitalGrid?.addEventListener('click', async (event) => {
        const target = event.target;
        if (!target.classList.contains('button-update')) {
            return;
        }

        const card = target.closest('.hospital-card');
        if (!card) {
            return;
        }

        const id = card.dataset.id;
        const beds = Number(card.querySelector('[name="beds"]').value);
        const doctors = Number(card.querySelector('[name="doctors"]').value);
        const emergency = Number(card.querySelector('[name="emergency"]').value);

        await updateAvailability({ id, beds, doctors, emergency });
        refreshList();
    });

    refreshList();
    setInterval(refreshList, 15000);
}

async function fetchHospitals() {
    const searchValue = document.getElementById('searchHospital')?.value || '';
    const bedsOnly = document.getElementById('bedsOnly')?.checked;
    const doctorsOnly = document.getElementById('doctorsOnly')?.checked;
    const emergencyOnly = document.getElementById('emergencyOnly')?.checked;

    const params = new URLSearchParams();
    if (searchValue) params.set('search', searchValue);
    if (bedsOnly) params.set('beds', 'true');
    if (doctorsOnly) params.set('doctors', 'true');
    if (emergencyOnly) params.set('emergency', 'true');

    const response = await fetch(`/api/hospitals?${params.toString()}`);
    if (!response.ok) {
        console.error('Failed to load hospital data');
        return [];
    }

    return response.json();
}

function renderHospitalList(hospitals) {
    const hospitalGrid = document.getElementById('hospitalGrid');
    const emptyState = document.getElementById('dashboardEmpty');
    const statHospitals = document.getElementById('statHospitals');
    const statBeds = document.getElementById('statBeds');
    const statDoctors = document.getElementById('statDoctors');
    const statEmergency = document.getElementById('statEmergency');

    if (!hospitalGrid || !statHospitals || !statBeds || !statDoctors || !statEmergency || !emptyState) {
        return;
    }

    if (hospitals.length === 0) {
        hospitalGrid.innerHTML = '';
        emptyState.classList.remove('hidden');
        statHospitals.textContent = '0';
        statBeds.textContent = '0';
        statDoctors.textContent = '0';
        statEmergency.textContent = '0';
        return;
    }

    emptyState.classList.add('hidden');
    hospitalGrid.innerHTML = hospitals.map(renderHospitalCard).join('');

    const totals = hospitals.reduce((acc, hospital) => {
        acc.beds += Number(hospital.beds);
        acc.doctors += Number(hospital.doctors);
        acc.emergency += Number(hospital.emergency);
        return acc;
    }, { beds: 0, doctors: 0, emergency: 0 });

    statHospitals.textContent = String(hospitals.length);
    statBeds.textContent = String(totals.beds);
    statDoctors.textContent = String(totals.doctors);
    statEmergency.textContent = String(totals.emergency);
}

function renderHospitalCard(hospital) {
    const emergencyStatus = hospital.emergency > 0 ? 'Online' : 'Offline';
    const adminSection = isAdmin ? `
        <div class="admin-controls">
            <label>
                Beds available
                <input name="beds" type="number" min="0" value="${hospital.beds}" />
            </label>
            <label>
                Doctors available
                <input name="doctors" type="number" min="0" value="${hospital.doctors}" />
            </label>
            <label>
                Emergency units
                <input name="emergency" type="number" min="0" value="${hospital.emergency}" />
            </label>
            <button type="button" class="button button-primary button-update">Save update</button>
        </div>
    ` : '';

    return `
        <article class="hospital-card" data-id="${hospital.id}">
            <div class="hospital-card-header">
                <div>
                    <h3>${hospital.name}</h3>
                    <p>${hospital.location}</p>
                </div>
                <span class="badge ${hospital.emergency > 0 ? 'status-ok' : 'status-low'}">${emergencyStatus}</span>
            </div>
            <div class="hospital-stats">
                <div><strong>${hospital.beds}</strong><span>Beds</span></div>
                <div><strong>${hospital.doctors}</strong><span>Doctors</span></div>
                <div><strong>${hospital.emergency}</strong><span>Emergency</span></div>
            </div>
            ${adminSection}
        </article>
    `;
}

function showLoading(show) {
    const loadingState = document.getElementById('loadingState');
    loadingState?.classList.toggle('hidden', !show);
}

async function updateAvailability(payload) {
    const response = await fetch('/update-availability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok) {
        toast(result.message || 'Unable to update availability.');
        return;
    }

    toast(result.message || 'Availability updated.');
}

function toast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3200);
}

function debounce(callback, delay = 180) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => callback(...args), delay);
    };
}
