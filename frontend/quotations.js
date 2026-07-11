const CLIENTS = {
    1: 'Aeroflot',
    2: 'Belavia',
    3: 'UTair',
    4: 'Pobeda',
};

const PAGE_SIZE = 10;

const clientHeadersRow = document.getElementById('clientHeadersRow');
const lettersPanel = document.getElementById('lettersPanel');
const lettersStatus = document.getElementById('lettersStatus');
const lettersList = document.getElementById('lettersList');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const pageIndicator = document.getElementById('pageIndicator');

let activeClientId = null;
let expandedLetterKeys = new Set();
const clientStates = {};

document.addEventListener('DOMContentLoaded', init);

function init() {
    clientHeadersRow.addEventListener('click', onClientHeaderClick);
    prevPageBtn.addEventListener('click', onPreviousPage);
    nextPageBtn.addEventListener('click', onNextPage);
}

function createClientState() {
    return {
        pageCursors: [null],
        currentPageIndex: 0,
        nextCursor: null,
        items: [],
        loading: false,
    };
}

function getClientState(clientId) {
    if (!clientStates[clientId]) {
        clientStates[clientId] = createClientState();
    }
    return clientStates[clientId];
}

function onClientHeaderClick(event) {
    const button = event.target.closest('.client-header-btn');
    if (!button) {
        return;
    }

    const clientId = Number(button.dataset.clientId);
    if (activeClientId === clientId) {
        return;
    }

    activeClientId = clientId;
    expandedLetterKeys = new Set();
    updateClientHeaderButtons();
    lettersPanel.hidden = false;
    loadLettersPage(clientId, 0);
}

function updateClientHeaderButtons() {
    clientHeadersRow.querySelectorAll('.client-header-btn').forEach((button) => {
        const isActive = Number(button.dataset.clientId) === activeClientId;
        button.classList.toggle('active', isActive);
    });
}

async function loadLettersPage(clientId, pageIndex) {
    const state = getClientState(clientId);
    state.loading = true;
    showLettersStatus('Loading quotations…', 'info');
    renderLetters([]);
    updatePaginationControls(state);

    try {
        const cursor = state.pageCursors[pageIndex] ?? null;
        const data = await fetchLetters(clientId, cursor);
        state.items = data.items || [];
        state.nextCursor = data.next_cursor || null;
        state.currentPageIndex = pageIndex;

        if (data.next_cursor) {
            state.pageCursors[pageIndex + 1] = data.next_cursor;
        } else {
            state.pageCursors = state.pageCursors.slice(0, pageIndex + 1);
        }

        hideLettersStatus();

        if (state.items.length === 0) {
            showLettersStatus(`No quotations found for ${CLIENTS[clientId]}.`, 'info');
        }

        renderLetters(state.items);
        updatePaginationControls(state);
    } catch (error) {
        showLettersStatus(error.message, 'error');
        renderLetters([]);
        updatePaginationControls(state);
    } finally {
        state.loading = false;
    }
}

