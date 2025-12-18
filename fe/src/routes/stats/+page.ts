import { redirect } from "@sveltejs/kit";
import { authStore } from "$lib/stores/auth";
import { get } from "svelte/store";

export const load = async () => {
    const auth = get(authStore);
    
    // Prevent API requests if not authenticated
    if (!auth.token || !auth.user) {
        throw redirect(302, '/login');
    }
    
    // Stats page will load data on the client side based on selections
    return {};
};
