import { writable } from 'svelte/store';
import { api } from '$lib/api';

export interface PushNotificationState {
	supported: boolean;
	permission: NotificationPermission;
	subscribed: boolean;
	loading: boolean;
}

const initialState: PushNotificationState = {
	supported: false,
	permission: 'default',
	subscribed: false,
	loading: false
};

function createPushStore() {
	const { subscribe: svelteSubscribe, set, update } = writable<PushNotificationState>(initialState);

	let registration: ServiceWorkerRegistration | null = null;

	
	const checkSupport = () => {
		const supported = 'serviceWorker' in navigator && 'PushManager' in window;
		update(state => ({ ...state, supported }));
		return supported;
	};

	
	const registerServiceWorker = async () => {
		if (!('serviceWorker' in navigator)) {
			return null;
		}

		try {
			registration = await navigator.serviceWorker.register('/service-worker.js');
			await navigator.serviceWorker.ready;
			return registration;
		} catch (error) {
			console.error('Service worker registration failed:', error);
			return null;
		}
	};

	
	const requestPermission = async (): Promise<NotificationPermission> => {
		if (!('Notification' in window)) {
			return 'denied';
		}

		const permission = await Notification.requestPermission();
		update(state => ({ ...state, permission }));
		return permission;
	};

	
	const subscribeToPush = async () => {
		update(state => ({ ...state, loading: true }));

		try {
			
			if (!checkSupport()) {
				throw new Error('Push notifications not supported');
			}

			
			if (!registration) {
				registration = await registerServiceWorker();
			}

			if (!registration) {
				throw new Error('Service worker registration failed');
			}

			
			const permission = await requestPermission();
			if (permission !== 'granted') {
				throw new Error('Notification permission denied');
			}

			
			const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY || 
				'BEl62iUYgUivxIkv69yViEuiBIa-Ib37J8xQmrysf3zKVzj4SDN5P4KWcXZ1Xzj1xN8TA0d5MZOuXwfR-Xe14pM';

			
			const subscription = await registration.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as BufferSource
			});

			
			const subscriptionData = subscription.toJSON();
			
			const headers: Record<string, string> = {
				'Content-Type': 'application/json',
			};
			
			if ((api as any).token) {
				headers['Authorization'] = `Bearer ${(api as any).token}`;
			}
			
			const response = await fetch(`${(api as any).baseURL || 'http://localhost:8000'}/notifications/subscribe`, {
				method: 'POST',
				headers,
				body: JSON.stringify({
					endpoint: subscriptionData.endpoint,
					keys: subscriptionData.keys
				})
			});
			
			if (!response.ok) {
				throw new Error('Failed to send subscription to backend');
			}

			update(state => ({ ...state, subscribed: true, loading: false }));
		} catch (error) {
			console.error('Push subscription failed:', error);
			update(state => ({ ...state, loading: false }));
			throw error;
		}
	};

	
	const unsubscribeFromPush = async () => {
		update(state => ({ ...state, loading: true }));

		try {
			if (!registration) {
				throw new Error('No service worker registration');
			}

			const subscription = await registration.pushManager.getSubscription();
			if (!subscription) {
				throw new Error('No push subscription found');
			}

			
			await subscription.unsubscribe();

			
			const subscriptionData = subscription.toJSON();
			
			const headers: Record<string, string> = {
				'Content-Type': 'application/json',
			};
			
			if ((api as any).token) {
				headers['Authorization'] = `Bearer ${(api as any).token}`;
			}
			
			const response = await fetch(`${(api as any).baseURL || 'http://localhost:8000'}/notifications/unsubscribe`, {
				method: 'POST',
				headers,
				body: JSON.stringify({
					endpoint: subscriptionData.endpoint,
					keys: subscriptionData.keys
				})
			});
			
			if (!response.ok) {
				throw new Error('Failed to remove subscription from backend');
			}

			update(state => ({ ...state, subscribed: false, loading: false }));
		} catch (error) {
			console.error('Push unsubscribe failed:', error);
			update(state => ({ ...state, loading: false }));
			throw error;
		}
	};

	
	const checkSubscription = async () => {
		if (!checkSupport()) {
			return;
		}

		try {
			if (!registration) {
				registration = await registerServiceWorker();
			}

			if (registration) {
				const subscription = await registration.pushManager.getSubscription();
				const permission = Notification.permission;
				
				update(state => ({
					...state,
					subscribed: !!subscription,
					permission
				}));
			}
		} catch (error) {
			console.error('Failed to check subscription:', error);
		}
	};

	
	checkSupport();
	checkSubscription();

	return {
		subscribe: svelteSubscribe,
		subscribeToPush,
		unsubscribeFromPush,
		checkSubscription,
		requestPermission
	};
}


function urlBase64ToUint8Array(base64String: string): Uint8Array {
	const padding = '='.repeat((4 - base64String.length % 4) % 4);
	const base64 = (base64String + padding)
		.replace(/-/g, '+')
		.replace(/_/g, '/');

	const rawData = atob(base64);
	const outputArray = new Uint8Array(rawData.length);

	for (let i = 0; i < rawData.length; ++i) {
		outputArray[i] = rawData.charCodeAt(i);
	}
	return outputArray;
}

export const pushNotifications = createPushStore();
