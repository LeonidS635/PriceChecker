// UI Manager Module
class UIManager {
    constructor() {
        this.searchResults = [];
        this.partGroups = new Map(); // Group results by part number
        this.filteredResults = [];
        this.selectedRows = new Set();
        this.selectMode = false;
        this.processedCount = 0;
        this.totalCount = 0;
        this.currentFilters = {
            portal_ids: [],
            conditions: []
        };
        this.notifications = [];
        this.portals = [];
        this.conditions = [];
        this.excelFiles = [];
    }

    // Initialize UI
    init() {
        this.setupEventListeners();
        this.setupModals();
    }

    // Setup event listeners
    setupEventListeners() {
        // Header buttons
        document.getElementById('settingsBtn').addEventListener('click', () => this.showModal('settingsModal'));
        document.getElementById('portalManagementBtn').addEventListener('click', () => this.showPortalManagementModal());
        document.getElementById('excelManagementBtn').addEventListener('click', () => this.showExcelManagementModal());

        // Search panel
        document.getElementById('filtersBtn').addEventListener('click', () => this.showFiltersModal());
        document.getElementById('searchBtn').addEventListener('click', () => this.startSearch());
        document.getElementById('cancelSearchBtn').addEventListener('click', () => this.cancelSearch());

        // Export controls
        document.getElementById('selectModeBtn').addEventListener('click', () => this.toggleSelectMode());
        document.getElementById('quotationBtn').addEventListener('click', () => this.showQuotationModal());

        // Error panel
        document.getElementById('errorToggleBtn').addEventListener('click', () => this.toggleErrorPanel());
        document.getElementById('closeErrorPanel').addEventListener('click', () => this.hideErrorPanel());
        document.getElementById('clearAllErrors').addEventListener('click', () => this.clearAllNotifications());

        // Excel file upload
        document.getElementById('uploadExcelBtn').addEventListener('click', () => this.triggerFileUpload());
        document.getElementById('excelFileInput').addEventListener('change', (e) => this.handleFileUpload(e));

        // Enter key in search input
        document.getElementById('partNumbersInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.startSearch();
            }
        });
    }

    // Setup modal functionality
    setupModals() {
        // Close modals on background click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });

        // Close modals on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    // Modal management
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = 'auto';
    }

    // Update configuration data
    updateConfig(config) {
        this.portals = config.portals || [];
        this.conditions = config.conditions || [];

        // Set default filters to all portals and conditions
        this.currentFilters = {
            portal_ids: this.portals.map(p => p.id),
            conditions: this.conditions.map(c => c.id)
        };

        this.updateFilterDisplays();
    }

    // Update filter displays
    updateFilterDisplays() {
        this.updateFiltersModal();
        this.updatePortalManagementModal();
    }

    // Update filters modal
    updateFiltersModal() {
        const portalContainer = document.getElementById('portalFilters');
        const conditionContainer = document.getElementById('conditionFilters');

        portalContainer.innerHTML = this.portals.map(portal => `
            <label class="checkbox-item">
                <input type="checkbox" value="${portal.id}" ${this.currentFilters.portal_ids.includes(portal.id) ? 'checked' : ''}>
                <span>${portal.name}</span>
            </label>
        `).join('');

        conditionContainer.innerHTML = this.conditions.map(condition => `
            <label class="checkbox-item">
                <input type="checkbox" value="${condition.id}" ${this.currentFilters.conditions.includes(condition.id) ? 'checked' : ''}>
                <span>${condition.name}</span>
            </label>
        `).join('');
    }

    // Show filters modal
    showFiltersModal() {
        this.updateFiltersModal();
        this.showModal('filtersModal');
    }

    // Apply filters
    applyFilters() {
        const selectedPortals = Array.from(document.querySelectorAll('#portalFilters input:checked'))
            .map(checkbox => parseInt(checkbox.value));

        const selectedConditions = Array.from(document.querySelectorAll('#conditionFilters input:checked'))
            .map(checkbox => parseInt(checkbox.value));

        this.currentFilters = {
            portal_ids: selectedPortals,
            conditions: selectedConditions
        };

        this.closeModal('filtersModal');
        this.updateFilterButton();
        this.applyTableFilters();
    }

    // Update filter button appearance
    updateFilterButton() {
        const btn = document.getElementById('filtersBtn');
        const totalPortals = this.portals.length;
        const selectedPortals = this.currentFilters.portal_ids.length;

        if (selectedPortals > 0 && selectedPortals < totalPortals) {
            btn.innerHTML = `<span class="icon">🔧</span> Filters (${selectedPortals})`;
            btn.classList.add('btn-primary');
            btn.classList.remove('btn-secondary');
        } else {
            btn.innerHTML = `<span class="icon">🔧</span> Filters`;
            btn.classList.add('btn-secondary');
            btn.classList.remove('btn-primary');
        }
    }

    // Portal Management Modal
    showPortalManagementModal() {
        this.updatePortalManagementModal();
        this.showModal('portalManagementModal');
    }

    updatePortalManagementModal() {
        const container = document.getElementById('portalLoginList');
        container.innerHTML = this.portals.map(portal => {
            const isLoggedIn = window.appState.loggedInPortals.includes(portal.id);
            return `
                <div class="portal-login-item ${isLoggedIn ? 'logged-in' : ''}" data-portal-id="${portal.id}">
                    <div class="portal-header">
                        <input type="checkbox" class="portal-checkbox" value="${portal.id}" checked>
                        <span class="portal-name">${portal.name}</span>
                        <span class="portal-status ${isLoggedIn ? 'online' : 'offline'}">
                            ${isLoggedIn ? 'Logged In' : 'Not Logged In'}
                        </span>
                    </div>
                    <div class="portal-credentials">
                        <div class="credential-group">
                            <label>Username:</label>
                            <input type="text" placeholder="Username" data-field="username">
                        </div>
                        <div class="credential-group">
                            <label>Password:</label>
                            <input type="password" placeholder="Password" data-field="password">
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add event listeners for select/deselect all
        document.getElementById('selectAllPortalsBtn').addEventListener('click', () => {
            document.querySelectorAll('.portal-checkbox').forEach(cb => cb.checked = true);
        });

        document.getElementById('deselectAllPortalsBtn').addEventListener('click', () => {
            document.querySelectorAll('.portal-checkbox').forEach(cb => cb.checked = false);
        });
    }

    // Get login credentials from modal
    getLoginCredentials() {
        const credentials = [];
        const selectedPortals = Array.from(document.querySelectorAll('.portal-checkbox:checked'));

        selectedPortals.forEach(checkbox => {
            const portalId = parseInt(checkbox.value);
            const portalItem = checkbox.closest('.portal-login-item');
            const username = portalItem.querySelector('[data-field="username"]').value;
            const password = portalItem.querySelector('[data-field="password"]').value;

            credentials.push({
                portal_id: portalId,
                username: username,
                password: password
            });
        });

        return credentials;
    }

    // Show login status
    showLoginStatus(message, type) {
        const statusDiv = document.getElementById('loginStatus');
        statusDiv.innerHTML = `<div class="login-status ${type}">${message}</div>`;
    }

    // Set login button loading state
    setLoginButtonLoading(loading) {
        const loginBtn = document.getElementById('performLoginBtn');
        const cancelBtn = document.getElementById('cancelLoginBtn');

        loginBtn.disabled = loading;
        loginBtn.style.display = loading ? 'none' : 'flex';
        cancelBtn.style.display = loading ? 'flex' : 'none';

        if (loading) {
            loginBtn.innerHTML = '<span class="icon">⏳</span> Logging in...';
        } else {
            loginBtn.innerHTML = '<span class="icon">🔑</span> Login';
        }
    }

    // Excel Management Modal
    showExcelManagementModal() {
        this.updateExcelFilesList();
        this.showModal('excelManagementModal');
    }

    updateExcelFilesList() {
        const container = document.getElementById('excelFilesList');

        if (this.excelFiles.length === 0) {
            container.innerHTML = '<p class="no-files">No Excel files uploaded</p>';
            return;
        }

        container.innerHTML = this.excelFiles.map(file => `
            <div class="excel-file-item">
                <span class="excel-file-name">${file.name}</span>
                <button class="excel-file-delete" onclick="window.uiManager.deleteExcelFile(${file.id})">
                    Delete
                </button>
            </div>
        `).join('');
    }

    triggerFileUpload() {
        document.getElementById('excelFileInput').click();
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (file) {
            window.appController.uploadExcelFile(file);
        }
    }

    deleteExcelFile(fileId) {
        window.appController.deleteExcelFile(fileId);
    }

    // Search functionality
    startSearch() {
        window.appController.performSearch();
    }

    cancelSearch() {
        window.appController.cancelSearch();
    }

    // Get part numbers from input
    getPartNumbers() {
        const input = document.getElementById('partNumbersInput');
        const text = input.value.trim();

        if (!text) return [];

        return text.split(/[,\s\n]+/)
            .map(num => num.trim())
            .filter(num => num.length > 0);
    }

    // Validate search form
    validateSearchForm() {
        const partNumbers = this.getPartNumbers();
        const selectedPortals = this.currentFilters.portal_ids.filter(id =>
            window.appState.loggedInPortals.includes(id)
        );

        if (partNumbers.length === 0) {
            this.addNotification(CONFIG.MESSAGES.NO_PART_NUMBERS, null, null, 'warning');
            return false;
        }

        if (selectedPortals.length === 0) {
            this.addNotification(CONFIG.MESSAGES.NO_LOGGED_IN_PORTALS, null, null, 'warning');
            return false;
        }

        return true;
    }

    // Progress management
    showProgress(current, total) {
        this.processedCount = current;
        this.totalCount = total;

        const container = document.getElementById('progressContainer');
        const progressText = document.getElementById('progressText');
        const progressStats = document.getElementById('progressStats');
        const progressFill = document.getElementById('progressFill');

        container.style.display = 'block';
        progressText.textContent = 'Searching...';
        progressStats.textContent = `${current} of ${total}`;

        const percentage = total > 0 ? (current / total) * 100 : 0;
        progressFill.style.width = `${percentage}%`;
    }

    hideProgress() {
        document.getElementById('progressContainer').style.display = 'none';
    }

    // Set search button loading state
    setSearchButtonLoading(loading) {
        const btn = document.getElementById('searchBtn');
        btn.disabled = loading;
        btn.innerHTML = loading ?
            '<span class="icon">⏳</span> Searching...' :
            '<span class="icon">🔍</span> Search';
    }

    // Results table management
    initResultsTable() {
        const container = document.getElementById('resultsTable');

        const tableClass = this.selectMode ? 'results-table select-mode' : 'results-table';
        const checkboxHeader = this.selectMode ? '<th><input type="checkbox" class="select-all-checkbox" id="selectAllCheckbox"></th>' : '';

        container.innerHTML = `
            <table class="${tableClass}">
                <thead>
                    <tr>
                        ${checkboxHeader}
                        ${CONFIG.TABLE_COLUMNS.map(col => `<th>${col.title}</th>`).join('')}
                    </tr>
                </thead>
                <tbody id="resultsTableBody">
                </tbody>
            </table>
        `;

        // Add select all functionality
        if (this.selectMode) {
            document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
                this.selectAllRows(e.target.checked);
            });
        }

        this.searchResults = [];
        this.partGroups.clear();
        this.filteredResults = [];
        this.selectedRows.clear();
        this.updateSelectedCount();
    }

    // Add search result to table
    addSearchResult(result) {
        this.searchResults.push(result);

        // Group by part number
        const partNumber = result.requested_part_number;
        if (!this.partGroups.has(partNumber)) {
            this.partGroups.set(partNumber, []);
        }
        this.partGroups.get(partNumber).push(result);

        this.applyTableFilters();
    }

    // Apply filters to table results
    applyTableFilters() {
        // Filter each part group
        const filteredGroups = new Map();

        for (const [partNumber, results] of this.partGroups) {
            const filteredResults = results.filter(result => {
                return this.currentFilters.portal_ids.includes(result.portal_id) &&
                    (result.condition_id === 0 || this.currentFilters.conditions.includes(result.condition_id));
            });

            if (filteredResults.length > 0) {
                filteredGroups.set(partNumber, filteredResults);
            }
        }

        this.filteredResults = [];
        for (const results of filteredGroups.values()) {
            this.filteredResults.push(...results);
        }

        this.updateTableDisplay(filteredGroups);
    }

    // Update table display with part separators
    updateTableDisplay(filteredGroups = null) {
        const tbody = document.getElementById('resultsTableBody');
        if (!tbody) return;

        if (!filteredGroups) {
            // Rebuild filtered groups
            filteredGroups = new Map();
            for (const [partNumber, results] of this.partGroups) {
                const filteredResults = results.filter(result => {
                    return this.currentFilters.portal_ids.includes(result.portal_id) &&
                        (result.condition_id === 0 || this.currentFilters.conditions.includes(result.condition_id));
                });

                if (filteredResults.length > 0) {
                    filteredGroups.set(partNumber, filteredResults);
                }
            }
        }

        let rowIndex = 0;
        const rows = [];
        const totalColumns = this.selectMode ? CONFIG.TABLE_COLUMNS.length + 1 : CONFIG.TABLE_COLUMNS.length;

        for (const [partNumber, results] of filteredGroups) {
            // Add part separator
            rows.push(`
                <tr class="part-separator">
                    <td colspan="${totalColumns}">${partNumber}</td>
                </tr>
            `);

            // Add part rows
            results.forEach(result => {
                const portal = this.portals.find(p => p.id === result.portal_id);
                const condition = this.conditions.find(c => c.id === result.condition_id);
                const isSelected = this.selectedRows.has(rowIndex);

                const checkboxCell = this.selectMode ?
                    `<td><input type="checkbox" class="row-checkbox" data-index="${rowIndex}" ${isSelected ? 'checked' : ''}></td>` : '';

                rows.push(`
                    <tr class="${isSelected ? 'selected' : ''}">
                        ${checkboxCell}
                        <td>${portal ? portal.name : 'Unknown'}</td>
                        <td>${result.part_number || ''}</td>
                        <td>${this.formatCellContent(result.description || '')}</td>
                        <td>${condition && condition.id !== 0 ? condition.code : ''}</td>
                        <td>${result.price && result.price > 0 ? '$' + result.price : ''}</td>
                        <td>${result.qty || ''}</td>
                        <td>${result.lead_time || ''}</td>
                        <td>${result.warehouse || ''}</td>
                        <td>${this.formatArray(result.interchangeable)}</td>
                        <td>${this.formatCellContent(result.other_information || '')}</td>
                    </tr>
                `);

                rowIndex++;
            });
        }

        tbody.innerHTML = rows.join('');

        // Add event listeners for row checkboxes
        if (this.selectMode) {
            tbody.querySelectorAll('.row-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    this.toggleRowSelection(parseInt(e.target.dataset.index), e.target.checked);
                });
            });
        }

        this.updateSelectAllCheckbox();
    }

    // Format cell content for display
    formatCellContent(content) {
        if (!content) return '';
        const text = String(content);
        return text.length > CONFIG.UI.MAX_CELL_LENGTH ?
            text.substring(0, CONFIG.UI.MAX_CELL_LENGTH) + '...' : text;
    }

    // Format array for display
    formatArray(arr) {
        if (!Array.isArray(arr) || arr.length === 0) return '';
        return arr.join(', ');
    }

    // Row selection management
    toggleSelectMode() {
        this.selectMode = !this.selectMode;
        const btn = document.getElementById('selectModeBtn');
        const quotationBtn = document.getElementById('quotationBtn');

        if (this.selectMode) {
            btn.innerHTML = '<span class="icon">❌</span> Exit Select';
            quotationBtn.style.display = 'flex';
        } else {
            btn.innerHTML = '<span class="icon">☑️</span> Select Mode';
            quotationBtn.style.display = 'none';
            this.selectedRows.clear();
        }

        this.updateTableDisplay();
        this.updateSelectedCount();
    }

    toggleRowSelection(index, selected) {
        if (selected) {
            this.selectedRows.add(index);
        } else {
            this.selectedRows.delete(index);
        }
        this.updateTableDisplay();
        this.updateSelectedCount();
        this.updateSelectAllCheckbox();
    }

    selectAllRows(selected) {
        if (selected) {
            this.filteredResults.forEach((_, index) => this.selectedRows.add(index));
        } else {
            this.selectedRows.clear();
        }
        this.updateTableDisplay();
        this.updateSelectedCount();
    }

    updateSelectAllCheckbox() {
        const checkbox = document.getElementById('selectAllCheckbox');
        if (!checkbox) return;

        const visibleRowCount = this.filteredResults.length;
        const selectedVisibleCount = this.filteredResults.filter((_, index) =>
            this.selectedRows.has(index)).length;

        if (selectedVisibleCount === 0) {
            checkbox.indeterminate = false;
            checkbox.checked = false;
        } else if (selectedVisibleCount === visibleRowCount) {
            checkbox.indeterminate = false;
            checkbox.checked = true;
        } else {
            checkbox.indeterminate = true;
            checkbox.checked = false;
        }
    }

    updateSelectedCount() {
        const countSpan = document.getElementById('selectedCount');
        if (countSpan) {
            countSpan.textContent = this.selectedRows.size;
        }
    }

    // Quotation functionality
    showQuotationModal() {
        if (this.selectedRows.size === 0) {
            this.addNotification(CONFIG.MESSAGES.NO_ROWS_SELECTED, null, null, 'warning');
            return;
        }

        this.updateQuotationModal();
        this.showModal('quotationModal');
    }

    updateQuotationModal() {
        const container = document.getElementById('quotationItemsList');
        const selectedItems = Array.from(this.selectedRows).map(index => this.filteredResults[index]);

        container.innerHTML = selectedItems.map((item, index) => {
            const portal = this.portals.find(p => p.id === item.portal_id);
            const condition = this.conditions.find(c => c.id === item.condition_id);

            return `
                <div class="quotation-item" data-index="${index}">
                    <div class="quotation-item-header">
                        <span class="quotation-item-part">${item.part_number || 'N/A'}</span>
                        <span class="quotation-item-portal">${portal ? portal.name : 'Unknown'}</span>
                    </div>
                    <div class="quotation-item-fields">
                        <div class="quotation-field-group">
                            <label>Description:</label>
                            <input type="text" data-field="description" value="${item.description || ''}">
                        </div>
                        <div class="quotation-field-group">
                            <label>Condition:</label>
                            <input type="text" data-field="condition" value="${condition && condition.id !== 0 ? condition.code : ''}">
                        </div>
                        <div class="quotation-field-group">
                            <label>Price ($):</label>
                            <input type="number" step="0.01" data-field="price" value="${item.price || ''}">
                        </div>
                        <div class="quotation-field-group">
                            <label>Lead Time:</label>
                            <input type="text" data-field="lead_time" value="${item.lead_time || ''}">
                        </div>
                        <div class="quotation-field-group">
                            <label>Quantity:</label>
                            <input type="number" data-field="qty" value="${item.qty || 1}">
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    getQuotationData() {
        const quotationNumber = parseInt(document.getElementById('quotationNumber').value.trim());

        if (!quotationNumber) {
            this.addNotification(CONFIG.MESSAGES.NO_QUOTATION_NUMBER, null, null, 'warning');
            return null;
        }

        const globalLogisticsPrice = parseFloat(document.getElementById('globalLogisticsPrice').value) || 0;
        const globalMarkup = parseFloat(document.getElementById('globalMarkup').value) || 1.0;

        const items = [];
        document.querySelectorAll('.quotation-item').forEach(itemEl => {
            const index = parseInt(itemEl.dataset.index);
            const originalItem = Array.from(this.selectedRows)[index];
            const result = this.filteredResults[originalItem];

            const item = {
                portal_id: result.portal_id,
                part_number: itemEl.querySelector('[class="quotation-item-part"]').value || result.part_number,
                description: itemEl.querySelector('[data-field="description"]').value || result.description,
                condition: itemEl.querySelector('[data-field="condition"]').value,
                price: parseFloat(itemEl.querySelector('[data-field="price"]').value) || 0,
                lead_time: parseInt(itemEl.querySelector('[data-field="lead_time"]').value || result.lead_time),
                qty: parseInt(itemEl.querySelector('[data-field="qty"]').value) || 1,
                logistics_price: globalLogisticsPrice,
                markup: globalMarkup
            };

            items.push(item);
        });

        return {
            quotation_number: quotationNumber,
            logistics_cost: globalLogisticsPrice,
            markup: globalMarkup,
            offers: items
        };
    }

    // Notification management
    addNotification(message, portalId = null, partNumber = null, type = 'error') {
        const portal = portalId ? this.portals.find(p => p.id === portalId) : null;

        const notification = {
            id: Date.now() + Math.random(),
            type: type,
            message: message,
            portal: portal ? portal.name : null,
            partNumber: partNumber,
            timestamp: new Date()
        };

        this.notifications.unshift(notification); // Add to beginning

        // Limit notifications
        if (this.notifications.length > CONFIG.UI.MAX_NOTIFICATIONS) {
            this.notifications = this.notifications.slice(0, CONFIG.UI.MAX_NOTIFICATIONS);
        }

        this.updateNotificationDisplay();
        this.updateErrorCounter();

        // Don't auto-show panel anymore, just update counter
    }

    updateNotificationDisplay() {
        const container = document.getElementById('errorList');
        container.innerHTML = this.notifications.map(notification => `
            <div class="notification-item ${notification.type}" data-id="${notification.id}">
                <div class="notification-header">
                    <span class="notification-time">${notification.timestamp.toLocaleTimeString()}</span>
                </div>
                ${notification.portal ? `<div class="notification-portal">${notification.portal}</div>` : ''}
                ${notification.partNumber ? `<div class="notification-part">Part: ${notification.partNumber}</div>` : ''}
                <div class="notification-message">${notification.message}</div>
                <button class="notification-close" onclick="window.uiManager.removeNotification('${notification.id}')">×</button>
            </div>
        `).join('');
    }

    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.updateNotificationDisplay();
        this.updateErrorCounter();
    }

    clearAllNotifications() {
        this.notifications = [];
        this.updateNotificationDisplay();
        this.updateErrorCounter();
    }

    updateErrorCounter() {
        const counter = document.getElementById('errorCount');
        const count = this.notifications.length;

        counter.textContent = count;
        counter.classList.toggle('zero', count === 0);

        // Don't auto-show panel, just update counter
    }

    // Error panel management
    toggleErrorPanel() {
        const panel = document.getElementById('errorPanel');
        if (panel.classList.contains('show')) {
            this.hideErrorPanel();
        } else {
            this.showErrorPanel();
        }
    }

    showErrorPanel() {
        document.getElementById('errorPanel').classList.add('show');
    }

    hideErrorPanel() {
        document.getElementById('errorPanel').classList.remove('show');
    }

    // Fatal error display
    showFatalError(message) {
        const overlay = document.getElementById('fatalErrorOverlay');
        const messageEl = document.getElementById('fatalErrorMessage');

        messageEl.textContent = message;
        overlay.style.display = 'block';
    }

    // Update portal statuses
    updatePortalStatuses(loggedInPortals) {
        // Update portal management modal if open
        if (document.getElementById('portalManagementModal').classList.contains('show')) {
            this.updatePortalManagementModal();
        }
    }

    // Update Excel files list
    updateExcelFiles(files) {
        this.excelFiles = files;

        // Add Excel files as portals
        files.forEach(file => {
            if (!this.portals.find(p => p.id === file.id)) {
                this.portals.push({
                    id: file.id,
                    name: file.name
                });
            }
        });

        this.updateFilterDisplays();

        // Update Excel management modal if open
        if (document.getElementById('excelManagementModal').classList.contains('show')) {
            this.updateExcelFilesList();
        }
    }

    // Remove Excel file
    removeExcelFile(fileId) {
        // Remove from Excel files
        this.excelFiles = this.excelFiles.filter(f => f.id !== fileId);

        // Remove from portals
        this.portals = this.portals.filter(p => p.id !== fileId);

        // Remove from filters
        this.currentFilters.portal_ids = this.currentFilters.portal_ids.filter(id => id !== fileId);

        // Update displays
        this.updateFilterDisplays();
        this.updateFilterButton();

        // Update Excel management modal if open
        if (document.getElementById('excelManagementModal').classList.contains('show')) {
            this.updateExcelFilesList();
        }
    }

    // Prepare for search
    prepareForSearch() {
        this.initResultsTable();
        this.hideProgress();
        this.selectedRows.clear();
        this.updateSelectedCount();

        const partNumbers = this.getPartNumbers();
        this.showProgress(0, partNumbers.length);
    }

    // Complete search
    completeSearch() {
        this.hideProgress();
        this.setSearchButtonLoading(false);
    }

    // Update search progress
    updateSearchProgress(processed) {
        this.showProgress(processed, this.totalCount);
    }
}

// Global functions for HTML onclick handlers
function closeModal(modalId) {
    window.uiManager.closeModal(modalId);
}

function applyFilters() {
    window.uiManager.applyFilters();
}

function performLogin() {
    window.appController.performLogin();
}

function cancelLogin() {
    window.appController.cancelLogin();
}

function formQuotation() {
    window.appController.formQuotation();
}