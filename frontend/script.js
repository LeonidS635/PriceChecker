// Configuration
const API_BASE_URL = 'http://localhost:8081';
let portals = [];
let conditions = [];
let loggedInPortals = new Set();
let excelPortals = [];
let notifications = [];
let currentSearchController = null;
let currentLoginController = null;
let currentLogoutController = null;
let selectionMode = true; // Enabled by default
let selectedRows = new Set();
let totalPartsToSearch = 0;
let processedParts = 0;
let displayedPartNumbers = new Set();
let currentQuotationData = {
    quotationNumber: '',
    logisticsCost: 0,
    markup: 0,
    incoterms: 'FOB',
    paymentTerms: 'Net 30',
    items: {}
};
let portalsInProgress = new Set();
let allSearchResults = [];

// DOM Elements
const searchButton = document.getElementById('searchButton');
const filterButton = document.getElementById('filterButton');
const settingsButton = document.getElementById('settingsButton');
const portalsButton = document.getElementById('portalsButton');
const excelButton = document.getElementById('excelButton');
const quotationButton = document.getElementById('quotationButton');
const notificationButton = document.getElementById('notificationButton');
const closeNotificationPanel = document.getElementById('closeNotificationPanel');
const clearAllNotifications = document.getElementById('clearAllNotifications');
const notificationPanel = document.getElementById('notificationPanel');
const notificationBadge = document.getElementById('notificationBadge');
const reloadButton = document.getElementById('reloadButton');
const criticalError = document.getElementById('criticalError');
const resultsTableBody = document.getElementById('resultsTableBody');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const filterModal = document.getElementById('filterModal');
const portalsModal = document.getElementById('portalsModal');
const excelModal = document.getElementById('excelModal');
const quotationModal = document.getElementById('quotationModal');
const applyFilters = document.getElementById('applyFilters');
const resetFilters = document.getElementById('resetFilters');
const loginAllPortals = document.getElementById('loginAllPortals');
const logoutAllPortals = document.getElementById('logoutAllPortals');
const uploadExcelBtn = document.getElementById('uploadExcelBtn');
const excelUpload = document.getElementById('excelUpload');
const uploadArea = document.getElementById('uploadArea');
const partNumberInput = document.getElementById('partNumberInput');
const selectAllCheckbox = document.getElementById('selectAllCheckbox');
const selectedCountText = document.getElementById('selectedCountText');
const quotationItemCount = document.getElementById('quotationItemCount');
const generateQuotation = document.getElementById('generateQuotation');
const cancelQuotation = document.getElementById('cancelQuotation');
const noQuotationItems = document.getElementById('noQuotationItems');
const quotationItems = document.getElementById('quotationItems');
const selectAllPortals = document.getElementById('selectAllPortals');
const selectAllConditions = document.getElementById('selectAllConditions');

// Event Listeners
document.addEventListener('DOMContentLoaded', init);
searchButton.addEventListener('click', performSearch);
filterButton.addEventListener('click', () => toggleModal(filterModal));
portalsButton.addEventListener('click', () => toggleModal(portalsModal));
excelButton.addEventListener('click', () => toggleModal(excelModal));
quotationButton.addEventListener('click', () => toggleModal(quotationModal));
notificationButton.addEventListener('click', toggleNotificationPanel);
closeNotificationPanel.addEventListener('click', toggleNotificationPanel);
clearAllNotifications.addEventListener('click', clearAllNotificationsHandler);
reloadButton.addEventListener('click', () => location.reload());
applyFilters.addEventListener('click', applyTableFilters);
resetFilters.addEventListener('click', resetTableFilters);
loginAllPortals.addEventListener('click', loginToAllPortals);
logoutAllPortals.addEventListener('click', logoutAllPortalsHandler);
uploadExcelBtn.addEventListener('click', uploadExcelFile);
selectAllCheckbox.addEventListener('change', toggleSelectAllRows);
generateQuotation.addEventListener('click', generateQuotationHandler);
cancelQuotation.addEventListener('click', () => toggleModal(quotationModal));
selectAllPortals.addEventListener('change', toggleSelectAllPortals);
selectAllConditions.addEventListener('change', toggleSelectAllConditions);

// Drag and drop for file upload
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary)';
    uploadArea.style.backgroundColor = '#f8fafc';
});

uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--border)';
    uploadArea.style.backgroundColor = 'transparent';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--border)';
    uploadArea.style.backgroundColor = 'transparent';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        excelUpload.files = files;
    }
});

uploadArea.addEventListener('click', () => {
    excelUpload.click();
});

excelUpload.addEventListener('click', (e) => {
    e.stopPropagation();
});

excelUpload.addEventListener('change', () => {
    if (excelUpload.files.length > 0) {
        uploadArea.querySelector('p').textContent = `Selected file: ${excelUpload.files[0].name}`;
    }
});

