// UI Manager Module
class UIManager {
    constructor() {
        this.searchResults = [];
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
        document.getElementById('exportBtn').addEventListener('click', () => this.exportSelected());

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
            this.showFatalError(CONFIG.MESSAGES.NO_PART_NUMBERS);
            return false;
        }

        if (selectedPortals.length === 0) {
            this.showFatalError(CONFIG.MESSAGES.NO_LOGGED_IN_PORTALS);
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
        const checkboxHeader = this.selectMode ? '<th><input type="checkbox" id="selectAllCheckbox"></th>' : '';

        container.innerHTML = `
                <table class="results-table">
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
        this.filteredResults = [];
        this.selectedRows.clear();
    }

    // Add search result to table
    addSearchResult(result) {
        this.searchResults.push(result);
        this.applyTableFilters();
    }

    // Apply filters to table results
    applyTableFilters() {
        this.filteredResults = this.searchResults.filter(result => {
            return this.currentFilters.portal_ids.includes(result.portal_id) &&
                (result.condition_id === 0 || this.currentFilters.conditions.includes(result.condition_id));
        });

        this.updateTableDisplay();
    }

    // Update table display
    updateTableDisplay() {
        const tbody = document.getElementById('resultsTableBody');
        if (!tbody) return;

        tbody.innerHTML = this.filteredResults.map((result, index) => {
            const portal = this.portals.find(p => p.id === result.portal_id);
            const condition = this.conditions.find(c => c.id === result.condition_id);
            const isSelected = this.selectedRows.has(index);

            const checkboxCell = this.selectMode ?
                `<td><input type="checkbox" class="row-checkbox" data-index="${index}" ${isSelected ? 'checked' : ''}></td>` : '';

            return `
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
            `;
        }).join('');

        // Add event listeners for row checkboxes
        if (this.selectMode) {
            tbody.querySelectorAll('.row-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    this.toggleRowSelection(parseInt(e.target.dataset.index), e.target.checked);
                });
            });
        }
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
        const exportBtn = document.getElementById('exportBtn');

        if (this.selectMode) {
            btn.innerHTML = '<span class="icon">❌</span> Exit Select';
            exportBtn.style.display = 'flex';
        } else {
            btn.innerHTML = '<span class="icon">☑️</span> Select Mode';
            exportBtn.style.display = 'none';
            this.selectedRows.clear();
        }

        this.updateTableDisplay();
    }

    toggleRowSelection(index, selected) {
        if (selected) {
            this.selectedRows.add(index);
        } else {
            this.selectedRows.delete(index);
        }
        this.updateTableDisplay();
    }

    selectAllRows(selected) {
        if (selected) {
            this.filteredResults.forEach((_, index) => this.selectedRows.add(index));
        } else {
            this.selectedRows.clear();
        }
        this.updateTableDisplay();
    }

    // Export functionality
    exportSelected() {
        if (this.selectedRows.size === 0) {
            this.addNotification(CONFIG.MESSAGES.NO_ROWS_SELECTED, null, null, 'warning');
            return;
        }

        const selectedData = Array.from(this.selectedRows).map(index => this.filteredResults[index]);
        window.appController.exportData(selectedData);
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

        // Auto-show panel if new error
        if (count > 0 && !document.getElementById('errorPanel').classList.contains('show')) {
            this.showErrorPanel();
        }
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