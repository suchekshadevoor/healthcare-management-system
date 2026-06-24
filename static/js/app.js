const translations = {
    en: {
        home: "Home",
        hospitals: "Hospitals",
        doctors: "Doctors",
        appointments: "Appointments",
        map: "Map",
        chatbot: "Chatbot",
        logout: "Logout",
        login: "Login",
        register: "Register",
        email: "Email",
        password: "Password",
        confirm_password: "Confirm Password",
        name: "Name",
        no_account: "Don't have an account?",
        have_account: "Already have an account?",
        dashboard: "Dashboard",
        dashboard_subtitle: "Manage hospital search, doctors, appointments, maps, and basic healthcare help.",
        beds_available: "Beds Available",
        quick_actions: "Quick Actions",
        hospital_management: "Hospital Management",
        hospital_subtitle: "Data is fetched dynamically from SQLite after CSV import.",
        all_hospitals: "All Hospitals",
        filter: "Filter",
        city: "City",
        doctor_management: "Doctor Management",
        doctor_subtitle: "Doctors are linked to hospitals through the database.",
        specialization: "Specialization",
        experience: "Experience",
        availability: "Availability",
        book_now: "Book Now",
        appointment_booking: "Appointment Booking",
        appointment_subtitle: "Select hospital, doctor, date, and time. Booked slots cannot be duplicated.",
        book_appointment: "Book Appointment",
        select_hospital: "Select Hospital",
        select_doctor: "Select Doctor",
        date: "Date",
        time: "Time",
        confirm_booking: "Confirm Booking",
        booking_history: "Booking History",
        hospital_map: "Hospital Map",
        map_subtitle: "Leaflet markers use latitude and longitude stored in SQLite.",
        chatbot_title: "Healthcare Chatbot",
        chatbot_subtitle: "Basic placeholder chatbot with static responses.",
        send: "Send"
    },
    kn: {
        home: "ಮುಖಪುಟ",
        hospitals: "ಆಸ್ಪತ್ರೆಗಳು",
        doctors: "ವೈದ್ಯರು",
        appointments: "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಳು",
        map: "ನಕ್ಷೆ",
        chatbot: "ಚಾಟ್‌ಬಾಟ್",
        logout: "ಲಾಗ್ ಔಟ್",
        login: "ಲಾಗಿನ್",
        register: "ನೋಂದಣಿ",
        email: "ಇಮೇಲ್",
        password: "ಪಾಸ್‌ವರ್ಡ್",
        confirm_password: "ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ",
        name: "ಹೆಸರು",
        no_account: "ಖಾತೆ ಇಲ್ಲವೇ?",
        have_account: "ಈಗಾಗಲೇ ಖಾತೆ ಇದೆಯೇ?",
        dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        dashboard_subtitle: "ಆಸ್ಪತ್ರೆ ಹುಡುಕಾಟ, ವೈದ್ಯರು, ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಳು, ನಕ್ಷೆ ಮತ್ತು ಮೂಲ ಆರೋಗ್ಯ ಸಹಾಯವನ್ನು ನಿರ್ವಹಿಸಿ.",
        beds_available: "ಲಭ್ಯವಿರುವ ಹಾಸಿಗೆಗಳು",
        quick_actions: "ತ್ವರಿತ ಕ್ರಮಗಳು",
        hospital_management: "ಆಸ್ಪತ್ರೆ ನಿರ್ವಹಣೆ",
        hospital_subtitle: "CSV ಆಮದು ನಂತರ SQLite ನಿಂದ ಡೇಟಾ ಡೈನಾಮಿಕ್ ಆಗಿ ಪಡೆಯಲಾಗುತ್ತದೆ.",
        all_hospitals: "ಎಲ್ಲಾ ಆಸ್ಪತ್ರೆಗಳು",
        filter: "ಫಿಲ್ಟರ್",
        city: "ನಗರ",
        doctor_management: "ವೈದ್ಯರ ನಿರ್ವಹಣೆ",
        doctor_subtitle: "ವೈದ್ಯರನ್ನು ಡೇಟಾಬೇಸ್ ಮೂಲಕ ಆಸ್ಪತ್ರೆಗಳಿಗೆ ಸಂಪರ್ಕಿಸಲಾಗಿದೆ.",
        specialization: "ವಿಶೇಷತೆ",
        experience: "ಅನುಭವ",
        availability: "ಲಭ್ಯತೆ",
        book_now: "ಈಗ ಬುಕ್ ಮಾಡಿ",
        appointment_booking: "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕ್ಕಿಂಗ್",
        appointment_subtitle: "ಆಸ್ಪತ್ರೆ, ವೈದ್ಯರು, ದಿನಾಂಕ ಮತ್ತು ಸಮಯ ಆಯ್ಕೆಮಾಡಿ. ಬುಕ್ ಆದ ಸಮಯವನ್ನು ಮರುಬುಕ್ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        book_appointment: "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬುಕ್ ಮಾಡಿ",
        select_hospital: "ಆಸ್ಪತ್ರೆ ಆಯ್ಕೆಮಾಡಿ",
        select_doctor: "ವೈದ್ಯರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        date: "ದಿನಾಂಕ",
        time: "ಸಮಯ",
        confirm_booking: "ಬುಕ್ಕಿಂಗ್ ದೃಢೀಕರಿಸಿ",
        booking_history: "ಬುಕಿಂಗ್ ಇತಿಹಾಸ",
        hospital_map: "ಆಸ್ಪತ್ರೆ ನಕ್ಷೆ",
        map_subtitle: "Leaflet ಮಾರ್ಕರ್‌ಗಳು SQLite ನಲ್ಲಿ ಇರುವ latitude ಮತ್ತು longitude ಬಳಸುತ್ತವೆ.",
        chatbot_title: "ಆರೋಗ್ಯ ಚಾಟ್‌ಬಾಟ್",
        chatbot_subtitle: "ಸ್ಥಿರ ಉತ್ತರಗಳೊಂದಿಗೆ ಮೂಲ ಚಾಟ್‌ಬಾಟ್.",
        send: "ಕಳುಹಿಸಿ"
    }
};