// Initialize application
function init() {
    fetchConfig();
    fetchExcelFiles();
    loadQuotationData();

    // Add event listeners for modal closing
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    document.querySelectorAll('.modal-close').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.modal-overlay').classList.remove('active');
        });
    });

    // Enter key for search
    partNumberInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Initialize select mode as enabled by default
    updateSelectionCount();
}

// Load quotation data from localStorage
function loadQuotationData() {
    const savedData = localStorage.getItem('currentQuotationData');
    if (savedData) {
        currentQuotationData = JSON.parse(savedData);

        // Restore global fields
        document.getElementById('quotationNumber').value = currentQuotationData.quotationNumber || '';
        document.getElementById('logisticsCost').value = currentQuotationData.logisticsCost || 0;
        document.getElementById('markup').value = currentQuotationData.markup || 0;
        document.getElementById('incoterms').value = currentQuotationData.incoterms || '';
        document.getElementById('paymentTerms').value = currentQuotationData.paymentTerms || '';
    }
}

// Save quotation data to localStorage
function saveQuotationData() {
    localStorage.setItem('currentQuotationData', JSON.stringify(currentQuotationData));
}

// Clear quotation data (called when new search is performed)
function clearQuotationData() {
    currentQuotationData = {
        quotationNumber: '',
        logisticsCost: 0,
        markup: 0,
        incoterms: '',
        paymentTerms: '',
        items: {}
    };
    localStorage.removeItem('currentQuotationData');

    // Clear global fields
    document.getElementById('quotationNumber').value = '';
    document.getElementById('logisticsCost').value = 0;
    document.getElementById('markup').value = 0;
    document.getElementById('incoterms').value = '';
    document.getElementById('paymentTerms').value = '';
}

// Fetch configuration from backend
async function fetchConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/config`);
        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const data = await response.json();
        portals = data.portals || [];
        conditions = data.conditions || [];

        // Filter out unknown condition
        conditions = conditions.filter(condition => condition.code !== 'Unknown');

        renderPortals();
        renderFilterOptions();

    } catch (error) {
        showCriticalError(`Failed to load configuration: ${error.message}`);
    }
}

// Fetch list of Excel files
async function fetchExcelFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/excel`, {
            method: 'GET'
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const data = await response.json();
        excelPortals = data.file_ids || [];
        renderExcelFiles();

    } catch (error) {
        addNotification('error', 'Excel', '', error.message);
    }
}

// Perform search
async function performSearch() {
    const partNumbers = partNumberInput.value
        .split(',')
        .map(pn => pn.trim())
        .filter(pn => pn);

    if (partNumbers.length === 0) {
        addNotification('error', 'Search', '', 'Please enter at least one part number');
        return;
    }

    // Clear previous selection and quotation data
    selectedRows.clear();
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
    clearQuotationData();
    updateSelectionCount();

    // Get selected portals and conditions from filters
    const selectedPortals = Array.from(document.querySelectorAll('#portalsFilterList input:checked'))
        .map(input => parseInt(input.value));
    
    // Filter only logged in portals
    const loggedInSelectedPortals = selectedPortals.filter(portalId => loggedInPortals.has(portalId));

    const selectedConditions = Array.from(document.querySelectorAll('#conditionsFilterList input:checked'))
        .map(input => parseInt(input.value));

    // Prepare filters
    const filters = {
        portal_ids: loggedInSelectedPortals,
        conditions: selectedConditions
    };

    // Clear previous results
    resultsTableBody.innerHTML = '';
    displayedPartNumbers.clear();
    allSearchResults = [];

    // Reset and show progress
    totalPartsToSearch = partNumbers.length;
    processedParts = 0;
    updateProgressBar();

    // Add initial no results message
    const noResultsRow = document.createElement('tr');
    noResultsRow.innerHTML = '<td colspan="11" class="no-results">Searching... Results will appear as they become available.</td>';
    resultsTableBody.appendChild(noResultsRow);

    try {
        currentSearchController = new AbortController();

        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                part_numbers: partNumbers,
                filters: filters
            }),
            signal: currentSearchController.signal
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        // Process streamed response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let partialLine = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = (partialLine + chunk).split('\n');
            partialLine = lines.pop() || '';

            for (const line of lines) {
                if (line.trim() === '') continue;

                try {
                    const result = JSON.parse(line);
                    processSearchResult(result);
                } catch (e) {
                    addNotification('error', 'Search', '', `Error parsing result: ${e.message}`);
                }
            }
        }

        // Process any remaining line
        if (partialLine.trim() !== '') {
            try {
                const result = JSON.parse(partialLine);
                processSearchResult(result);
            } catch (e) {
                addNotification('error', 'Search', '', `Error parsing result: ${e.message}`);
            }
        }

        addNotification('info', 'Search', '', `Search completed for ${partNumbers.length} part numbers`);

    } catch (error) {
        if (error.name !== 'AbortError') {
            addNotification('error', 'Search', '', error.message);

            // Restore no results message
            resultsTableBody.innerHTML = '';
            const noResultsRow = document.createElement('tr');
            noResultsRow.innerHTML = '<td colspan="11" class="no-results">No search results yet. Enter part numbers to start searching.</td>';
            resultsTableBody.appendChild(noResultsRow);
        }
    } finally {
        currentSearchController = null;
        if (displayedPartNumbers.size == 0) {
            noResultsRow.innerHTML = '<td colspan="11" class="no-results">No search results were found. Enter part numbers to start searching.</td>';
        }
    }
}

