import { api, RequestStatus } from "$lib/api";
import { redirect } from "@sveltejs/kit";
import { authStore } from "$lib/stores/auth";
import { get } from "svelte/store";

export const load = async () => {
    const auth = get(authStore);
    
    // Prevent API requests if not authenticated
    if (!auth.token || !auth.user) {
        throw redirect(302, '/login');
    }
    
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
