<script lang="ts">
	import { onMount } from 'svelte';
	import { api, Building, Department, type StatsOut } from '$lib/api';
	import Dropdown from '$lib/components/controls/Dropdown.svelte';
	import Button from '$lib/components/controls/Button.svelte';
	import { showToast } from '$lib/stores/toast';
	import { currentUser, isHeadOfDepartment } from '$lib/stores/auth';

	let selectedBuilding = $state<Building | null>(null);
	let selectedPeriod = $state<'day' | 'week' | 'month'>('month');

	let allStats = $state<StatsOut | null>(null);
	let itStats = $state<StatsOut | null>(null);
	let maintenanceStats = $state<StatsOut | null>(null);
	let loading = $state(false);

	const buildingOptions = [
		{ value: '', label: 'Все корпуса' },
		{ value: Building.Millionschikova, label: Building.Millionschikova },
		{ value: Building.Kolomenskaya, label: Building.Kolomenskaya },
		{ value: Building.Sudostroitelnaya, label: Building.Sudostroitelnaya },
		{ value: Building.Kharkovskiy, label: Building.Kharkovskiy }
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
			selectedBuildingStr = $currentUser.building as string;
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

	function StatCard({ label, value }: { label: string; value: string | number }) {
		return `<div class="bg-gray-50 rounded-lg p-4">
			<div class="text-sm text-gray-600 font-medium">${label}</div>
			<div class="text-2xl font-bold text-blue-600">${value}</div>
		</div>`;
	}
</script>

<div class="min-h-screen px-4 py-6 md:py-8">
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
					options={buildingOptions}
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
			<Button onclick={loadStats} disabled={loading}>
				{loading ? 'Обновление...' : 'Обновить'}
			</Button>
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
					<div class="grid grid-cols-2 md:grid-cols-5 gap-3">
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Всего заявок</div>
							<div class="text-2xl font-bold text-blue-600">{allStats.total_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Открытые</div>
							<div class="text-2xl font-bold text-green-600">{allStats.open_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Закрытые</div>
							<div class="text-2xl font-bold text-purple-600">{allStats.closed_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Соотношение</div>
							<div class="text-2xl font-bold text-amber-600">{formatRatio(allStats.ratio)}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Среднее время</div>
							<div class="text-2xl font-bold text-red-600">
								{formatHours(allStats.avg_processing_time_hours)}
							</div>
						</div>
					</div>
				</div>

				<!-- Department Stats Sections - for all users -->
				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-semibold text-gray-800 mb-4">Отдел IT</h2>
					<div class="grid grid-cols-2 md:grid-cols-5 gap-3">
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Всего заявок</div>
							<div class="text-2xl font-bold text-blue-600">{itStats?.total_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Открытые</div>
							<div class="text-2xl font-bold text-green-600">{itStats?.open_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Закрытые</div>
							<div class="text-2xl font-bold text-purple-600">{itStats?.closed_requests}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Соотношение</div>
							<div class="text-2xl font-bold text-amber-600">{formatRatio(itStats?.ratio || 0)}</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Среднее время</div>
							<div class="text-2xl font-bold text-red-600">
								{formatHours(itStats?.avg_processing_time_hours || 0)}
							</div>
						</div>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm p-6">
					<h2 class="text-xl font-semibold text-gray-800 mb-4">Отдел АХЧ</h2>
					<div class="grid grid-cols-2 md:grid-cols-5 gap-3">
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Всего заявок</div>
							<div class="text-2xl font-bold text-blue-600">
								{maintenanceStats?.total_requests}
							</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Открытые</div>
							<div class="text-2xl font-bold text-green-600">
								{maintenanceStats?.open_requests}
							</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Закрытые</div>
							<div class="text-2xl font-bold text-purple-600">
								{maintenanceStats?.closed_requests}
							</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Соотношение</div>
							<div class="text-2xl font-bold text-amber-600">
								{formatRatio(maintenanceStats?.ratio || 0)}
							</div>
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<div class="text-sm text-gray-600 font-medium">Среднее время</div>
							<div class="text-2xl font-bold text-red-600">
								{formatHours(maintenanceStats?.avg_processing_time_hours || 0)}
							</div>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
