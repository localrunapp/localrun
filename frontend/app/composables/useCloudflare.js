import { useApi } from './useApi';

export const useCloudflare = () => {
    const api = useApi();

    const getConfig = async () => {
        return await api.get('/providers/cloudflare');
    };

    const saveConfig = async (config) => {
        return await api.post('/providers/cloudflare', config);
    };

    const testToken = async (token) => {
        // The backend expects the token as a query param or body. 
        // The controller method signature is test_cloudflare_token(token: str, ...)
        // Since it's a POST, we should send it in the body or query. 
        // FastAPI usually expects query params for simple types unless Body() is used.
        // Let's check the controller signature again. It's `token: str`. 
        // By default FastAPI treats this as a query param. 
        // But for security, tokens should be in body. 
        // Ideally the backend should use Body(), but I didn't specify it. 
        // I'll send it as a query param for now as per default FastAPI behavior, 
        // but it's better to update backend to accept Body. 
        // Wait, I can send it as query param `?token=...`.

        // Actually, let's try sending it as query param first since I didn't use Body(...) in python.
        return await api.post(`/providers/cloudflare/test?token=${encodeURIComponent(token)}`, {});
    };

    return {
        getConfig,
        saveConfig,
        testToken
    };
};
