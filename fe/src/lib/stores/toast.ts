import { writable } from 'svelte/store';

export interface ToastData {
    id: number;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
}

function createToastStore() {
    const { subscribe, update } = writable<ToastData[]>([]);
    let nextId = 0;
    const timers = new Map<number, ReturnType<typeof setTimeout>>();

    return {
        subscribe,
        show: (message: string, type: ToastData['type'] = 'info', duration = 5000) => {
            const id = nextId++;
            update(toasts => [...toasts, { id, message, type, duration }]);
            
            if (duration && duration > 0) {
                const timer = setTimeout(() => {
                    
                    update(toasts => toasts.filter(t => t.id !== id));
                    timers.delete(id);
                }, duration);

                timers.set(id, timer);
            }
            return id;
        },
        remove: (id: number) => {
            
            const timer = timers.get(id);
            if (timer) {
                clearTimeout(timer);
                timers.delete(id);
            }

            update(toasts => toasts.filter(t => t.id !== id));
        },
        success: (message: string, duration?: number) => {
            return toast.show(message, 'success', duration);
        },
        error: (message: string, duration?: number) => {
            return toast.show(message, 'error', duration);
        },
        warning: (message: string, duration?: number) => {
            return toast.show(message, 'warning', duration);
        },
        info: (message: string, duration?: number) => {
            return toast.show(message, 'info', duration);
        }
    };
}

export const toast = createToastStore();


export function showToast(message: string, type: ToastData['type'] = 'info', duration: number = 5000) {
    
    return toast.show(message, type, duration);
}
