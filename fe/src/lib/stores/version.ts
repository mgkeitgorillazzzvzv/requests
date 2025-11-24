import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const VERSION_STORAGE_KEY = 'frontend_version';

function createVersionStore() {
	const { subscribe, set } = writable<string | null>(null);

	
	if (browser) {
		const checkVersion = async () => {
			try {
				const response = await fetch(
					`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/version`
				);
				const data = await response.json();
				const newVersion = data.version;
				const storedVersion = localStorage.getItem(VERSION_STORAGE_KEY);

				
				if (!storedVersion || storedVersion !== newVersion) {
					
					if ('serviceWorker' in navigator && 'caches' in window) {
						const cacheNames = await caches.keys();
						await Promise.all(cacheNames.map(name => caches.delete(name)));
					}

					
					const keysToKeep = ['auth_token'];
					const allKeys = Object.keys(localStorage);
					allKeys.forEach(key => {
						if (!keysToKeep.includes(key)) {
							localStorage.removeItem(key);
						}
					});

					
					sessionStorage.clear();
				}

				
				localStorage.setItem(VERSION_STORAGE_KEY, newVersion);
				set(newVersion);
			} catch (error) {
				console.warn('Failed to check version:', error);
				
				const storedVersion = localStorage.getItem(VERSION_STORAGE_KEY) || '1.0.0';
				set(storedVersion);
			}
		};

		checkVersion();
	}

	return {
		subscribe
	};
}

export const versionStore = createVersionStore();
