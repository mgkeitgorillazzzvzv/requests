<script lang="ts">
	import { onMount } from 'svelte';
	import { api, Building, Department, buildingOptions, type StatsOut } from '$lib/api';
	import { normalizeBuilding } from '$lib/util';
	import Dropdown from '$lib/components/controls/Dropdown.svelte';
	import Button from '$lib/components/controls/Button.svelte';
	import { showToast } from '$lib/stores/toast';
	import { currentUser, isHeadOfDepartment } from '$lib/stores/auth';
	import { createPullToRefresh, attachPullToRefresh, PULL_THRESHOLD } from '$lib/utils/pullToRefresh';

	let selectedBuilding = $state<Building | null>(null);
	let selectedPeriod = $state<'day' | 'week' | 'month'>('month');

	let allStats = $state<StatsOut | null>(null);
	let itStats = $state<StatsOut | null>(null);
	let maintenanceStats = $state<StatsOut | null>(null);
	let loading = $state(false);
	let pullState = $state({ pullProgress: 0, isPulling: false, touchStartY: 0 });

	const statsBuildings = [
		{ value: '', label: 'Все корпуса' },
		...buildingOptions
	];

	const periodOptions = [
		{ value: 'day', label: 'День' },
		{ value: 'week', label: 'Неделя' },
		{ value: 'month', label: 'Месяц' }
	];

	let selectedBuildingStr = $state('');
	let selectedPeriodStr = $state('month');

	$effect(() => {
		// For head of department, automatically use their building
		if ($isHeadOfDepartment && $currentUser?.building && selectedBuildingStr === '') {
			selectedBuildingStr = normalizeBuilding($currentUser.building as string) as string;
		}
		selectedBuilding = selectedBuildingStr === '' ? null : (selectedBuildingStr as Building);
		selectedPeriod = selectedPeriodStr as 'day' | 'week' | 'month';
		loadStats();
	});

	async function loadStats() {
		loading = true;

		try {
			
			allStats = await api.getStats(selectedBuilding, null, selectedPeriod);
			
			
			
			// Load department stats for all users (admin sees by selected building, head sees their building)
			itStats = await api.getStats(selectedBuilding, Department.IT, selectedPeriod);
			maintenanceStats = await api.getStats(
				selectedBuilding,
				Department.Maintenance,
				selectedPeriod
			);
		} catch (e) {
			const errorMsg = e instanceof Error ? e.message : 'Ошибка загрузки статистики';
			console.error('Error loading stats:', e);
			showToast(errorMsg, 'error');
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadStats();
		const pullHandlers = createPullToRefresh(pullState, () => loading, () => loadStats());
		const cleanup = attachPullToRefresh(pullHandlers);

		return () => {
			cleanup();
		};
	});

	function formatHours(hours: number): string {
		if (hours === 0) return 'Нет данных';
		if (hours < 1) {
			const minutes = Math.round(hours * 60);
			return `${minutes} мин`;
		}
		if (hours < 24) {
			return `${hours.toFixed(1)} ч`;
		}
		const days = Math.floor(hours / 24);
		const remainingHours = Math.round(hours % 24);
		return `${days} д ${remainingHours} ч`;
	}

	function formatRatio(ratio: number): string {
		return `${(ratio * 100).toFixed(1)}%`;
	}

</script>

{#snippet statCard(label: string, value: string | number, colorClass: string)}
	<div class="bg-gray-50 rounded-lg p-4">
		<div class="text-sm text-gray-600 font-medium">{label}</div>
		<div class="text-2xl font-bold {colorClass}">{value}</div>
	</div>
{/snippet}

{#snippet statsGrid(stats: StatsOut)}
	<div class="grid grid-cols-2 md:grid-cols-6 gap-3">
		{@render statCard('Всего заявок', stats.total_requests, 'text-blue-600')}
		{@render statCard('Открытые', stats.open_requests, 'text-green-600')}
		{@render statCard('Закрытые', stats.closed_requests, 'text-purple-600')}
		{@render statCard('Соотношение', formatRatio(stats.ratio), 'text-amber-600')}
		{@render statCard('Время исполнения', formatHours(stats.execution_time_hours), 'text-red-600')}
		{@render statCard('Время рассмотрения', formatHours(stats.avg_review_time_hours), 'text-indigo-600')}
	</div>
{/snippet}

<div class="min-h-screen px-4 py-6 md:py-8">
	{#if pullState.isPulling || pullState.pullProgress > 0}
		<div
			class="fixed top-0 left-0 right-0 h-1 bg-blue-500 z-50"
			style="width: {(pullState.pullProgress / PULL_THRESHOLD) * 100}%"
		></div>
	{/if}
	<div class="max-w-5xl mx-auto">
		<div class="mb-6">
			<h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Статистика заявок</h1>
			<p class="text-gray-600">
					Просматривайте метрики по заявкам и их обработке.
			</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-{$isHeadOfDepartment ? '2' : '3'} gap-3 mb-6">
			{#if !$isHeadOfDepartment}
				<Dropdown
					options={statsBuildings}
					bind:value={selectedBuildingStr}
					aria-label="Фильтр по корпусу"
					placeholder="Все корпуса"
				/>
			{/if}
			<Dropdown
				options={periodOptions}
				bind:value={selectedPeriodStr}
				aria-label="Фильтр по периоду"
				placeholder="Месяц"
			/>
			<!-- <Button onclick={loadStats} disabled={loading}>
				{loading ? 'Обновление...' : 'Обновить'}
			</Button> -->
		</div>

		{#if loading && !allStats}
			<div class="text-gray-500 text-center py-12">Загрузка статистики...</div>
		{:else if allStats}
			<div class="space-y-6">
				<!-- Overall Stats Section -->
				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-semibold text-gray-800 mb-4">
						{#if $isHeadOfDepartment}
							Статистика корпуса {$currentUser?.building}
						{:else}
							Общая статистика
						{/if}
					</h2>
					{@render statsGrid(allStats)}
				</div>

				<!-- Department Stats Sections - for all users -->
				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-semibold text-gray-800 mb-4">Отдел IT</h2>
					{#if itStats}
						{@render statsGrid(itStats)}
					{/if}
				</div>

				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-semibold text-gray-800 mb-4">Отдел АХЧ</h2>
					{#if maintenanceStats}
						{@render statsGrid(maintenanceStats)}
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>
