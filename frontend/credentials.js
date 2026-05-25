let portals = [];

const credentialsList = document.getElementById('credentialsList');
const saveCredentialsBtn = document.getElementById('saveCredentialsBtn');
const credentialsStatus = document.getElementById('credentialsStatus');

document.addEventListener('DOMContentLoaded', init);

saveCredentialsBtn.addEventListener('click', saveAllCredentials);

function init() {
    fetchConfig();
}

async function fetchConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/config`);
        if (!response.ok) {
            throw new Error(await parseErrorResponse(response));
        }

        const data = await response.json();
        portals = data.portals || [];
        renderCredentialsForm();
        saveCredentialsBtn.disabled = portals.length === 0;
    } catch (error) {
        credentialsList.innerHTML = `<p class="error-text">Failed to load portals: ${error.message}</p>`;
    }
}

function renderCredentialsForm() {
    if (portals.length === 0) {
        credentialsList.innerHTML = '<p class="loading-text">No portals configured.</p>';
        return;
    }

    credentialsList.innerHTML = '';

    portals.forEach(portal => {
        const stored = getStoredCredentials(portal.id);
        const row = document.createElement('div');
        row.className = 'credential-item';
        row.innerHTML = `
            <div class="credential-portal-name">${portal.name}</div>
            <div class="credential-fields">
                <input type="text" class="form-input credential-username"
                    placeholder="Username" data-portal-id="${portal.id}"
                    value="${escapeHtml(stored.username)}" autocomplete="username">
                <input type="password" class="form-input credential-password"
                    placeholder="Password" data-portal-id="${portal.id}"
                    value="${escapeHtml(stored.password)}" autocomplete="current-password">
            </div>
        `;
        credentialsList.appendChild(row);

        row.querySelector('.credential-username').addEventListener('change', (e) => {
            const id = parseInt(e.target.dataset.portalId, 10);
            const password = row.querySelector('.credential-password').value;
            saveStoredCredentials(id, e.target.value, password);
        });

        row.querySelector('.credential-password').addEventListener('change', (e) => {
            const id = parseInt(e.target.dataset.portalId, 10);
            const username = row.querySelector('.credential-username').value;
            saveStoredCredentials(id, username, e.target.value);
        });
    });
}

async function saveAllCredentials() {
    const payload = portals.map(portal => {
        const row = credentialsList.querySelector(`.credential-username[data-portal-id="${portal.id}"]`).closest('.credential-item');
        const username = row.querySelector('.credential-username').value;
        const password = row.querySelector('.credential-password').value;
        saveStoredCredentials(portal.id, username, password);
        return {
            portal_id: portal.id,
            username,
            password
        };
    });

    saveCredentialsBtn.disabled = true;
    showStatus('info', 'Saving credentials…');

    try {
        const response = await fetch(`${API_BASE_URL}/save-credentials`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(await parseErrorResponse(response));
        }

        const results = await response.json();
        const failed = results.filter(r => !r.success);

        if (failed.length === 0) {
            showStatus('success', 'Credentials saved for all portals.');
        } else {
            const names = failed.map(r => getPortalName(r.portal_id)).join(', ');
            showStatus('warning', `Saved with errors for: ${names}`);
        }
    } catch (error) {
        showStatus('error', error.message);
    } finally {
        saveCredentialsBtn.disabled = false;
    }
}

function getPortalName(portalId) {
    const portal = portals.find(p => p.id === portalId);
    return portal ? portal.name : `Portal ${portalId}`;
}

function showStatus(type, message) {
    credentialsStatus.hidden = false;
    credentialsStatus.className = `credentials-status credentials-status-${type}`;
    credentialsStatus.textContent = message;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