// Process a single search result
function processSearchResult(result) {
    processedParts++;
    updateProgressBar();

    // Store all results for client-side filtering
    allSearchResults.push(result);
    
    let atLeastOneSuccess = false;
    for (const portalResult of result.offers_statuses) {
        if (portalResult.success) {
            atLeastOneSuccess = true;
            break;
        }
    }

    if (atLeastOneSuccess) {
        const partNumber = result.requested_part_number;

        // Add part number divider
        addPartNumberDivider(partNumber);
        displayedPartNumbers.add(partNumber);

        for (const portalResult of result.offers_statuses) {
            if (portalResult.success) {
                if (portalResult.offers && portalResult.offers.length > 0) {
                    // Add offers for this part number
                    portalResult.offers.forEach(offer => {
                        addTableRow(offer, portalResult.portal_id);
                    });
                } else {
                    addNotification('info', getPortalName(portalResult.portal_id), partNumber, 'No offers found');
                }
            } else {
                addNotification('error', getPortalName(portalResult.portal_id), partNumber, portalResult.error || 'Unknown error');
            }
        }
    }

    // Remove "searching" message if we have results
    const searchingMsg = resultsTableBody.querySelector('.no-results');
    if (searchingMsg && atLeastOneSuccess) {
        searchingMsg.remove();
    }
}

// Add part number divider
function addPartNumberDivider(partNumber) {
    const dividerRow = document.createElement('tr');
    dividerRow.className = 'part-divider';
    dividerRow.innerHTML = `<td colspan="11">Part Number: ${partNumber}</td>`;
    resultsTableBody.appendChild(dividerRow);
}

// Update progress bar
function updateProgressBar() {
    if (totalPartsToSearch > 0) {
        const progress = Math.min(100, (processedParts / totalPartsToSearch) * 100);
        progressBar.style.width = `${progress}%`;

        if (progressText) {
            progressText.textContent = `${processedParts} of ${totalPartsToSearch} parts processed`;
        }
    }
}

// Format price with thousands separators
function formatPrice(price) {
    if (!price && price !== 0) return '';
    return `$${price.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0')}`;
}

