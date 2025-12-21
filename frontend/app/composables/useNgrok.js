import { useApi } from './useApi';

export const useNgrok = () => {
    const api = useApi();

    const getConfig = async () => {
        return await api.get('/providers/ngrok');
    };

    const saveConfig = async (config) => {
        return await api.post('/providers/ngrok', config);
    };

    return {
        getConfig,
        saveConfig
    };
};
