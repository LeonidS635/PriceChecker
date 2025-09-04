// API Client Module
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.activeRequests = new Map(); // Track active requests for cancellation
    }

    // Base HTTP request method
    async request(endpoint, options = {}, requestId = null) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = {...defaultOptions, ...options};

        // Create AbortController for request cancellation
        const controller = new AbortController();
        config.signal = controller.signal;

        // Store controller if requestId provided
        if (requestId) {
            this.activeRequests.set(requestId, controller);
        }

        try {
            const response = await fetch(url, config);

            // Remove from active requests
            if (requestId) {
                this.activeRequests.delete(requestId);
            }

            // Check response status
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;

                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (e) {
                    // If can't parse JSON error, use default message
                }

                throw new APIError(errorMessage, response.status);
            }

            // For streaming responses return the response itself
            if (options.stream) {
                return response;
            }

            // For file downloads return the response
            if (options.download) {
                return response;
            }

            return await response.json();
        } catch (error) {
            // Remove from active requests
            if (requestId) {
                this.activeRequests.delete(requestId);
            }

            if (error.name === 'AbortError') {
                throw new APIError('Request cancelled', 0);
            }

            if (error instanceof APIError) {
                throw error;
            }

            // Network or other errors
            throw new APIError(CONFIG.MESSAGES.SERVER_UNAVAILABLE, 0);
        }
    }

    // Cancel active request
    cancelRequest(requestId) {
        const controller = this.activeRequests.get(requestId);
        if (controller) {
            controller.abort();
            this.activeRequests.delete(requestId);
        }
    }

    // Get configuration (portals and conditions)
    async getConfig() {
        return this.request(CONFIG.ENDPOINTS.CONFIG);
    }

    // Login to portals
    async login(credentials) {
        return this.request(CONFIG.ENDPOINTS.LOGIN, {
            method: 'POST',
            body: JSON.stringify(credentials)
        }, 'login');
    }

    // Cancel login request
    cancelLogin() {
        this.cancelRequest('login');
    }

    // Search for parts (streaming response)
    async search(partNumbers, filters) {
        return this.request(CONFIG.ENDPOINTS.SEARCH, {
            method: 'POST',
            body: JSON.stringify({
                part_numbers: partNumbers,
                filters: filters
            }),
            stream: true
        }, 'search');
    }

    // Cancel search request
    cancelSearch() {
        this.cancelRequest('search');
    }

    // Form quotation
    async formQuotation(quotationData) {
        return this.request(CONFIG.ENDPOINTS.QUOTATION, {
            method: 'POST',
            body: JSON.stringify(quotationData),
            download: true
        });
    }

    // Get Excel files list
    async getExcelFiles() {
        return this.request(CONFIG.ENDPOINTS.EXCEL);
    }

    // Upload Excel file
    async uploadExcelFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request(CONFIG.ENDPOINTS.EXCEL, {
            method: 'POST',
            body: formData,
            headers: {} // Remove Content-Type to let browser set it with boundary
        });
    }
}

// API Error class
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.isFatal = status === 0; // 0 status means network issues
    }
}

// Streaming response handler
class StreamingResponseHandler {
    constructor(onResult, onError, onComplete, onProgress) {
        this.onResult = onResult;
        this.onError = onError;
        this.onComplete = onComplete;
        this.onProgress = onProgress;
        this.processedCount = 0;
    }

    async handleResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const {done, value} = await reader.read();

                if (done) {
                    this.onComplete?.();
                    break;
                }

                const chunk = decoder.decode(value, {stream: true});
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);

                            this.processedCount++;
                            this.onProgress?.(this.processedCount);

                            // Check if this is an error from server
                            for (const searchRes of data) {
                                if (searchRes.success === false) {
                                    this.onError?.(searchRes.error, searchRes.portal_id, searchRes.requested_part_number);
                                } else if (searchRes.success === true) {
                                    if (searchRes.offers && searchRes.offers.length > 0) {
                                        // Process offers
                                        searchRes.offers.forEach(offer => {
                                            this.onResult?.({
                                                ...offer,
                                                portal_id: searchRes.portal_id,
                                                requested_part_number: searchRes.requested_part_number
                                            });
                                        });
                                    } else {
                                        // No offers found - show info message
                                        this.onError?.(
                                            `${CONFIG.MESSAGES.PART_NOT_FOUND}: ${searchRes.requested_part_number}`,
                                            searchRes.portal_id,
                                            searchRes.requested_part_number,
                                            'info'
                                        );
                                    }
                                }
                            }
                        } catch (e) {
                            console.warn('Failed to parse JSON:', line);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Search cancelled by user');
            } else {
                console.error('Error reading streaming response:', error);
                this.onError?.(error.message);
            }
        }
    }
}

// Global API client instance
const apiClient = new APIClient(CONFIG.API_BASE_URL);