export const useApi = () => {
    const config = useRuntimeConfig();
    const authStore = useAuthStore();

    // Usar proxy de Vite - rutas relativas
    const baseURL = config.public.apiBaseUrl || '';

    const request = async (endpoint, options = {}) => {
        const token = authStore.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Asegurar que el endpoint empiece con /api/
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        if (!cleanEndpoint.startsWith('/api/')) {
            cleanEndpoint = `/api${cleanEndpoint}`;
        }
        
        const url = `${baseURL}${cleanEndpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    };

    return {
        get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
        post: (endpoint, data, options = {}) => request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data),
        }),
        put: (endpoint, data, options = {}) => request(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data),
        }),
        patch: (endpoint, data, options = {}) => request(endpoint, {
            ...options,
            method: 'PATCH',
            body: JSON.stringify(data),
        }),
        delete: (endpoint, options = {}) => request(endpoint, { ...options, method: 'DELETE' }),
    };
};
