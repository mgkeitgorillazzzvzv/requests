import { api } from "$lib/api";
import { error } from "@sveltejs/kit";
import { get } from "svelte/store";
import { authStore } from "$lib/stores/auth";

export const load = async ({ params }) => {
    try {
        const userId = parseInt(params.id);
        if (isNaN(userId)) {
            throw error(400, 'Invalid user ID');
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

        const user = await api.getUser(userId);
        return { user, currentUser: authState.user };
    } catch (err) {
        console.error('Failed to load user:', err);
        throw error(404, 'User not found');
    }
};
