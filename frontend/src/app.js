// Main Application Controller
class AppController {
    constructor() {
        this.portals = [];
        this.conditions = [];
        this.loggedInPortals = [];
        this.excelFiles = [];
        this.isSearching = false;
        this.isLoggingIn = false;
    }

    // Initialize application
    async init() {
        try {
            // Initialize UI
            window.uiManager.init();

            // Load configuration from server
            await this.loadConfig();

            // Load Excel files list
            await this.loadExcelFiles();

            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Initialization error:', error);
            this.handleFatalError(error);
        }
    }

    // Load configuration (portals and conditions)
    async loadConfig() {
        try {
            const config = await apiClient.getConfig();

            this.portals = config.portals || [];
            this.conditions = config.conditions || [];

            // Update UI with configuration
            window.uiManager.updateConfig({
                portals: this.portals,
                conditions: this.conditions
            });

            console.log('Configuration loaded:', {
                portals: this.portals.length,
                conditions: this.conditions.length
            });
        } catch (error) {
            console.error('Failed to load configuration:', error);
            throw error;
        }
    }

    // Load Excel files list
    async loadExcelFiles() {
        try {
            const response = await apiClient.getExcelFiles();

            if (response.success) {
                // Convert file IDs to file objects
                this.excelFiles = response.file_ids.map(id => ({
                    id: id,
                    name: `Excel File ${id}` // Server should provide actual names
                }));

                window.uiManager.updateExcelFiles(this.excelFiles);
                console.log('Excel files loaded:', this.excelFiles.length);
            } else {
                console.warn('Failed to load Excel files:', response.error);
            }
        } catch (error) {
            console.warn('Error loading Excel files:', error.message);
            // Not critical, continue without Excel files
        }
    }

    // Perform login
    async performLogin() {
        if (this.isLoggingIn) {
            console.log('Login already in progress');
            return;
        }

        const credentials = window.uiManager.getLoginCredentials();

        if (credentials.length === 0) {
            window.uiManager.showLoginStatus(CONFIG.MESSAGES.NO_PORTALS_SELECTED, 'error');
            return;
        }

        this.isLoggingIn = true;
        window.uiManager.setLoginButtonLoading(true);
        window.uiManager.showLoginStatus(CONFIG.MESSAGES.LOGIN_PROCESSING, 'loading');

        try {
            const response = await apiClient.login(credentials);

            // Process login results
            const successfulLogins = [];
            const failedLogins = [];

            response.forEach(result => {
                if (result.success) {
                    successfulLogins.push(result.portal_id);
                } else {
                    failedLogins.push({
                        portal_id: result.portal_id,
                        error: result.error
                    });

                    // Add error to notifications
                    window.uiManager.addNotification(
                        result.error,
                        result.portal_id,
                        null,
                        'error'
                    );
                }
            });

            // Update logged in portals
            this.loggedInPortals = [...new Set([...this.loggedInPortals, ...successfulLogins])];

            // Update UI
            window.uiManager.updatePortalStatuses(this.loggedInPortals);

            // Show status message
            if (successfulLogins.length === credentials.length) {
                window.uiManager.showLoginStatus(
                    `${CONFIG.MESSAGES.LOGIN_SUCCESS}: ${successfulLogins.length} portals`,
                    'success'
                );
            } else {
                window.uiManager.showLoginStatus(
                    `Partial login: ${successfulLogins.length}/${credentials.length} successful`,
                    'success'
                );
            }

            console.log('Login completed:', {
                successful: successfulLogins.length,
                failed: failedLogins.length
            });

        } catch (error) {
            console.error('Login error:', error);

            if (error.isFatal) {
                this.handleFatalError(error);
            } else {
                window.uiManager.showLoginStatus(
                    `${CONFIG.MESSAGES.LOGIN_ERROR}: ${error.message}`,
                    'error'
                );
            }
        } finally {
            this.isLoggingIn = false;
            window.uiManager.setLoginButtonLoading(false);
        }
    }

    // Cancel login
    cancelLogin() {
        if (this.isLoggingIn) {
            apiClient.cancelLogin();
            this.isLoggingIn = false;
            window.uiManager.setLoginButtonLoading(false);
            window.uiManager.showLoginStatus('Login cancelled', 'info');
        }
    }

    // Perform search
    async performSearch() {
        if (this.isSearching) {
            console.log('Search already in progress');
            return;
        }

        // Validate search form
        if (!window.uiManager.validateSearchForm()) {
            return;
        }

        this.isSearching = true;
        window.uiManager.setSearchButtonLoading(true);
        window.uiManager.prepareForSearch();

        const partNumbers = window.uiManager.getPartNumbers();
        const filters = {
            portal_ids: window.uiManager.currentFilters.portal_ids.filter(id =>
                this.loggedInPortals.includes(id)
            ),
            conditions: window.uiManager.currentFilters.conditions
        };

        try {
            const response = await apiClient.search(partNumbers, filters);

            // Create streaming response handler
            const streamHandler = new StreamingResponseHandler(
                // onResult - handle search result
                (result) => {
                    window.uiManager.addSearchResult(result);
                },
                // onError - handle error
                (error, portalId, partNumber, type = 'error') => {
                    window.uiManager.addNotification(error, portalId, partNumber, type);
                },
                // onComplete - search completed
                () => {
                    this.completeSearch();
                },
                // onProgress - update progress
                (processed) => {
                    window.uiManager.updateSearchProgress(processed);
                }
            );

            // Start processing streaming response
            await streamHandler.handleResponse(response);

        } catch (error) {
            console.error('Search error:', error);

            if (error.isFatal) {
                this.handleFatalError(error);
            } else {
                window.uiManager.addNotification(
                    `${CONFIG.MESSAGES.SEARCH_ERROR}: ${error.message}`,
                    null,
                    null,
                    'error'
                );
                this.completeSearch();
            }
        }
    }

