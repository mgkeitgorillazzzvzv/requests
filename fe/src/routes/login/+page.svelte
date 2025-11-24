<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore, isAuthenticated } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import Button from '$lib/components/controls/Button.svelte';
	import Entry from '$lib/components/controls/Entry.svelte';
	import { showToast } from '$lib/stores/toast';

	let username = '';
	let password = '';
	let isLoading = false;

	onMount(() => {
		
		const unsubscribe = isAuthenticated.subscribe(value => {
			if (value) {
				goto('/');
			}
		});
		return unsubscribe;
	});

	async function handleLogin() {
		if (!username || !password) {
			showToast('Заполните все поля', 'error');
			return;
		}

		isLoading = true;
		const result = await authStore.login(username, password);
		isLoading = false;

		if (result.success) {
			showToast('Вход выполнен успешно', 'success');
			goto('/');
		} else {
			showToast(result.error || 'Неверный логин или пароль', 'error');
		}
	}
</script>

<div class="flex justify-center items-center min-h-screen ">
	<div class="bg-white rounded-xl shadow-lg p-10 w-full max-w-sm">
		<h1 class="text-2xl md:text-3xl font-bold text-center text-gray-900 mb-2">Вход в систему</h1>

		<form class="flex flex-col gap-5">
			<div class="flex flex-col gap-2">
				<label for="username" class="text-sm font-medium text-gray-700">Имя пользователя</label>
				<Entry
					bind:value={username}
					placeholder="Введите имя пользователя"
					disabled={isLoading}
				/>
			</div>

			<div class="flex flex-col gap-2">
				<label for="password" class="text-sm font-medium text-gray-700">Пароль</label>
				<Entry
					bind:value={password}
					type="password"
					placeholder="Введите пароль"
					disabled={isLoading}
				/>
			</div>

			<div class="mt-2">
				<Button onclick={handleLogin} disabled={isLoading} className="w-full">
					{isLoading ? 'Вход...' : 'Войти'}
				</Button>
			</div>
		</form>
	</div>
</div>
