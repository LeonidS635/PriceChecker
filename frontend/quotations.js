const CLIENTS = {
    1: 'Aeroflot',
    2: 'Belavia',
    3: 'UTair',
    4: 'Pobeda',
};

const PAGE_SIZE = 50;
const PENDING_SEARCH_PARTS_KEY = 'pendingSearchParts';

const clientHeadersRow = document.getElementById('clientHeadersRow');
const lettersPanel = document.getElementById('lettersPanel');
const lettersStatus = document.getElementById('lettersStatus');
const rfqTableWrap = document.getElementById('rfqTableWrap');
const rfqTableBody = document.getElementById('rfqTableBody');
const rfqScrollSentinel = document.getElementById('rfqScrollSentinel');
const rfqLoadMoreStatus = document.getElementById('rfqLoadMoreStatus');
const selectedPartsToggle = document.getElementById('selectedPartsToggle');
const selectedPartsDetails = document.getElementById('selectedPartsDetails');
const selectedPartsCount = document.getElementById('selectedPartsCount');
const selectedPartsNumbersHint = document.getElementById('selectedPartsNumbersHint');
const selectedPartsList = document.getElementById('selectedPartsList');
const clearSelectedParts = document.getElementById('clearSelectedParts');
const searchSelectedParts = document.getElementById('searchSelectedParts');

let activeClientId = null;
const clientStates = {};
let scrollObserver = null;

/** @type {Map<string, { partNumber: string, alternatives: string[] }>} */
const selectedRows = new Map();

/** @type {Set<string>} */
const excludedPartNumbers = new Set();

document.addEventListener('DOMContentLoaded', init);

function init() {
    clientHeadersRow.addEventListener('click', onClientHeaderClick);
    rfqTableBody.addEventListener('change', onRowCheckboxChange);
    selectedPartsToggle.addEventListener('click', toggleSelectedPartsDetails);
    clearSelectedParts.addEventListener('click', clearSelection);
    searchSelectedParts.addEventListener('click', startSearchWithSelectedParts);
    selectedPartsList.addEventListener('click', onSelectedPartsListClick);
    setupScrollObserver();
    updateSelectedPartsBar();
}

