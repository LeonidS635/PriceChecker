const API_BASE_URL = 'http://localhost:8081';

function getStoredCredentials(portalId) {
    return {
        username: localStorage.getItem(`username-${portalId}`) || '',
        password: localStorage.getItem(`password-${portalId}`) || ''
    };
}

function saveStoredCredentials(portalId, username, password) {
    localStorage.setItem(`username-${portalId}`, username);
    localStorage.setItem(`password-${portalId}`, password);
}

async function parseErrorResponse(response) {
    const errorText = await response.text();
    let errorMessage = `HTTP error! status: ${response.status}`;

    try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorMessage;
    } catch (e) {
        if (errorText) {
            errorMessage = `${errorMessage}: ${errorText}`;
        }
    }

    return errorMessage;
}
