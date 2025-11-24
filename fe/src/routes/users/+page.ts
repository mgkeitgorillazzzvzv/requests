import { api } from "$lib/api";

export const load = async () => {
    try {
        const users = await api.listUsers();
        return { users };
    } catch (error) {
        console.error('Failed to load users:', error);
        return { users: [] };
    }
};
