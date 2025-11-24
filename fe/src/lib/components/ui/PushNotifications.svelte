<script lang="ts">
	import { pushNotifications } from '$lib/stores/push';
	import Button from '$lib/components/controls/Button.svelte';
    import { toast } from '$lib/stores/toast';

	let state: any;
	pushNotifications.subscribe(value => {
		state = value;
	});

	async function handleSubscribe() {
		try {
			await pushNotifications.subscribeToPush();
		} catch (error) {
			console.error('Failed to subscribe:', error);
			toast.error('Не удалось подписаться на уведомления. Проверьте разрешения браузера.');
		}
	}

	async function handleUnsubscribe() {
		try {
			await pushNotifications.unsubscribeFromPush();
		} catch (error) {
			console.error('Failed to unsubscribe:', error);
			toast.error('Не удалось отписаться от уведомлений.');
		}
	}
</script>

<div class="w-full bg-gray-50 border border-gray-200 rounded-lg p-4">
	{#if !state?.supported}
		<p class="text-sm text-gray-600">Уведомления недоступны. На iOS нажмите "Поделиться" и добавьте сайт на экран "Домой" для получения уведомлений.</p>
	{:else if state?.permission === 'denied'}
		<p class="text-sm font-medium text-yellow-600">Уведомления заблокированы. Разрешите уведомления в настройках браузера.</p>
	{:else if state?.subscribed}
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
			<p class="text-sm font-medium text-green-600">✓ Уведомления включены</p>
			<Button className="w-full sm:w-auto" onclick={handleUnsubscribe} disabled={state?.loading}>
				{state?.loading ? 'Загрузка...' : 'Выключить'}
			</Button>
		</div>
	{:else}
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
			<p class="text-sm text-gray-600">Включите уведомления, чтобы получать информацию о новых заявках</p>
			<Button className="w-full sm:w-auto" onclick={handleSubscribe} disabled={state?.loading}>
				{state?.loading ? 'Загрузка...' : 'Включить'}
			</Button>
		</div>
	{/if}
</div>

<!-- Styling migrated to Tailwind classes; original local CSS removed -->
