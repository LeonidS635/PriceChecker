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
const selectedPartsCopyStatus = document.getElementById('selectedPartsCopyStatus');

let activeClientId = null;
const clientStates = {};
let scrollObserver = null;
let copyStatusTimer = null;

/** @type {Map<string, { partNumber: string, alternatives: string[] }>} */
const selectedRows = new Map();

/** @type {Set<string>} */
const excludedPartNumbers = new Set();

document.addEventListener('DOMContentLoaded', init);

function init() {
    clientHeadersRow.addEventListener('click', onClientHeaderClick);
    rfqTableBody.addEventListener('change', onTableCheckboxChange);
    selectedPartsToggle.addEventListener('click', toggleSelectedPartsDetails);
    clearSelectedParts.addEventListener('click', clearSelection);
    searchSelectedParts.addEventListener('click', copySelectedPartsToSearch);
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

function buildGroupKey(clientId, item) {
    return `${clientId}|${item.received_at || ''}|${item.subject || ''}`;
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

function queryCheckboxesByGroup(groupKey, selector) {
    return Array.from(rfqTableBody.querySelectorAll(selector))
        .filter((checkbox) => checkbox.dataset.groupKey === groupKey);
}

function syncRowCheckboxesFromSelection() {
    rfqTableBody.querySelectorAll('.row-checkbox').forEach((checkbox) => {
        checkbox.checked = selectedRows.has(checkbox.dataset.rowKey);
    });
}

function syncGroupCheckbox(groupKey) {
    const groupCheckbox = queryCheckboxesByGroup(groupKey, '.group-checkbox')[0];
    if (!groupCheckbox) {
        return;
    }

    const rowCheckboxes = queryCheckboxesByGroup(groupKey, '.row-checkbox');
    const selectedCount = rowCheckboxes.filter((checkbox) => selectedRows.has(checkbox.dataset.rowKey)).length;
    const total = rowCheckboxes.length;

    groupCheckbox.checked = total > 0 && selectedCount === total;
    groupCheckbox.indeterminate = selectedCount > 0 && selectedCount < total;
}

function syncAllGroupCheckboxes() {
    const groupKeys = new Set(
        Array.from(rfqTableBody.querySelectorAll('.group-checkbox'))
            .map((checkbox) => checkbox.dataset.groupKey)
            .filter(Boolean)
    );
    groupKeys.forEach((groupKey) => syncGroupCheckbox(groupKey));
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
    syncAllGroupCheckboxes();
}

function selectRowFromCheckbox(checkbox) {
    const key = checkbox.dataset.rowKey;
    if (!key) {
        return;
    }

    const entry = {
        partNumber: checkbox.dataset.partNumber || '',
        alternatives: parseAlternativesDataset(checkbox.dataset.alternatives),
    };
    selectedRows.set(key, entry);
    getRowPartNumbers(entry).forEach((pn) => excludedPartNumbers.delete(pn));
    checkbox.checked = true;
}

function deselectRowFromCheckbox(checkbox) {
    const key = checkbox.dataset.rowKey;
    if (!key) {
        return;
    }

    selectedRows.delete(key);
    checkbox.checked = false;
}

function onTableCheckboxChange(event) {
    const groupCheckbox = event.target.closest('.group-checkbox');
    if (groupCheckbox) {
        const groupKey = groupCheckbox.dataset.groupKey;
        const rowCheckboxes = queryCheckboxesByGroup(groupKey, '.row-checkbox');

        if (groupCheckbox.checked) {
            rowCheckboxes.forEach((checkbox) => selectRowFromCheckbox(checkbox));
        } else {
            rowCheckboxes.forEach((checkbox) => deselectRowFromCheckbox(checkbox));
        }

        groupCheckbox.indeterminate = false;
        updateSelectedPartsBar();
        return;
    }

    const checkbox = event.target.closest('.row-checkbox');
    if (!checkbox) {
        return;
    }

    if (checkbox.checked) {
        selectRowFromCheckbox(checkbox);
    } else {
        deselectRowFromCheckbox(checkbox);
    }

    syncGroupCheckbox(checkbox.dataset.groupKey);
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
    rfqTableBody.querySelectorAll('.row-checkbox').forEach((checkbox) => {
        checkbox.checked = false;
    });
    rfqTableBody.querySelectorAll('.group-checkbox').forEach((checkbox) => {
        checkbox.checked = false;
        checkbox.indeterminate = false;
    });
    hideCopyStatus();
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

function hideCopyStatus() {
    if (copyStatusTimer) {
        clearTimeout(copyStatusTimer);
        copyStatusTimer = null;
    }
    selectedPartsCopyStatus.hidden = true;
    selectedPartsCopyStatus.textContent = '';
}

function showCopyStatus(message) {
    hideCopyStatus();
    selectedPartsCopyStatus.hidden = false;
    selectedPartsCopyStatus.textContent = message;
    copyStatusTimer = setTimeout(() => {
        hideCopyStatus();
    }, 3500);
}

function copySelectedPartsToSearch() {
    const partNumbers = getDedupedSelectedPartNumbers();
    if (!partNumbers.length) {
        return;
    }

    localStorage.setItem(PENDING_SEARCH_PARTS_KEY, JSON.stringify(partNumbers));
    showCopyStatus(`Copied ${partNumbers.length} part number${partNumbers.length === 1 ? '' : 's'} to search. Open the main page when ready.`);
}

function updateSelectedPartsBar() {
    const rowCount = selectedRows.size;
    const partNumbers = getDedupedSelectedPartNumbers();
    const hasSelection = rowCount > 0;
    const hasParts = partNumbers.length > 0;

    selectedPartsCount.textContent = `${rowCount} row${rowCount === 1 ? '' : 's'} selected`;
    selectedPartsNumbersHint.textContent = hasParts
        ? `· ${partNumbers.length} part number${partNumbers.length === 1 ? '' : 's'}`
        : '';

    clearSelectedParts.disabled = !hasSelection;
    searchSelectedParts.disabled = !hasParts;

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

function getGroupCheckState(clientId, item) {
    const parts = Array.isArray(item.parts) ? item.parts : [];
    let selectedCount = 0;

    parts.forEach((_, partIndex) => {
        if (selectedRows.has(buildRowKey(clientId, item, partIndex))) {
            selectedCount += 1;
        }
    });

    return {
        checked: parts.length > 0 && selectedCount === parts.length,
        indeterminate: selectedCount > 0 && selectedCount < parts.length,
    };
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
        const groupKey = buildGroupKey(clientId, item);
        const groupState = getGroupCheckState(clientId, item);

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
                        <div class="rfq-subject-header">
                            <input
                                type="checkbox"
                                class="group-checkbox"
                                data-group-key="${escapeHtml(groupKey)}"
                                ${groupState.checked ? 'checked' : ''}
                                aria-label="Select all parts in this letter"
                                title="Select all parts in this letter"
                            >
                            <div class="rfq-subject-text">
                                <div class="rfq-subject">${subject}</div>
                                <div class="rfq-subject-time">${receivedAt}</div>
                            </div>
                        </div>
                    </td>
                `;
            }

            rows.push(`
                <tr class="${rowClass}">
                    ${subjectCell}
                    <td class="col-part-number">
                        <label class="rfq-part-select">
                            <input
                                type="checkbox"
                                class="row-checkbox"
                                data-row-key="${escapeHtml(rowKey)}"
                                data-group-key="${escapeHtml(groupKey)}"
                                data-part-number="${escapeHtml(partNumberRaw)}"
                                data-alternatives="${escapeHtml(JSON.stringify(alternativesRaw))}"
                                ${isChecked ? 'checked' : ''}
                                aria-label="Select part ${partNumber}"
                            >
                            <span class="rfq-part-number-text">${partNumber}</span>
                        </label>
                    </td>
                    <td class="col-description">${description}</td>
                    <td class="col-quantity">${quantity}</td>
                    <td class="col-alternatives">${alternatives}</td>
                </tr>
            `);
        });
    });

    rfqTableBody.innerHTML = rows.join('');

    rfqTableBody.querySelectorAll('.group-checkbox').forEach((checkbox) => {
        const groupKey = checkbox.dataset.groupKey;
        const groupState = getGroupCheckStateFromDom(groupKey);
        checkbox.checked = groupState.checked;
        checkbox.indeterminate = groupState.indeterminate;
    });
}

function getGroupCheckStateFromDom(groupKey) {
    const rowCheckboxes = queryCheckboxesByGroup(groupKey, '.row-checkbox');
    const selectedCount = rowCheckboxes.filter((checkbox) => selectedRows.has(checkbox.dataset.rowKey)).length;
    const total = rowCheckboxes.length;

    return {
        checked: total > 0 && selectedCount === total,
        indeterminate: selectedCount > 0 && selectedCount < total,
    };
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