function applyLanguage(language) {
    const dictionary = translations[language] || translations.en;
    document.querySelectorAll("[data-i18n]").forEach((element) => {
        const key = element.dataset.i18n;
        if (dictionary[key]) {
            element.textContent = dictionary[key];
        }
    });
    localStorage.setItem("careconnect_language", language);
}

const languageSelect = document.getElementById("languageSelect");
if (languageSelect) {
    const savedLanguage = localStorage.getItem("careconnect_language") || "en";
    languageSelect.value = savedLanguage;
    applyLanguage(savedLanguage);
    languageSelect.addEventListener("change", (event) => applyLanguage(event.target.value));
}

const hospitalSelect = document.getElementById("hospitalSelect");
const doctorSelect = document.getElementById("doctorSelect");
if (hospitalSelect && doctorSelect) {
    const allDoctorOptions = Array.from(doctorSelect.querySelectorAll("option")).slice(1);

    function filterDoctors() {
        const hospitalId = hospitalSelect.value;
        const selectedDoctor = doctorSelect.dataset.selected;
        doctorSelect.innerHTML = '<option value="">Choose doctor</option>';

        allDoctorOptions.forEach((option) => {
            if (!hospitalId || option.dataset.hospital === hospitalId) {
                const clone = option.cloneNode(true);
                if (selectedDoctor && clone.value === selectedDoctor) {
                    clone.selected = true;
                }
                doctorSelect.appendChild(clone);
            }
        });
    }

    hospitalSelect.addEventListener("change", () => {
        doctorSelect.dataset.selected = "";
        filterDoctors();
    });
    filterDoctors();
}

const chatForm = document.getElementById("chatForm");
if (chatForm) {
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");

    function addMessage(text, className) {
        const bubble = document.createElement("div");
        bubble.className = className;
        bubble.textContent = text;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        addMessage(message, "user-message");
        chatInput.value = "";

        const response = await fetch("/api/chatbot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        addMessage(data.reply, "bot-message");
    });
}

const leafletMap = document.getElementById("leafletMap");
if (leafletMap && window.L) {
    const hospitals = JSON.parse(leafletMap.dataset.hospitals || "[]");
    const first = hospitals[0] || { lat: 16.8302, lng: 75.7100 };
    const map = L.map("leafletMap").setView([first.lat, first.lng], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }).addTo(map);

    hospitals.forEach((hospital) => {
        L.marker([hospital.lat, hospital.lng])
            .addTo(map)
            .bindPopup(`
                <strong>${hospital.name}</strong><br>
                ${hospital.type} - ${hospital.city}<br>
                Beds: ${hospital.beds}<br>
                Oxygen: ${hospital.oxygen}
            `);
    });
}
