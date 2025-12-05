<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Toast from '$lib/components/ui/Toast.svelte';
	import ViewSwitcher from '$lib/components/ui/ViewSwitcher.svelte';
	import { authStore, isAuthenticated } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	
	let { children } = $props();

	onMount(() => {
		const unsubscribe = page.subscribe($page => {
			const currentPath = $page.url.pathname;
			
			// Список публичных страниц, не требующих авторизации
			const publicPaths = ['/', '/login'];
			const isPublicPath = publicPaths.includes(currentPath);
			
			if (!$authStore.isLoading) {
				// Если пользователь не авторизован и пытается попасть на защищенную страницу
				if (!$isAuthenticated && !isPublicPath) {
					goto('/login');
				}
				// Если пользователь авторизован и находится на странице логина, перенаправляем на заявки
				else if ($isAuthenticated && currentPath === '/login') {
					goto('/requests');
				}
				// Если пользователь авторизован и на главной странице, перенаправляем на заявки
				else if ($isAuthenticated && currentPath === '/') {
					goto('/requests');
				}
			}
		});

		return unsubscribe;
	});

	let showNavigation = $derived($isAuthenticated && $page.url.pathname !== '/login' && $page.url.pathname !== '/');
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if $authStore.isLoading}
	<div class="loading-screen">
		<div class="spinner"></div>
	</div>
{:else}
	<div class="app-container" class:with-navigation={showNavigation}>
		{@render children()}
	</div>
	
	{#if showNavigation}
		<ViewSwitcher />
	{/if}
{/if}

<Toast />

<style>
	.loading-screen {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 100vh;
		background: #f5f5f5;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.app-container {
		min-height: 100vh;
	}

	.app-container.with-navigation {
		padding-bottom: calc(4rem + env(safe-area-inset-bottom));
	}
</style>
