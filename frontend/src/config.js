// Application Configuration
const CONFIG = {
    // API Server URL
    API_BASE_URL: 'http://localhost:8081',

    // API Endpoints
    ENDPOINTS: {
        CONFIG: '/config',
        LOGIN: '/login',
        SEARCH: '/search',
        QUOTATION: '/quotation',
        EXCEL: '/excel'
    },

    // UI Settings
    UI: {
        // Notification timeout (ms)
        NOTIFICATION_TIMEOUT: 5000,

        // Maximum cell text length before truncation
        MAX_CELL_LENGTH: 200,

        // Search debounce delay (ms)
        SEARCH_DEBOUNCE: 300,

        // Maximum notifications to show
        MAX_NOTIFICATIONS: 100
    },

    // Notification types
    NOTIFICATION_TYPES: {
        ERROR: 'error',
        WARNING: 'warning',
        INFO: 'info'
    },

    // User Messages
    MESSAGES: {
        LOADING_CONFIG: 'Loading configuration...',
        CONFIG_ERROR: 'Failed to load configuration',
        LOGIN_SUCCESS: 'Login successful',
        LOGIN_ERROR: 'Login failed',
        LOGIN_PROCESSING: 'Processing login...',
        SEARCH_STARTING: 'Starting search...',
        SEARCH_COMPLETE: 'Search completed',
        SEARCH_CANCELLED: 'Search cancelled',
        SEARCH_ERROR: 'Search failed',
        QUOTATION_SUCCESS: 'Quotation formed successfully',
        QUOTATION_ERROR: 'Failed to form quotation',
        EXCEL_UPLOAD_SUCCESS: 'Excel file uploaded successfully',
        EXCEL_UPLOAD_ERROR: 'Failed to upload Excel file',
        EXCEL_DELETE_SUCCESS: 'Excel file deleted successfully',
        FATAL_ERROR: 'A critical error occurred. Please reload the application.',
        NO_PORTALS_SELECTED: 'Please select at least one portal',
        NO_LOGGED_IN_PORTALS: 'Please login to at least one portal before searching',
        NO_PART_NUMBERS: 'Please enter part numbers to search',
        NO_ROWS_SELECTED: 'Please select items to form quotation',
        NO_QUOTATION_NUMBER: 'Please enter a quotation number',
        SERVER_UNAVAILABLE: 'Server is unavailable',
        PART_NOT_FOUND: 'Part not found'
    },

    // Table columns configuration
    TABLE_COLUMNS: [
        {key: 'portal', title: 'Portal', sortable: true},
        {key: 'part_number', title: 'Part Number', sortable: true},
        {key: 'description', title: 'Description', sortable: false},
        {key: 'condition', title: 'Condition', sortable: true},
        {key: 'price', title: 'Price', sortable: true},
        {key: 'qty', title: 'QTY', sortable: true},
        {key: 'lead_time', title: 'Lead Time', sortable: false},
        {key: 'warehouse', title: 'Warehouse', sortable: false},
        {key: 'interchangeable', title: 'Interchangeable', sortable: false},
        {key: 'other_information', title: 'Other Information', sortable: false}
    ]
};