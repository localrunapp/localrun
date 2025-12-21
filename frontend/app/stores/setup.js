import { defineStore } from 'pinia';

export const useSetupStore = defineStore('setupStore', {
    state: () => ({
        isSetupComplete: false,
        systemInfo: null,
        loading: false,
    }),

    actions: {
        async checkSetupStatus() {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/setup/status', {
                    // Add timeout and error handling
                    signal: AbortSignal.timeout(5000), // 5 second timeout
                    headers: {
                        'Accept': 'application/json',
                    }
                });

                if (!response.ok) {
                    // HTTP error (4xx, 5xx) - API is reachable but returned an error
                    return {
                        setup_completed: false,
                        error: 'http_error',
                        message: `HTTP error! status: ${response.status}`
                    };
                }

                const data = await response.json();
                this.isSetupComplete = data.setup_completed || false;
                return data;
            } catch (error) {
                console.error('Error checking setup status:', error);

                // Distinguish between network errors (offline) and other errors
                const isNetworkError =
                    error.name === 'TypeError' ||
                    error.name === 'TimeoutError' ||
                    error.message.includes('fetch') ||
                    error.message.includes('Failed to fetch') ||
                    error.message.includes('NetworkError') ||
                    error.message.includes('timed out');

                return {
                    setup_completed: false,
                    error: isNetworkError ? 'offline' : 'unknown',
                    message: error.message || 'Unable to connect to API server'
                };
            }
        },

        async getSystemInfo() {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/setup/system-info');
                const data = await response.json();
                this.systemInfo = data;
                return data;
            } catch (error) {
                console.error('Error getting system info:', error);
                return null;
            }
        },

        async getAgentInstallScript() {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/setup/agent-install-script');
                const script = await response.text(); // Changed from .json() to .text()
                return script || '';
            } catch (error) {
                console.error('Error getting agent install script:', error);
                return '';
            }
        },

        async verifyInitialPassword(password) {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/setup/verify-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password }),
                });
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error verifying password:', error);
                return { valid: false, message: 'Error verifying password' };
            }
        },

        async completeSetup(setupData) {
            try {
                this.loading = true;
                const config = useRuntimeConfig();
                const response = await fetch('/api/setup/complete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(setupData),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Setup failed');
                }

                const data = await response.json();
                this.isSetupComplete = true;
                return data;
            } catch (error) {
                console.error('Error completing setup:', error);
                throw error;
            } finally {
                this.loading = false;
            }
        },
    },

    persist: {
        paths: ['isSetupComplete']
    }
});
