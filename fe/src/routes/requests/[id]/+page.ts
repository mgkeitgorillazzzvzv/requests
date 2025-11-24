import { api } from "$lib/api";
import { error } from "@sveltejs/kit";
import { get } from "svelte/store";
import { authStore } from "$lib/stores/auth";
export const load = async ({ params, depends }) => {
    depends('requests:id');
    try {
        const requestId = parseInt(params.id);
        if (isNaN(requestId)) {
            throw error(400, 'Invalid request ID');
        }
        
        
        let authState = get(authStore);
        if (authState.isLoading) {
            await new Promise<void>(resolve => {
                const unsubscribe = authStore.subscribe(state => {
                    if (!state.isLoading) {
                        unsubscribe();
                        resolve();
                    }
                });
            });
            authState = get(authStore);
        }
        
        const request = await api.getRequest(requestId);
        return { request, user: authState.user };
    } catch (err) {
        console.error('Failed to load request:', err);
        throw error(404, 'Request not found');
    }
};