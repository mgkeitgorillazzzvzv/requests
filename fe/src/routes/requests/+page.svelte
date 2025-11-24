<script lang="ts">
	import Button from "$lib/components/controls/Button.svelte";
	import Dropdown from "$lib/components/controls/Dropdown.svelte";
	import Entry from "$lib/components/controls/Entry.svelte";
	import RequestCard from "$lib/components/ui/RequestCard.svelte";
	import { api, RequestStatus, type RequestOut } from "$lib/api";
	import { showToast } from "$lib/stores/toast";
	import { canCreateRequests } from "$lib/stores/auth";
	import { onMount } from "svelte";
	import { goto } from "$app/navigation";
	import type { PageData } from "./$types";

	let { data }: { data: PageData } = $props();

	let requests = $state<RequestOut[]>(data.requests ?? []);
	let isLoading = $state(false);
	let search = $state('');
	let statusFilter = $state<'all' | RequestStatus>(RequestStatus.Created); 

	const statusOptions = [
		{ label: 'Все статусы', value: 'all' },
		{ label: 'Созданo', value: RequestStatus.Created },
		{ label: 'Ожидает подтверждения', value: RequestStatus.PendingApproval },
		{ label: 'Выполнено', value: RequestStatus.Completed },
		{ label: 'Отложено', value: RequestStatus.Postponed }
	];

	const filteredRequests = $derived.by(() => {
		const term = search.trim().toLowerCase();
		let filtered = requests.filter((request) => {
			const matchesStatus =
				statusFilter === 'all' || request.status === statusFilter;
			const matchesSearch = term
				? [
					  request.title,
					  request.description ?? '',
					  request.opened_by.first_name,
					  request.opened_by.last_name,
					  request.building,
					  request.department ?? ''
				  ].some((field) => field.toLowerCase().includes(term))
				: true;
			return matchesStatus && matchesSearch;
		});

		
		filtered.sort((a, b) => {
			if (a.urgent && !b.urgent) return -1;
			if (!a.urgent && b.urgent) return 1;
			
			return new Date(b.opened_at).getTime() - new Date(a.opened_at).getTime();
		});

		return filtered;
	});

	const fetchRequests = async () => {
		isLoading = true;
		try {
			requests = await api.listRequests();
		} catch (error) {
			console.error('Failed to load requests:', error);
			showToast('Не удалось загрузить заявки', 'error');
		} finally {
			isLoading = false;
		}
	};

	onMount(() => {
		fetchRequests();
	});

	function handleCreateRequest() {
		goto('/requests/new');
	}
</script>

<div class="max-w-5xl mx-auto p-4 flex flex-col gap-4">
	<div class="flex flex-col gap-2">
		<div class="flex justify-between items-start gap-2">
			<div class="flex flex-col gap-1">
				<h1 class="text-3xl font-bold">Заявки</h1>
				<p class="text-gray-600">Просматривайте и фильтруйте заявки по статусу и названию.</p>
			</div>
			{#if $canCreateRequests}
				<Button onclick={handleCreateRequest}>
					Создать
				</Button>
			{/if}
		</div>
		<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
			<Entry
				bind:value={search}
				placeholder="Поиск по заявкам"
				aria-label="Поиск по заявкам"
			/>
			<Dropdown
				bind:value={statusFilter}
				options={statusOptions}
				aria-label="Фильтр по статусу"
				placeholder="Все статусы"
			/>
			<Button onclick={fetchRequests} disabled={isLoading}>
				{isLoading ? 'Обновление...' : 'Обновить список'}
			</Button>
		</div>
	</div>

	{#if isLoading && requests.length === 0}
		<div class="text-gray-500">Загрузка заявок...</div>
	{:else if filteredRequests.length === 0}
		<div class="text-gray-500">Заявки не найдены.</div>
	{:else}
		<div class="flex flex-col gap-3">
			{#each filteredRequests as request (request.id)}
				<RequestCard request={request} />
			{/each}
		</div>
	{/if}
</div>