async function fetchLetters(clientId, cursor) {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE) });

    if (cursor) {
        params.set('after_job_id', cursor.job_id);
        params.set('after_received_at', cursor.received_at);
    }

    const response = await fetch(
        `${RFQ_VIEWER_API_BASE_URL}/clients/${clientId}/rfqs?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
    }

    return response.json();
}

function renderLetters(items) {
    if (!items.length) {
        lettersList.innerHTML = '';
        return;
    }

    lettersList.innerHTML = items.map((item, index) => {
        const letterKey = getLetterKey(item, index);
        const isExpanded = expandedLetterKeys.has(letterKey);
        const subject = escapeHtml(item.subject || '(No subject)');
        const receivedAt = formatReceivedAt(item.received_at);
        const partsCount = Array.isArray(item.parts) ? item.parts.length : 0;

        return `
            <div class="letter-item">
                <div class="letter-row ${isExpanded ? 'expanded' : ''}" data-letter-key="${escapeHtml(letterKey)}" role="button" tabindex="0">
                    <span class="letter-caret" aria-hidden="true">${isExpanded ? '▾' : '▸'}</span>
                    <span class="letter-subject" title="${subject}">${subject}</span>
                    <span class="letter-time">${receivedAt}</span>
                    <span class="letter-parts-count">${partsCount} part${partsCount === 1 ? '' : 's'}</span>
                </div>
                <div class="letter-details ${isExpanded ? '' : 'hidden'}" data-letter-key="${escapeHtml(letterKey)}">
                    ${renderPartsTable(item.parts || [])}
                </div>
            </div>
        `;
    }).join('');

    lettersList.querySelectorAll('.letter-row').forEach((row) => {
        row.addEventListener('click', onLetterRowClick);
        row.addEventListener('keydown', onLetterRowKeydown);
    });
}

function onLetterRowClick(event) {
    toggleLetterExpansion(event.currentTarget.dataset.letterKey);
}

function onLetterRowKeydown(event) {
    if (event.key !== 'Enter' && event.key !== ' ') {
        return;
    }

    event.preventDefault();
    toggleLetterExpansion(event.currentTarget.dataset.letterKey);
}

function toggleLetterExpansion(letterKey) {
    if (expandedLetterKeys.has(letterKey)) {
        expandedLetterKeys.delete(letterKey);
    } else {
        expandedLetterKeys.add(letterKey);
    }

    const state = getClientState(activeClientId);
    renderLetters(state.items);
}

function renderPartsTable(parts) {
    if (!parts.length) {
        return '<p class="no-items">No parts in this quotation.</p>';
    }

    const rows = parts.map((part) => {
        const partNumber = escapeHtml(part.part_number || '—');
        const description = escapeHtml(part.description ?? '—');
        const quantity = part.quantity != null ? escapeHtml(String(part.quantity)) : '—';
        const alternatives = Array.isArray(part.alternatives) && part.alternatives.length
            ? escapeHtml(part.alternatives.join(', '))
            : '—';

        return `
            <tr>
                <td class="col-part-number">${partNumber}</td>
                <td class="col-description">${description}</td>
                <td class="col-quantity">${quantity}</td>
                <td class="col-alternatives">${alternatives}</td>
            </tr>
        `;
    }).join('');

    return `
        <div class="parts-table-container">
            <table class="parts-table">
                <colgroup>
                    <col class="col-part-number">
                    <col class="col-description">
                    <col class="col-quantity">
                    <col class="col-alternatives">
                </colgroup>
                <thead>
                    <tr>
                        <th>Part Number</th>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Alternatives</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

function updatePaginationControls(state) {
    const pageNumber = state.currentPageIndex + 1;
    pageIndicator.textContent = `Page ${pageNumber}`;
    prevPageBtn.disabled = state.loading || state.currentPageIndex === 0;
    nextPageBtn.disabled = state.loading || !state.nextCursor;
}

function onPreviousPage() {
    if (activeClientId == null) {
        return;
    }

    const state = getClientState(activeClientId);
    if (state.currentPageIndex === 0 || state.loading) {
        return;
    }

    expandedLetterKeys = new Set();
    loadLettersPage(activeClientId, state.currentPageIndex - 1);
}

function onNextPage() {
    if (activeClientId == null) {
        return;
    }

    const state = getClientState(activeClientId);
    if (!state.nextCursor || state.loading) {
        return;
    }

    expandedLetterKeys = new Set();
    loadLettersPage(activeClientId, state.currentPageIndex + 1);
}

function showLettersStatus(message, type) {
    lettersStatus.hidden = false;
    lettersStatus.textContent = message;
    lettersStatus.className = `letters-status letters-status-${type}`;
}

function hideLettersStatus() {
    lettersStatus.hidden = true;
    lettersStatus.textContent = '';
    lettersStatus.className = 'letters-status';
}

function getLetterKey(item, index) {
    const state = getClientState(activeClientId);
    return `${activeClientId}-${state.currentPageIndex}-${index}`;
}

function formatReceivedAt(value) {
    if (!value) {
        return '—';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return escapeHtml(String(value));
    }

    return date.toLocaleString();
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
