<script lang="ts">
	import { page } from '$app/stores';
	import { isAdmin, isHeadOfDepartment } from '$lib/stores/auth';
	import RequestIcon from '$lib/assets/request.svg';
	import UsersIcon from '$lib/assets/users.svg';
	import SettingsIcon from '$lib/assets/settings.svg';
	import StatsIcon from '$lib/assets/stats.svg';

	interface Tab {
		name: string;
		path: string;
		icon: string;
		requiresAdmin?: boolean;
		requiresAdminOrHead?: boolean;
	}

	const tabs: Tab[] = [
		{ name: 'Заявки', path: '/requests', icon: RequestIcon },
		{ name: 'Пользователи', path: '/users', icon: UsersIcon, requiresAdmin: true },
		{ name: 'Статистика', path: '/stats', icon: StatsIcon, requiresAdminOrHead: true },
		{ name: 'Настройки', path: '/settings', icon: SettingsIcon },
	];

	$: visibleTabs = tabs.filter(tab => {
		if (tab.requiresAdmin) return $isAdmin;
		if (tab.requiresAdminOrHead) return $isAdmin || $isHeadOfDepartment;
		return true;
	});
	$: isActive = (path: string): boolean => {
		return $page.url.pathname === path || $page.url.pathname.startsWith(path + '/');
	};
</script>

<nav class="fixed bottom-0 left-0 right-0 flex bg-white border-t border-gray-200 shadow-lg z-50">
	{#each visibleTabs as tab}
		<a 
			href={tab.path} 
			class="flex-1 flex flex-col items-center justify-center py-3 px-2 transition-colors relative"
			class:text-indigo-600={isActive(tab.path)}
			class:text-gray-600={!isActive(tab.path)}
			class:hover:bg-gray-50={!isActive(tab.path)}
		>
			{#if isActive(tab.path)}
				<div class="absolute top-0 left-0 right-0 h-1 bg-indigo-600 rounded-b"></div>
			{/if}
			<img src={tab.icon} alt={tab.name} class="w-6 h-6" class:brightness-0={!isActive(tab.path)} />
			<span class="text-xs font-medium mt-1 whitespace-nowrap">{tab.name}</span>
		</a>
	{/each}
</nav>

<style>
	nav {
		padding-bottom: env(safe-area-inset-bottom);
	}

	@media (max-width: 480px) {
		span {
			font-size: 0.65rem;
		}
	}
</style>