// Add row to results table
function addTableRow(offer, portalId) {
    const row = document.createElement('tr');
    const rowId = `row_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    row.dataset.rowId = rowId;

    const portalName = getPortalName(portalId);
    const condition = conditions.find(c => c.id === offer.condition_id);
    const conditionCode = condition ? condition.code : '';

    const interchangeable = offer.interchangeable && offer.interchangeable.length
        ? offer.interchangeable.join(', ')
        : '';

    const price = offer.price ? formatPrice(offer.price) : '';

    row.innerHTML = `
        <td class="select-column">
            <input type="checkbox" class="row-checkbox">
        </td>
        <td>${portalName}</td>
        <td>${offer.part_number}</td>
        <td>${offer.description || ''}</td>
        <td>${conditionCode}</td>
        <td class="price-cell">${price}</td>
        <td>${offer.qty || ''}</td>
        <td>${offer.lead_time || ''}</td>
        <td>${offer.warehouse || ''}</td>
        <td>${interchangeable}</td>
        <td>${offer.other_information || ''}</td>
    `;

    const checkbox = row.querySelector('.row-checkbox');
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            selectedRows.add(rowId);
        } else {
            selectedRows.delete(rowId);
            // Remove from quotation data if deselected
            if (currentQuotationData.items[rowId]) {
                delete currentQuotationData.items[rowId];
                saveQuotationData();
            }
        }
        updateSelectionCount();
        updateSelectAllCheckbox();
        updateQuotationItems();
    });

    resultsTableBody.appendChild(row);
    return row;
}

// Update selection count
function updateSelectionCount() {
    const selectedCountValue = document.querySelectorAll('.row-checkbox:checked').length;

    if (selectedCountValue > 0) {
        selectedCountText.textContent = selectedCountValue;
    } else {
        selectedCountText.textContent = '';
    }

    quotationItemCount.textContent = selectedCountValue;
}

// Toggle select all rows
function toggleSelectAllRows() {
    const checkboxes = resultsTableBody.querySelectorAll('.row-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        const row = checkbox.closest('tr');

        if (selectAllCheckbox.checked) {
            selectedRows.add(row.dataset.rowId);
        } else {
            selectedRows.delete(row.dataset.rowId);
            // Remove from quotation data if deselected
            if (currentQuotationData.items[row.dataset.rowId]) {
                delete currentQuotationData.items[row.dataset.rowId];
            }
        }
    });

    updateSelectionCount();
    updateQuotationItems();
    saveQuotationData();
}

// Update select all checkbox
function updateSelectAllCheckbox() {
    const checkboxes = resultsTableBody.querySelectorAll('.row-checkbox');
    const allChecked = checkboxes.length > 0 && Array.from(checkboxes).every(checkbox => checkbox.checked);
    const someChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);

    selectAllCheckbox.checked = allChecked;
    selectAllCheckbox.indeterminate = someChecked && !allChecked;
}

// Update quotation items display
function updateQuotationItems() {
    const selectedItems = getSelectedItemsForQuotation();

    quotationItems.innerHTML = '';

    if (selectedItems.length === 0) {
        noQuotationItems.style.display = 'block';
        quotationItems.style.display = 'none';
    } else {
        noQuotationItems.style.display = 'none';
        quotationItems.style.display = 'table-row-group';

        selectedItems.forEach((item, index) => {
            const row = document.createElement('tr');
            row.dataset.rowId = item.rowId;

            // Use saved data if available, otherwise use table data
            const savedItem = currentQuotationData.items[item.rowId] || item;

            row.innerHTML = `
                <td><input type="text" class="quotation-item-input" value="${savedItem.part_number}" data-field="part_number"></td>
                <td><input type="text" class="quotation-item-input" value="${savedItem.description}" data-field="description"></td>
                <td><input type="number" class="quotation-item-input" value="${savedItem.qty}" data-field="qty" min="1"></td>
                <td><input type="text" class="quotation-item-input" value="${savedItem.condition}" data-field="condition"></td>
                <td><input type="number" class="quotation-item-input" value="${savedItem.price.toFixed(2)}" data-field="price" step="0.01" min="0"></td>
                <td><input type="text" class="quotation-item-input" value="${savedItem.lead_time}" data-field="lead_time"></td>
                <td>
                    <button class="remove-item-btn" title="Remove item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </td>
            `;
            quotationItems.appendChild(row);

            // Add event listener for remove button
            const removeBtn = row.querySelector('.remove-item-btn');
            removeBtn.addEventListener('click', () => {
                removeItemFromQuotation(item.rowId);
            });

            // Add event listeners for input changes
            const inputs = row.querySelectorAll('.quotation-item-input');
            inputs.forEach(input => {
                // Save current value on change
                input.addEventListener('change', () => {
                    updateQuotationItemData(item.rowId, input.dataset.field, input.value);
                });

                // Also save on input for better responsiveness
                input.addEventListener('input', () => {
                    updateQuotationItemData(item.rowId, input.dataset.field, input.value);
                });
            });
        });
    }
}

// Remove item from quotation
function removeItemFromQuotation(rowId) {
    // Uncheck the corresponding row in the main table
    const mainRow = document.querySelector(`tr[data-row-id="${rowId}"]`);
    if (mainRow) {
        const checkbox = mainRow.querySelector('.row-checkbox');
        if (checkbox) {
            checkbox.checked = false;
            checkbox.dispatchEvent(new Event('change'));
        }
    }

    // Remove from saved data
    if (currentQuotationData.items[rowId]) {
        delete currentQuotationData.items[rowId];
        saveQuotationData();
    }
}

// Update quotation item data
function updateQuotationItemData(rowId, field, value) {
    if (!currentQuotationData.items[rowId]) {
        currentQuotationData.items[rowId] = getSelectedItemsForQuotation().find(item => item.rowId === rowId);
    }

    if (currentQuotationData.items[rowId]) {
        if (field === 'price' || field === 'qty') {
            currentQuotationData.items[rowId][field] = parseFloat(value) || 0;
        } else {
            currentQuotationData.items[rowId][field] = value;
        }
        saveQuotationData();
    }
}

// Generate quotation
async function generateQuotationHandler() {
    const quotationNumber = document.getElementById('quotationNumber').value.trim();

    if (!quotationNumber) {
        addNotification('error', 'Quotation', '', 'Quotation number is required');
        document.getElementById('quotationNumber').focus();
        return;
    }

    // Save global fields
    currentQuotationData.quotationNumber = quotationNumber;
    currentQuotationData.logisticsCost = parseFloat(document.getElementById('logisticsCost').value) || 0;
    currentQuotationData.markup = parseFloat(document.getElementById('markup').value) || 0;
    currentQuotationData.incoterms = document.getElementById('incoterms').value;
    currentQuotationData.paymentTerms = document.getElementById('paymentTerms').value;
    saveQuotationData();

    const selectedItems = getSelectedItemsForQuotation();

    if (selectedItems.length === 0) {
        addNotification('error', 'Quotation', '', 'Please select at least one item');
        return;
    }

    const quotationData = {
        quotation_number: parseInt(quotationNumber) || 0,
        logistics_cost: currentQuotationData.logisticsCost,
        markup: currentQuotationData.markup,
        incoterms: currentQuotationData.incoterms,
        payment_terms: currentQuotationData.paymentTerms,
        offers: selectedItems.map(item => {
            const savedItem = currentQuotationData.items[item.rowId] || item;
            return {
                part_number: savedItem.part_number,
                description: savedItem.description,
                qty: parseInt(savedItem.qty) || 0,
                condition: savedItem.condition,
                price: parseFloat(savedItem.price) || 0,
                lead_time: parseInt(savedItem.lead_time)
            };
        })
    };

    try {
        const response = await fetch(`${API_BASE_URL}/quotation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(quotationData)
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `quotation-${quotationNumber}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        addNotification('success', 'Quotation', '', 'Quotation generated successfully');
        toggleModal(quotationModal);

    } catch (error) {
        addNotification('error', 'Quotation', '', error.message);
    }
}

// Get selected items for quotation
function getSelectedItemsForQuotation() {
    const selectedItems = [];
    const rows = resultsTableBody.querySelectorAll('tr');

    rows.forEach(row => {
        if (row.classList.contains('part-divider')) return;

        const checkbox = row.querySelector('.row-checkbox');
        if (checkbox && checkbox.checked) {
            const cells = row.querySelectorAll('td');
            selectedItems.push({
                rowId: row.dataset.rowId,
                part_number: cells[2].textContent,
                description: cells[3].textContent,
                qty: parseInt(cells[6].textContent) || 1,
                condition: cells[4].textContent,
                price: parseFloat(cells[5].textContent.replace(/[$\u00A0]/g, '')) || 0,
                lead_time: cells[7].textContent
            });
        }
    });

    return selectedItems;
}

// Render portals in manage portals modal (Excel files excluded)
function renderPortals() {
    const portalList = document.getElementById('portalList');
    portalList.innerHTML = '';

    // Only show regular portals (exclude Excel files)
    portals.forEach(portal => {
        const portalElement = document.createElement('div');
        portalElement.className = 'portal-item';

        const buttonText = portalsInProgress.has(portal.id) ?
            (loggedInPortals.has(portal.id) ? 'Logging out...' : 'Logging in...') :
            (loggedInPortals.has(portal.id) ? 'Logout' : 'Login');

        const buttonClass = portalsInProgress.has(portal.id) ?
            (loggedInPortals.has(portal.id) ? 'btn-logging-out' : 'btn-loading') :
            (loggedInPortals.has(portal.id) ? 'btn-danger' : 'btn-primary');

        portalElement.innerHTML = `
            <span class="portal-name">${portal.name}</span>
            <div class="portal-form" data-portal-id="${portal.id}">
                <input type="text" class="form-input username-input" placeholder="Username" id="username-${portal.id}" value="${localStorage.getItem(`username-${portal.id}`) || ''}">
                <input type="password" class="form-input password-input" placeholder="Password" id="password-${portal.id}" value="${localStorage.getItem(`password-${portal.id}`) || ''}">
                <button class="btn portal-login-btn ${buttonClass}" 
                        data-portal-id="${portal.id}" ${portalsInProgress.has(portal.id) ? 'disabled' : ''}>
                    ${buttonText}
                </button>
            </div>
        `;

        portalList.appendChild(portalElement);

        const loginButton = portalElement.querySelector('button');
        loginButton.addEventListener('click', () => {
            if (loggedInPortals.has(portal.id)) {
                logoutPortal(portal.id);
            } else {
                loginPortal(portal.id);
            }
        });

        const usernameInput = portalElement.querySelector('.username-input');
        const passwordInput = portalElement.querySelector('.password-input');

        usernameInput.addEventListener('change', () => {
            localStorage.setItem(`username-${portal.id}`, usernameInput.value);
        });

        passwordInput.addEventListener('change', () => {
            localStorage.setItem(`password-${portal.id}`, passwordInput.value);
        });
    });
}

// Login to a portal
async function loginPortal(portalId) {
    const username = document.getElementById(`username-${portalId}`).value;
    const password = document.getElementById(`password-${portalId}`).value;

    localStorage.setItem(`username-${portalId}`, username);
    localStorage.setItem(`password-${portalId}`, password);

    // Show loading state
    portalsInProgress.add(portalId);
    renderPortals();

    try {
        currentLoginController = new AbortController();

        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([{
                portal_id: portalId,
                username: username,
                password: password
            }]),
            signal: currentLoginController.signal
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const results = await response.json();
        results.forEach(result => {
            if (result.success) {
                loggedInPortals.add(result.portal_id);
                addNotification('success', getPortalName(result.portal_id), '', 'Login successful');
            } else {
                addNotification('error', getPortalName(result.portal_id), '', result.error || 'Login failed');
            }
        });

    } catch (error) {
        if (error.name !== 'AbortError') {
            addNotification('error', getPortalName(portalId), '', error.message);
        }
    } finally {
        currentLoginController = null;

        portalsInProgress.delete(portalId);
        renderPortals();
    }
}

// Logout from a portal
async function logoutPortal(portalId) {
    // Show loading state
    portalsInProgress.add(portalId);
    renderPortals();

    try {
        currentLogoutController = new AbortController();

        const response = await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ portal_ids: [portalId] }),
            signal: currentLogoutController.signal
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const results = await response.json();
        results.forEach(result => {
            if (result.success) {
                loggedInPortals.delete(result.portal_id);
                addNotification('success', getPortalName(result.portal_id), '', 'Logout successful');
            } else {
                addNotification('error', getPortalName(result.portal_id), '', result.error || 'Logout failed');
            }
        });

    } catch (error) {
        if (error.name !== 'AbortError') {
            addNotification('error', getPortalName(portalId), '', error.message);
        }
    } finally {
        currentLogoutController = null;

        portalsInProgress.delete(portalId);
        renderPortals();
    }
}

// Login to all portals
async function loginToAllPortals() {
    const credentials = [];

    // Only login to regular portals (exclude Excel files)
    portals.forEach(portal => {
        if (!loggedInPortals.has(portal.id)) {
            const username = document.getElementById(`username-${portal.id}`)?.value || '';
            const password = document.getElementById(`password-${portal.id}`)?.value || '';

            credentials.push({
                portal_id: portal.id,
                username: username,
                password: password
            });
        }
    });

    if (credentials.length === 0) {
        addNotification('info', 'Login', '', 'No portals to login to');
        return;
    }

    credentials.forEach(creds => {
        portalsInProgress.add(creds.portal_id)
    })
    renderPortals();

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const results = await response.json();
        results.forEach(result => {
            if (result.success) {
                loggedInPortals.add(result.portal_id);
                addNotification('success', getPortalName(result.portal_id), '', 'Login successful');
            } else {
                addNotification('error', getPortalName(result.portal_id), '', result.error || 'Login failed');
            }
        });
    } catch (error) {
        addNotification('error', 'Login', '', error.message);
    } finally {
        credentials.forEach(creds => {
            portalsInProgress.delete(creds.portal_id)
        })
        renderPortals();
    }
}

// Logout from all portals
async function logoutAllPortalsHandler() {
    const portalIds = Array.from(loggedInPortals);

    if (portalIds.length === 0) {
        addNotification('info', 'Logout', '', 'No portals to logout from');
        return;
    }

    portalIds.forEach(id => {
        portalsInProgress.add(id)
    })
    renderPortals();

    try {
        const response = await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ portal_ids: portalIds })
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const results = await response.json();
        results.forEach(result => {
            if (result.success) {
                loggedInPortals.delete(result.portal_id);
                addNotification('success', getPortalName(result.portal_id), '', 'Logout successful');
            } else {
                addNotification('error', getPortalName(result.portal_id), '', result.error || 'Logout failed');
            }
        });
    } catch (error) {
        addNotification('error', 'Logout', '', error.message);
    } finally {
        portalIds.forEach(id => {
            portalsInProgress.delete(id)
        })
        renderPortals();
    }
}

// Render Excel files
function renderExcelFiles() {
    const excelList = document.getElementById('excelList');
    excelList.innerHTML = '';

    console.log(excelPortals)

    if (excelPortals.length === 0) {
        excelList.innerHTML = '<div class="no-items">No Excel files uploaded</div>';
        return;
    }

    excelPortals.forEach(id => {
        const fileElement = document.createElement('div');
        fileElement.className = 'file-item';
        fileElement.innerHTML = `
            <span class="file-name">Excel Portal ${id}</span>
            <button class="btn btn-icon delete-excel" data-file-id="${id}">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;
        excelList.appendChild(fileElement);

        const deleteButton = fileElement.querySelector('.delete-excel');
        deleteButton.addEventListener('click', () => {
            deleteExcelFile(id);
        });
    });
}