function createClientState() {
    return {
        items: [],
        nextCursor: null,
        hasNext: false,
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
    updateClientHeaderButtons();
    lettersPanel.hidden = false;
    resetAndLoad(clientId);
}

function updateClientHeaderButtons() {
    clientHeadersRow.querySelectorAll('.client-header-btn').forEach((button) => {
        const isActive = Number(button.dataset.clientId) === activeClientId;
        button.classList.toggle('active', isActive);
    });
}

function resetAndLoad(clientId) {
    const state = getClientState(clientId);
    state.items = [];
    state.nextCursor = null;
    state.hasNext = false;
    renderTable([]);
    hideLoadMoreStatus();
    loadMore(clientId, true);
}

async function loadMore(clientId, isInitial = false) {
    const state = getClientState(clientId);
    if (state.loading) {
        return;
    }
    if (!isInitial && !state.hasNext) {
        return;
    }

    state.loading = true;

    if (isInitial) {
        showLettersStatus('Loading quotations…', 'info');
        rfqTableWrap.hidden = true;
    } else {
        showLoadMoreStatus('Loading more…');
    }

    let shouldContinue = false;

    try {
        const after = isInitial ? null : state.nextCursor;
        const data = await fetchLetters(clientId, after);
        const newItems = data.items || [];
        const pagination = data.pagination || {};

        if (isInitial) {
            state.items = newItems;
        } else {
            state.items = mergeRfqs(state.items, newItems);
        }

        state.hasNext = Boolean(pagination.has_next);
        state.nextCursor = pagination.next || null;

        hideLettersStatus();
        hideLoadMoreStatus();

        if (state.items.length === 0) {
            rfqTableWrap.hidden = true;
            showLettersStatus(`No quotations found for ${CLIENTS[clientId]}.`, 'info');
        } else {
            rfqTableWrap.hidden = false;
            renderTable(state.items);
        }

        updateScrollSentinel(state);
        shouldContinue = true;
    } catch (error) {
        if (isInitial) {
            rfqTableWrap.hidden = true;
            renderTable([]);
            showLettersStatus(error.message, 'error');
        } else {
            showLoadMoreStatus(error.message, true);
        }
        updateScrollSentinel(state);
    } finally {
        state.loading = false;
    }

    if (shouldContinue) {
        maybeContinueLoading(clientId);
    }
}

function maybeContinueLoading(clientId) {
    if (activeClientId !== clientId) {
        return;
    }

    const state = getClientState(clientId);
    if (!state.hasNext || state.loading || rfqTableWrap.hidden || rfqScrollSentinel.hidden) {
        return;
    }

    const rootRect = rfqTableWrap.getBoundingClientRect();
    const sentinelRect = rfqScrollSentinel.getBoundingClientRect();
    if (sentinelRect.top <= rootRect.bottom + 80) {
        loadMore(clientId, false);
    }
}

async function fetchLetters(clientId, afterCursor) {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE) });

    if (afterCursor) {
        params.set('after', afterCursor);
    }

    const response = await fetch(
        `${RFQ_VIEWER_API_BASE_URL}/clients/${clientId}/rfqs?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
    }

    return response.json();
}

function mergeRfqs(existing, incoming) {
    if (!incoming.length) {
        return existing;
    }
    if (!existing.length) {
        return incoming.slice();
    }

    const result = existing.slice();
    const last = result[result.length - 1];
    const first = incoming[0];

    if (sameRfq(last, first)) {
        result[result.length - 1] = {
            ...last,
            parts: [...(last.parts || []), ...(first.parts || [])],
        };
        return result.concat(incoming.slice(1));
    }

    return result.concat(incoming);
}

function sameRfq(a, b) {
    return a.subject === b.subject && a.received_at === b.received_at;
}

function buildRowKey(clientId, item, partIndex) {
    return `${clientId}|${item.received_at || ''}|${item.subject || ''}|${partIndex}`;
}

function normalizePartNumber(value) {
    if (value == null) {
        return '';
    }
    return String(value).trim();
}

function getDedupedSelectedPartNumbers() {
    const seen = new Set();
    const result = [];

    selectedRows.forEach((entry) => {
        const candidates = [entry.partNumber, ...(entry.alternatives || [])];
        candidates.forEach((pn) => {
            const normalized = normalizePartNumber(pn);
            if (!normalized || seen.has(normalized) || excludedPartNumbers.has(normalized)) {
                return;
            }
            seen.add(normalized);
            result.push(normalized);
        });
    });

    return result;
}

function getRowPartNumbers(entry) {
    return [entry.partNumber, ...(entry.alternatives || [])]
        .map(normalizePartNumber)
        .filter(Boolean);
}

function syncRowCheckboxesFromSelection() {
    rfqTableBody.querySelectorAll('.row-checkbox').forEach((checkbox) => {
        checkbox.checked = selectedRows.has(checkbox.dataset.rowKey);
    });
}

function pruneRowsWithNoRemainingParts() {
    const keysToDelete = [];

    selectedRows.forEach((entry, key) => {
        const remaining = getRowPartNumbers(entry)
            .filter((pn) => !excludedPartNumbers.has(pn));
        if (!remaining.length) {
            keysToDelete.push(key);
        }
    });

    keysToDelete.forEach((key) => selectedRows.delete(key));
    syncRowCheckboxesFromSelection();
}

function onRowCheckboxChange(event) {
    const checkbox = event.target.closest('.row-checkbox');
    if (!checkbox) {
        return;
    }

    const key = checkbox.dataset.rowKey;
    if (!key) {
        return;
    }

    if (checkbox.checked) {
        const entry = {
            partNumber: checkbox.dataset.partNumber || '',
            alternatives: parseAlternativesDataset(checkbox.dataset.alternatives),
        };
        selectedRows.set(key, entry);
        getRowPartNumbers(entry).forEach((pn) => excludedPartNumbers.delete(pn));
    } else {
        selectedRows.delete(key);
    }

    updateSelectedPartsBar();
}

function parseAlternativesDataset(value) {
    if (!value) {
        return [];
    }

    try {
        const parsed = JSON.parse(value);
        if (!Array.isArray(parsed)) {
            return [];
        }
        return parsed.map(normalizePartNumber).filter(Boolean);
    } catch (error) {
        return [];
    }
}

function toggleSelectedPartsDetails() {
    const isOpen = !selectedPartsDetails.hidden;
    selectedPartsDetails.hidden = isOpen;
    selectedPartsToggle.setAttribute('aria-expanded', String(!isOpen));
    selectedPartsToggle.classList.toggle('open', !isOpen);
}

function clearSelection() {
    selectedRows.clear();
    excludedPartNumbers.clear();
    rfqTableBody.querySelectorAll('.row-checkbox:checked').forEach((checkbox) => {
        checkbox.checked = false;
    });
    updateSelectedPartsBar();
}

function removePartNumberFromSelection(partNumber) {
    const target = normalizePartNumber(partNumber);
    if (!target) {
        return;
    }

    excludedPartNumbers.add(target);
    pruneRowsWithNoRemainingParts();
    updateSelectedPartsBar();
}

function onSelectedPartsListClick(event) {
    const removeButton = event.target.closest('.selected-part-remove');
    if (!removeButton) {
        return;
    }

    event.preventDefault();
    removePartNumberFromSelection(removeButton.dataset.partNumber);
}

function startSearchWithSelectedParts() {
    const partNumbers = getDedupedSelectedPartNumbers();
    if (!partNumbers.length) {
        return;
    }

    localStorage.setItem(PENDING_SEARCH_PARTS_KEY, JSON.stringify(partNumbers));
    window.location.href = 'index.html';
}

function updateSelectedPartsBar() {
    const rowCount = selectedRows.size;
    const partNumbers = getDedupedSelectedPartNumbers();
    const hasSelection = rowCount > 0;

    selectedPartsCount.textContent = `${rowCount} row${rowCount === 1 ? '' : 's'} selected`;
    selectedPartsNumbersHint.textContent = hasSelection
        ? `· ${partNumbers.length} part number${partNumbers.length === 1 ? '' : 's'}`
        : '';

    clearSelectedParts.disabled = !hasSelection;
    searchSelectedParts.disabled = !hasSelection;

    if (!partNumbers.length) {
        selectedPartsList.innerHTML = '<p class="selected-parts-empty">No parts selected</p>';
        return;
    }

    selectedPartsList.innerHTML = `
        <ul>
            ${partNumbers.map((pn) => `
                <li class="selected-part-chip">
                    <span class="selected-part-label">${escapeHtml(pn)}</span>
                    <button
                        type="button"
                        class="selected-part-remove"
                        data-part-number="${escapeHtml(pn)}"
                        aria-label="Remove ${escapeHtml(pn)}"
                        title="Remove"
                    >&times;</button>
                </li>
            `).join('')}
        </ul>
    `;
}

function renderTable(items) {
    if (!items.length) {
        rfqTableBody.innerHTML = '';
        return;
    }

    const rows = [];
    const clientId = activeClientId;

    items.forEach((item) => {
        const parts = Array.isArray(item.parts) ? item.parts : [];
        if (!parts.length) {
            return;
        }

        const subject = escapeHtml(item.subject || '(No subject)');
        const receivedAt = formatReceivedAt(item.received_at);
        const rowspan = parts.length;

        parts.forEach((part, partIndex) => {
            const partNumberRaw = normalizePartNumber(part.part_number);
            const alternativesRaw = Array.isArray(part.alternatives)
                ? part.alternatives.map(normalizePartNumber).filter(Boolean)
                : [];
            const rowKey = buildRowKey(clientId, item, partIndex);
            const isChecked = selectedRows.has(rowKey);

            const partNumber = escapeHtml(partNumberRaw || '—');
            const description = escapeHtml(part.description ?? '—');
            const quantity = part.quantity != null ? escapeHtml(String(part.quantity)) : '—';
            const alternatives = alternativesRaw.length
                ? escapeHtml(alternativesRaw.join(', '))
                : '—';

            const isGroupStart = partIndex === 0;
            const rowClass = isGroupStart ? 'rfq-group-start' : '';

            let subjectCell = '';
            if (isGroupStart) {
                subjectCell = `
                    <td class="col-subject" rowspan="${rowspan}">
                        <div class="rfq-subject">${subject}</div>
                        <div class="rfq-subject-time">${receivedAt}</div>
                    </td>
                `;
            }

            rows.push(`
                <tr class="${rowClass}">
                    <td class="select-column">
                        <input
                            type="checkbox"
                            class="row-checkbox"
                            data-row-key="${escapeHtml(rowKey)}"
                            data-part-number="${escapeHtml(partNumberRaw)}"
                            data-alternatives="${escapeHtml(JSON.stringify(alternativesRaw))}"
                            ${isChecked ? 'checked' : ''}
                            aria-label="Select part ${partNumber}"
                        >
                    </td>
                    ${subjectCell}
                    <td class="col-part-number">${partNumber}</td>
                    <td class="col-description">${description}</td>
                    <td class="col-quantity">${quantity}</td>
                    <td class="col-alternatives">${alternatives}</td>
                </tr>
            `);
        });
    });

    rfqTableBody.innerHTML = rows.join('');
}

function setupScrollObserver() {
    scrollObserver = new IntersectionObserver(
        (entries) => {
            const entry = entries[0];
            if (!entry?.isIntersecting || activeClientId == null) {
                return;
            }

            const state = getClientState(activeClientId);
            if (state.hasNext && !state.loading) {
                loadMore(activeClientId, false);
            }
        },
        {
            root: rfqTableWrap,
            rootMargin: '80px',
            threshold: 0,
        }
    );

    scrollObserver.observe(rfqScrollSentinel);
}

function updateScrollSentinel(state) {
    rfqScrollSentinel.hidden = !state.hasNext;
}

function showLoadMoreStatus(message, isError = false) {
    rfqLoadMoreStatus.hidden = false;
    rfqLoadMoreStatus.textContent = message;
    rfqLoadMoreStatus.className = `rfq-load-more-status${isError ? ' rfq-load-more-error' : ''}`;
}

function hideLoadMoreStatus() {
    rfqLoadMoreStatus.hidden = true;
    rfqLoadMoreStatus.textContent = '';
    rfqLoadMoreStatus.className = 'rfq-load-more-status';
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
