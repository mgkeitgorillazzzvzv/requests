<script lang="ts">
	import { goto } from '$app/navigation';
	import { getPlatformInfo } from '$lib';
	import { authStore, isAuthenticated } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import Button from '$lib/components/controls/Button.svelte';
	import Entry from '$lib/components/controls/Entry.svelte';
	import { showToast } from '$lib/stores/toast';
	import Modal from '$lib/components/ui/Modal.svelte';
	import { pushNotifications } from '$lib/stores/push';
    import { get } from 'svelte/store';

	import menu26 from '$lib/assets/tutorial/26/menu.jpeg';
	import addtohomescreen26 from '$lib/assets/tutorial/26/addtohomescreen.jpeg';
	import sharemenu26 from '$lib/assets/tutorial/26/sharemenu.jpeg';
	import addressbar26 from '$lib/assets/tutorial/26/addressbar.jpeg';


	import addressbarAndroid from '$lib/assets/tutorial/android/addressbar.png';
	import menuAndroid from '$lib/assets/tutorial/android/menu.png';
	import install1Android from '$lib/assets/tutorial/android/install1.png';
	import install2Android from '$lib/assets/tutorial/android/install2.png';

	import addressbarPre26 from '$lib/assets/tutorial/pre26/addressbar.jpg';
	import shareMenuPre26 from '$lib/assets/tutorial/pre26/sharemenu.jpg';
	import addtohomescreenPre26 from '$lib/assets/tutorial/pre26/addtohomescreen.jpg';

	import notifications from '$lib/assets/tutorial/notifications.jpg';

	let username = $state('');
	let password = $state('');
	let isLoading = $state(false);
    let platformInfo = $state<{ os: string; major: number | null; } | null>(null);
	let pushSupported = $state(false);
	let showTutorial = $state(false);
	let shouldShowTutorialButton = $state(false);

	onMount(() => {
		platformInfo = getPlatformInfo();
		pushSupported = get(pushNotifications).supported;
		showTutorial = (!pushSupported  && platformInfo?.os == 'ios') || platformInfo?.os == 'android';
		shouldShowTutorialButton = showTutorial;
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

		{#if shouldShowTutorialButton}
			<div class="mt-4 pt-4">
				<button
					onclick={() => showTutorial = true}
					class="w-full px-4 py-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
				>
					Показать руководство
				</button>
			</div>
		{/if}
	</div>
</div>

<Modal bind:isOpen={showTutorial} title="Руководство использования">
	<div class="space-y-6 max-h-96 overflow-y-auto">
		{#if platformInfo?.os == 'ios' && (platformInfo?.major ?? 0) <= 18}
			<div class="space-y-4">
				<p class="text-sm text-gray-700">Для использования приложения с уведомлениями выполните следующие шаги:</p>
				{platformInfo.major}
				<div class="space-y-3">
					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">1. Нажмите на кнопку "Поделиться"</p>
						<p class="text-xs text-gray-600 mb-2">Найдите кнопку "Поделиться" внизу экрана Safari, расположенную под адресной строкой.</p>
						<img src={addressbarPre26} alt="Кнопка поделиться в Safari" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">2. Выберите "Добавить на главный экран"</p>
						<p class="text-xs text-gray-600 mb-2">В меню поделиться прокрутите вниз и найдите опцию "Добавить на главный экран".</p>
						<img src={shareMenuPre26} alt="Опция добавить на главный экран" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">3. Настройте ярлык приложения</p>
						<p class="text-xs text-gray-600 mb-2">По желанию измените название ярлыка и нажмите кнопку "Добавить".</p>
						<img src={addtohomescreenPre26} alt="Экран добавления на главный экран" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">4. Откройте приложение и включите уведомления</p>
						<p class="text-xs text-gray-600 mb-2">На главном экране найдите новый ярлык приложения, откройте его, выполните вход и перейдите в настройки для включения уведомлений.</p>
						<img src={notifications} alt="Настройки уведомлений" class="w-full rounded border border-gray-200" />
					</div>
				</div>
			</div>

		{:else if platformInfo?.os == 'ios' && (platformInfo?.major ?? 0) <= 26}
			<div class="space-y-4">
				<p class="text-sm text-gray-700">Для использования приложения с уведомлениями выполните следующие шаги:</p>
				
				<div class="space-y-3">
					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">1. Откройте меню Safari</p>
						<p class="text-xs text-gray-600 mb-2">Нажмите на иконку "..." (три точки) внизу экрана Safari.</p>
						<img src={addressbar26} alt="Иконка меню в Safari" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">2. Выберите "Поделиться"</p>
						<p class="text-xs text-gray-600 mb-2">В появившемся меню найдите и нажмите опцию "Поделиться".</p>
						<img src={menu26} alt="Опция поделиться в меню" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">3. Найдите "Добавить на главный экран"</p>
						<p class="text-xs text-gray-600 mb-2">Прокрутите вниз меню поделиться и выберите "Добавить на главный экран".</p>
						<img src={sharemenu26} alt="Опция добавить на главный экран" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">4. Завершите добавление приложения</p>
						<p class="text-xs text-gray-600 mb-2">По желанию отредактируйте название ярлыка и нажмите "Добавить".</p>
						<img src={addtohomescreen26} alt="Экран добавления на главный экран" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">5. Включите уведомления</p>
						<p class="text-xs text-gray-600 mb-2">Откройте приложение через новый ярлык, выполните вход и включите уведомления в настройках.</p>
						<img src={notifications} alt="Настройки уведомлений" class="w-full rounded border border-gray-200" />
					</div>
				</div>
			</div>

		{:else if platformInfo?.os == 'android'}
			<div class="space-y-4">
				<p class="text-sm text-gray-700">Для использования приложения с уведомлениями выполните следующие шаги:</p>
				
				<div class="space-y-3">
					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">1. Откройте меню браузера</p>
						<p class="text-xs text-gray-600 mb-2">Нажмите на кнопку меню (три точки) в верхнем или нижнем углу экрана Chrome. Рекомендуется использовать браузер Chrome для добавления приложения на главный экран.</p>
						<img src={addressbarAndroid} alt="Кнопка меню в Chrome" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">2. Выберите "Добавить на гл. экран"</p>
						<p class="text-xs text-gray-600 mb-2">В выпадающем меню найдите и нажмите опцию "Добавить на гл. экран".</p>
						<img src={menuAndroid} alt="Опция добавить на главный экран" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">3. Подтвердите установку</p>
						<p class="text-xs text-gray-600 mb-2">В появившемся диалоге нажмите кнопку "Установить".</p>
						<img src={install1Android} alt="Первый экран установки" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">4. Настройте название приложения</p>
						<p class="text-xs text-gray-600 mb-2">При необходимости измените название ярлыка и снова нажмите "Установить".</p>
						<img src={install2Android} alt="Второй экран установки" class="w-full rounded border border-gray-200" />
					</div>

					<div>
						<p class="text-sm font-medium text-gray-900 mb-2">5. Завершите процесс</p>
						<p class="text-xs text-gray-600 mb-2">Вернитесь на главный экран, найдите новый ярлык приложения, откройте его, выполните вход и включите уведомления в настройках.</p>
						<img src={notifications} alt="Настройки уведомлений" class="w-full rounded border border-gray-200" />
					</div>
				</div>
			</div>
		{/if}
	</div>
</Modal>