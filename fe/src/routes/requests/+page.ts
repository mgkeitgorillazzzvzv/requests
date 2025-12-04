import { api, RequestStatus } from "$lib/api";

export const load = async () => {
    try {
        const result = await api.listRequests({
            status: RequestStatus.Created,
            offset: 0,
            limit: 6
        });
        return { 
            requests: result.items,
            total: result.total,
            hasMore: result.has_more
        };
    } catch (error) {
        console.error('Failed to load requests:', error);
        return { requests: [], total: 0, hasMore: false };
    }
};