// Upload Excel file
async function uploadExcelFile() {
    const fileInput = document.getElementById('excelUpload');
    const file = fileInput.files[0];

    if (!file) {
        addNotification('error', 'Excel', '', 'Please select a file to upload');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/excel`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
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

            throw new Error(errorMessage);
        }

        const result = await response.json();

        if (result.success) {
            excelPortals.push(result.portal_id);
            addNotification('success', 'Excel', '', `File uploaded successfully as portal ${result.portal_id}`);
        } else {
            addNotification('error', 'Excel', '', result.error || `Failed to upload`);
        }

        renderExcelFiles();
        renderFilterOptions();

        // Reset upload area
        fileInput.value = '';
        uploadArea.querySelector('p').textContent = 'Drag and drop Excel file here or click to browse';

    } catch (error) {
        addNotification('error', 'Excel', '', error.message);
    }
}

// Delete Excel file
function deleteExcelFile(fileId) {
    excelPortals = excelPortals.filter(id => id !== fileId);
    loggedInPortals.delete(fileId);

    renderExcelFiles();
    renderFilterOptions();

    addNotification('info', 'Excel', '', `Excel portal ${fileId} removed`);
}

// Render filter options
function renderFilterOptions() {
    const portalsFilterList = document.getElementById('portalsFilterList');
    const conditionsFilterList = document.getElementById('conditionsFilterList');

    // Portals filter
    portalsFilterList.innerHTML = '';

    // Add regular portals
    portals.forEach(portal => {
        const option = document.createElement('div');
        option.className = 'filter-option';
        option.innerHTML = `
            <input type="checkbox" id="portal-${portal.id}" value="${portal.id}" checked>
            <label for="portal-${portal.id}">${portal.name}</label>
        `;
        portalsFilterList.appendChild(option);
    });

    // Add Excel portals
    excelPortals.forEach(id => {
        const option = document.createElement('div');
        option.className = 'filter-option';
        option.innerHTML = `
            <input type="checkbox" id="excel-${id}" value="${id}" checked>
            <label for="excel-${id}">Excel Portal ${id}</label>
        `;
        portalsFilterList.appendChild(option);
    });

    // Conditions filter
    conditionsFilterList.innerHTML = '';
    conditions.forEach(condition => {
        const option = document.createElement('div');
        option.className = 'filter-option';
        option.innerHTML = `
            <input type="checkbox" id="condition-${condition.id}" value="${condition.id}" checked>
            <label for="condition-${condition.id}">${condition.code} - ${condition.name}</label>
        `;
        conditionsFilterList.appendChild(option);
    });

    // Update select all checkboxes
    updateSelectAllFilterCheckboxes();
}

// Toggle select all portals
function toggleSelectAllPortals() {
    const portalCheckboxes = document.querySelectorAll('#portalsFilterList input[type="checkbox"]');
    portalCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllPortals.checked;
    });
}

// Toggle select all conditions
function toggleSelectAllConditions() {
    const conditionCheckboxes = document.querySelectorAll('#conditionsFilterList input[type="checkbox"]');
    conditionCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllConditions.checked;
    });
}

// Update select all filter checkboxes
function updateSelectAllFilterCheckboxes() {
    const portalCheckboxes = document.querySelectorAll('#portalsFilterList input[type="checkbox"]');
    const conditionCheckboxes = document.querySelectorAll('#conditionsFilterList input[type="checkbox"]');

    // Listen for changes on individual checkboxes
    portalCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const allChecked = Array.from(portalCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(portalCheckboxes).some(cb => cb.checked);

            selectAllPortals.checked = allChecked;
            selectAllPortals.indeterminate = someChecked && !allChecked;
        });
    });

    conditionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const allChecked = Array.from(conditionCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(conditionCheckboxes).some(cb => cb.checked);

            selectAllConditions.checked = allChecked;
            selectAllConditions.indeterminate = someChecked && !allChecked;
        });
    });
}

// Apply table filters
function applyTableFilters() {
    const selectedPortals = Array.from(document.querySelectorAll('#portalsFilterList input:checked'))
        .map(input => parseInt(input.value));

    const selectedConditions = Array.from(document.querySelectorAll('#conditionsFilterList input:checked'))
        .map(input => parseInt(input.value));

    // If we have search results, filter them client-side
    if (allSearchResults.length > 0) {
        filterExistingResults(selectedPortals, selectedConditions);
    }

    addNotification('info', 'Filter', '', 'Filters applied');
    toggleModal(filterModal);
}

// Filter existing results
function filterExistingResults(selectedPortals, selectedConditions) {
    // Clear current display
    resultsTableBody.innerHTML = '';
    displayedPartNumbers.clear();
    selectedRows.clear();
    updateSelectionCount();

    let hasResults = false;

    // Filter and display results
    if (selectedPortals.length > 0 && selectedConditions.length > 0) {
        allSearchResults.forEach(result => {
            let atLeastOneSuccess = false;
            for (const portalResult of result.offers_statuses) {
                if (portalResult.success && portalResult.offers && portalResult.offers.length > 0) {
                    const filteredOffers = portalResult.offers.filter(offer => {
                        return selectedConditions.includes(offer.condition_id);
                    });

                    if (selectedPortals.includes(portalResult.portal_id) && filteredOffers.length > 0) {
                        atLeastOneSuccess = true;
                    }
                }
            }

            if (atLeastOneSuccess) {
                const partNumber = result.requested_part_number;

                // Add part number divider
                addPartNumberDivider(partNumber);
                displayedPartNumbers.add(partNumber);

                for (const portalResult of result.offers_statuses) {
                    if (portalResult.success && portalResult.offers && portalResult.offers.length > 0) {
                        // Check if portal is selected
                        if (!selectedPortals.includes(portalResult.portal_id)) {
                            continue; // Skip this portal
                        }

                        // Filter offers by condition
                        const filteredOffers = portalResult.offers.filter(offer => {
                            return selectedConditions.includes(offer.condition_id);
                        });

                        if (filteredOffers.length > 0) {
                            hasResults = true;

                            // Add filtered offers
                            filteredOffers.forEach(offer => {
                                addTableRow(offer, portalResult.portal_id);
                            });
                        }
                    }
                }
            }
        });
    }

    // Show no results message if needed
    if (!hasResults) {
        const noResultsRow = document.createElement('tr');
        noResultsRow.innerHTML = '<td colspan="11" class="no-results">No results match the selected filters</td>';
        resultsTableBody.appendChild(noResultsRow);
    }
}

// Reset table filters
function resetTableFilters() {
    document.querySelectorAll('#portalsFilterList input, #conditionsFilterList input').forEach(input => {
        input.checked = true;
    });

    selectAllPortals.checked = true;
    selectAllPortals.indeterminate = false;
    selectAllConditions.checked = true;
    selectAllConditions.indeterminate = false;

    const allPortals = Array.from(document.querySelectorAll('#portalsFilterList input'))
        .map(input => parseInt(input.value));
    const allConditions = Array.from(document.querySelectorAll('#conditionsFilterList input'))
        .map(input => parseInt(input.value));

    if (allSearchResults.length > 0) {
        filterExistingResults(allPortals, allConditions);
    }

    addNotification('info', 'Filter', '', 'Filters reset');
}

// Get portal name by ID
function getPortalName(portalId) {
    const portal = portals.find(p => p.id === portalId);
    if (portal) return portal.name;

    const excelPortal = excelPortals.find(id => id === portalId);
    if (excelPortal) return `Excel Portal ${excelPortal}`;

    return `Portal ${portalId}`;
}

// Add notification
function addNotification(type, source, partNumber, message) {
    const timestamp = new Date().toLocaleTimeString();
    const id = Date.now();

    const notification = {
        id,
        type,
        source,
        partNumber,
        message,
        timestamp
    };

    notifications.push(notification);
    notificationBadge.textContent = notifications.length;

    const notificationElement = document.createElement('div');
    notificationElement.className = `notification-item notification-${type}`;
    notificationElement.innerHTML = `
        <button class="notification-close-top" data-id="${id}">&times;</button>
        <div class="notification-content">
            <strong>${source}${partNumber ? ` (${partNumber})` : ''}</strong>: ${message}
        </div>
        <div class="notification-time">${timestamp}</div>
    `;

    const notificationList = document.getElementById('notificationList');
    notificationList.prepend(notificationElement);

    notificationElement.querySelector('.notification-close-top').addEventListener('click', function () {
        const id = parseInt(this.getAttribute('data-id'));
        removeNotification(id);
    });
}

// Remove notification
function removeNotification(id) {
    notifications = notifications.filter(n => n.id !== id);
    notificationBadge.textContent = notifications.length;

    const notificationElement = document.querySelector(`.notification-close-top[data-id="${id}"]`)?.closest('.notification-item');
    if (notificationElement) {
        notificationElement.remove();
    }
}

// Clear all notifications
function clearAllNotificationsHandler() {
    notifications = [];
    notificationBadge.textContent = '0';
    document.getElementById('notificationList').innerHTML = '';
}

// Toggle notification panel
function toggleNotificationPanel() {
    notificationPanel.classList.toggle('open');
}

// Toggle modal visibility
function toggleModal(modal) {
    modal.classList.toggle('active');

    if (modal === quotationModal && modal.classList.contains('active')) {
        updateQuotationItems();

        // Save global fields when modal is opened
        currentQuotationData.quotationNumber = document.getElementById('quotationNumber').value;
        currentQuotationData.logisticsCost = parseFloat(document.getElementById('logisticsCost').value) || 0;
        currentQuotationData.markup = parseFloat(document.getElementById('markup').value) || 0;
        currentQuotationData.incoterms = document.getElementById('incoterms').value;
        currentQuotationData.paymentTerms = document.getElementById('paymentTerms').value;
        saveQuotationData();
    }
}

// Show critical error
function showCriticalError(message) {
    document.getElementById('criticalErrorMessage').textContent = message;
    criticalError.style.display = 'flex';
}