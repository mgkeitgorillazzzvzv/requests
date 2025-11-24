<script lang="ts">
	import { authStore, currentUser } from '$lib/stores/auth';
	import { versionStore } from '$lib/stores/version';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/controls/Button.svelte';
	import PushNotifications from '$lib/components/ui/PushNotifications.svelte';
	import { showToast } from '$lib/stores/toast';
	import { Role } from '$lib';
	import { capitalizeFirstLetter, getFullName } from '$lib/util';
	function handleLogout() {
		authStore.logout();
		showToast('Вы вышли из системы', 'success');
		goto('/login');
	}
	
</script>

<div class="min-h-screen  px-4 py-6 md:py-8">
	<div class="max-w-3xl mx-auto">
		<h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-6">Настройки</h1>

		<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Информация о пользователе</h2>
			{#if $currentUser}
				<div class="space-y-3">
				<div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
					<span class="font-medium text-gray-600">Имя:</span>
					<span class="font-semibold text-gray-900">{getFullName($currentUser)}</span>
				</div>
					<div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
						<span class="font-medium text-gray-600">Логин:</span>
						<span class="font-semibold text-gray-900">{$currentUser.username}</span>
					</div>
					<div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
						<span class="font-medium text-gray-600">Роль:</span>
						<span class="font-semibold text-gray-900">{capitalizeFirstLetter($currentUser.role)}</span>
					</div>
					{#if $currentUser.building}
						<div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
							<span class="font-medium text-gray-600">Корпус:</span>
							<span class="font-semibold text-gray-900">{$currentUser.building}</span>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Информация о системе</h2>
			<div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
				<span class="font-medium text-gray-600">Версия:</span>
				<span class="font-semibold text-gray-900">{$versionStore || 'Загрузка...'}</span>
			</div>
		</div>

		<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Уведомления</h2>
			<PushNotifications />
		</div>
		<div class="bg-white rounded-lg shadow-sm p-6">
			<h2 class="text-xl font-semibold text-gray-800 mb-4">Действия</h2>
			<div class="flex flex-col gap-3">
				<Button onclick={handleLogout} variant="danger" className="w-full">
					Выйти из аккаунта
				</Button>
			</div>
		</div>
	</div>
</div>

