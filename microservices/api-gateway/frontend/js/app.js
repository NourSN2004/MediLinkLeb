// MediLink Frontend - Service Status Checker

const SERVICES = [
    { name: 'Auth Service', endpoint: '/api/auth/health/live/' },
    { name: 'Doctor Service', endpoint: '/api/doctors/health/live/' },
    { name: 'Patient Service', endpoint: '/api/patients/health/live/' },
    { name: 'Pharmacy Service', endpoint: '/api/pharmacies/health/live/' },
    { name: 'Scheduling Service', endpoint: '/api/appointments/health/live/' },
    { name: 'Inventory Service', endpoint: '/api/medicines/health/live/' },
    { name: 'Notification Service', endpoint: '/api/notifications/health/live/' }
];

async function checkServiceHealth(service) {
    try {
        const response = await fetch(service.endpoint, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            return { ...service, status: 'healthy' };
        } else {
            return { ...service, status: 'unhealthy' };
        }
    } catch (error) {
        return { ...service, status: 'unknown', error: error.message };
    }
}

async function checkAllServices() {
    const statusContainer = document.getElementById('service-status');
    statusContainer.innerHTML = '<p>Checking services...</p>';

    try {
        const results = await Promise.all(SERVICES.map(checkServiceHealth));

        let html = '';
        results.forEach(result => {
            const statusClass = result.status === 'healthy' ? 'status-healthy' :
                              result.status === 'unhealthy' ? 'status-unhealthy' : 'status-unknown';

            html += `
                <div class="service-item">
                    <span class="status-indicator ${statusClass}"></span>
                    <strong>${result.name}:</strong> ${result.status.toUpperCase()}
                    ${result.error ? ` (${result.error})` : ''}
                </div>
            `;
        });

        statusContainer.innerHTML = html;
    } catch (error) {
        statusContainer.innerHTML = `<p style="color: #f5222d;">Error checking services: ${error.message}</p>`;
    }
}

// Check services on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAllServices();

    // Refresh every 30 seconds
    setInterval(checkAllServices, 30000);
});

// Add click handler to manually refresh
document.addEventListener('DOMContentLoaded', () => {
    const statusSection = document.querySelector('.status h3');
    if (statusSection) {
        statusSection.style.cursor = 'pointer';
        statusSection.title = 'Click to refresh';
        statusSection.addEventListener('click', checkAllServices);
    }
});
