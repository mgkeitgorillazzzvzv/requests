import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { api, type UserOut, type Role } from '$lib/api';

interface AuthState {
	token: string | null;
	user: UserOut | null;
	isLoading: boolean;
}

const STORAGE_KEY = 'auth_token';

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		token: null,
		user: null,
		isLoading: true
	});

	
	if (browser) {
		const storedToken = localStorage.getItem(STORAGE_KEY);
		if (storedToken) {
			api.setToken(storedToken);
			
			api.getCurrentUser()
				.then(user => {
					update(state => ({
						token: storedToken,
						user,
						isLoading: false
					}));
				})
				.catch(() => {
					
					localStorage.removeItem(STORAGE_KEY);
					api.clearToken();
					update(state => ({
						token: null,
						user: null,
						isLoading: false
					}));
				});
		} else {
			update(state => ({ ...state, isLoading: false }));
		}
	}

	return {
		subscribe,
		login: async (username: string, password: string) => {
			try {
				const tokenData = await api.login({ username, password });
				const user = await api.getCurrentUser();
				
				if (browser) {
					localStorage.setItem(STORAGE_KEY, tokenData.access_token);
				}
				
				set({
					token: tokenData.access_token,
					user,
					isLoading: false
				});
				
				return { success: true };
			} catch (error) {
				return { 
					success: false, 
					error: error instanceof Error ? error.message : 'Ошибка входа' 
				};
			}
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem(STORAGE_KEY);
			}
			api.clearToken();
			set({
				token: null,
				user: null,
				isLoading: false
			});
		},
		refreshUser: async () => {
			try {
				const user = await api.getCurrentUser();
				update(state => ({ ...state, user }));
			} catch (error) {
				
				if (browser) {
					localStorage.removeItem(STORAGE_KEY);
				}
				api.clearToken();
				set({
					token: null,
					user: null,
					isLoading: false
				});
			}
		}
	};
}

export const authStore = createAuthStore();


export const isAuthenticated = derived(
	authStore,
	$auth => !!$auth.token && !!$auth.user
);

export const currentUser = derived(
	authStore,
	$auth => $auth.user
);

export const userRole = derived(
	authStore,
	$auth => $auth.user?.role || null
);

export const isAdmin = derived(
	userRole,
	$role => $role === 'администратор'
);

export const isHeadOfDepartment = derived(
	userRole,
	$role => $role === 'заведующий отделением'
);

export const isSpecialist = derived(
	userRole,
	$role => $role === 'специалист'
);

export const isExecutor = derived(
	userRole,
	$role => $role === 'исполнитель'
);

export const canCreateRequests = derived(
	userRole,
	$role => $role === 'администратор' || $role === 'заведующий отделением' || $role === 'специалист'
);;

export const canCreateUsers = derived(
	userRole,
	$role => $role === 'администратор' || $role === 'заведующий отделением'
);

export const canApproveStatusChanges = derived(
	userRole,
	$role => $role === 'заведующий отделением'
);

export const canRequestStatusChange = derived(
	userRole,
	$role => $role === 'исполнитель'
);
