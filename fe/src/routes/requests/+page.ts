import { api } from "$lib/api";

export const load = async () => {
    try {
        const requests = await api.listRequests();
        return { requests };
    } catch (error) {
        console.error('Failed to load requests:', error);
        return { requests: [] };
    }
};