    // Cancel search
    cancelSearch() {
        if (this.isSearching) {
            apiClient.cancelSearch();
            this.completeSearch();
            window.uiManager.addNotification(
                CONFIG.MESSAGES.SEARCH_CANCELLED,
                null,
                null,
                'info'
            );
        }
    }

    // Complete search
    completeSearch() {
        this.isSearching = false;
        window.uiManager.completeSearch();
        console.log('Search completed');
    }

    // Export data
    async exportData(selectedData) {
        try {
            const response = await apiClient.exportData(selectedData);

            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'export.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            window.uiManager.addNotification(
                CONFIG.MESSAGES.EXPORT_SUCCESS,
                null,
                null,
                'info'
            );

            console.log('Export completed successfully');

        } catch (error) {
            console.error('Export error:', error);

            window.uiManager.addNotification(
                `${CONFIG.MESSAGES.EXPORT_ERROR}: ${error.message}`,
                null,
                null,
                'error'
            );
        }
    }

    // Upload Excel file
    async uploadExcelFile(file) {
        try {
            const response = await apiClient.uploadExcelFile(file);

            if (response.success) {
                // Add new portal for the Excel file
                const newPortal = {
                    id: response.portal_id,
                    name: file.name
                };

                this.portals.push(newPortal);
                this.excelFiles.push(newPortal);

                // Update UI
                window.uiManager.updateConfig({
                    portals: this.portals,
                    conditions: this.conditions
                });

                window.uiManager.addNotification(
                    CONFIG.MESSAGES.EXCEL_UPLOAD_SUCCESS,
                    null,
                    null,
                    'info'
                );

                console.log('Excel file uploaded:', newPortal);
            } else {
                window.uiManager.addNotification(
                    `${CONFIG.MESSAGES.EXCEL_UPLOAD_ERROR}: ${response.error}`,
                    null,
                    null,
                    'error'
                );
            }
        } catch (error) {
            console.error('Excel upload error:', error);

            window.uiManager.addNotification(
                `${CONFIG.MESSAGES.EXCEL_UPLOAD_ERROR}: ${error.message}`,
                null,
                null,
                'error'
            );
        }
    }

    // Delete Excel file (local only)
    deleteExcelFile(fileId) {
        // Remove from local arrays
        this.excelFiles = this.excelFiles.filter(f => f.id !== fileId);
        this.portals = this.portals.filter(p => p.id !== fileId);
        this.loggedInPortals = this.loggedInPortals.filter(id => id !== fileId);
        // Update UI
        window.uiManager.removeExcelFile(fileId);

        window.uiManager.addNotification(
            CONFIG.MESSAGES.EXCEL_DELETE_SUCCESS,
            null,
            null,
            'info'
        );

        console.log('Excel file deleted locally:', fileId);
    }

    // Handle fatal errors
    handleFatalError(error) {
        console.error('Fatal error:', error);

        let message = CONFIG.MESSAGES.FATAL_ERROR;
        if (error.message) {
            message += `\n\nDetails: ${error.message}`;
        }

        window.uiManager.showFatalError(message);
    }

    // Get application state
    getAppState() {
        return {
            portals: this.portals,
            conditions: this.conditions,
            loggedInPortals: this.loggedInPortals,
            excelFiles: this.excelFiles,
            isSearching: this.isSearching,
            isLoggingIn: this.isLoggingIn,
            searchResults: window.uiManager.searchResults,
            notifications: window.uiManager.notifications
        };
    }

    // Reload configuration
    async reloadConfig() {
        try {
            await this.loadConfig();
            await this.loadExcelFiles();
            console.log('Configuration reloaded');
        } catch (error) {
            console.error('Failed to reload configuration:', error);
            this.handleFatalError(error);
        }
    }
}

// Global instances
window.appController = new AppController();
window.uiManager = new UIManager();

// Global state for easy access
window.appState = {
    get portals() {
        return window.appController.portals;
    },
    get conditions() {
        return window.appController.conditions;
    },
    get loggedInPortals() {
        return window.appController.loggedInPortals;
    },
    get excelFiles() {
        return window.appController.excelFiles;
    },
    get isSearching() {
        return window.appController.isSearching;
    },
    get isLoggingIn() {
        return window.appController.isLoggingIn;
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.appController.init();
});

// Global error handlers
window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
    window.appController.handleFatalError(event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    window.appController.handleFatalError(event.reason);
});

// Debug utilities (remove in production)
window.debug = {
    getState: () => window.appController.getAppState(),
    reloadConfig: () => window.appController.reloadConfig(),
    clearNotifications: () => window.uiManager.clearAllNotifications(),
    testSearch: (partNumbers = ['TEST123'], filters = {portal_ids: [1], conditions: [1]}) => {
        // Set test data
        document.getElementById('partNumbersInput').value = partNumbers.join(', ');
        window.uiManager.currentFilters = filters;
        window.appController.performSearch();
    },
    testLogin: () => {
        // Simulate successful login for testing
        window.appController.loggedInPortals = window.appController.portals.map(p => p.id);
        window.uiManager.updatePortalStatuses(window.appController.loggedInPortals);
        console.log('Test login completed');
    }
};