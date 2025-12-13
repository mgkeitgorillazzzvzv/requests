<script lang="ts">
	import Button from "$lib/components/controls/Button.svelte";
	import FAB from "$lib/components/ui/FAB.svelte";
	import Dropdown from "$lib/components/controls/Dropdown.svelte";
	import Entry from "$lib/components/controls/Entry.svelte";
	import RequestCard from "$lib/components/ui/RequestCard.svelte";
	import { api, RequestStatus, type RequestOut } from "$lib/api";
	import { showToast } from "$lib/stores/toast";
	import { canCreateRequests } from "$lib/stores/auth";
	import { createPullToRefresh, attachPullToRefresh, PULL_THRESHOLD } from "$lib/utils/pullToRefresh";
	import { onMount } from "svelte";
	import { goto } from "$app/navigation";
	import type { PageData } from "./$types";

	let { data }: { data: PageData } = $props();

	let requests = $state<RequestOut[]>(data.requests ?? []);
	let isLoading = $state(false);
	let isLoadingMore = $state(false);
	let hasMore = $state(data.hasMore ?? true);
	let total = $state(data.total ?? 0);
	let search = $state('');
	let statusFilter = $state<'all' | RequestStatus>(RequestStatus.Created);
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;
	let listContainer: HTMLDivElement | null = $state(null);
	let pullState = $state({ pullProgress: 0, isPulling: false, touchStartY: 0 });

	const LIMIT = 6;

	const statusOptions = [
		{ label: 'Все статусы', value: 'all' },
		{ label: 'Созданo', value: RequestStatus.Created },
		{ label: 'Ожидает подтверждения', value: RequestStatus.PendingApproval },
		{ label: 'Ожидает создания (Аномимные)', value: RequestStatus.PendingCreationApproval },
		{ label: 'Выполнено', value: RequestStatus.Completed },
		{ label: 'Отложено', value: RequestStatus.Postponed }
	];

	const fetchRequests = async (reset: boolean = true) => {
		if (reset) {
			isLoading = true;
			requests = [];
		} else {
			isLoadingMore = true;
		}
		
		try {
			const offset = reset ? 0 : requests.length;
			const result = await api.listRequests({
				status: statusFilter === 'all' ? null : statusFilter,
				search: search.trim() || null,
				offset,
				limit: LIMIT
			});
			
			if (reset) {
				requests = result.items;
			} else {
				requests = [...requests, ...result.items];
			}
			hasMore = result.has_more;
			total = result.total;
		} catch (error) {
			console.error('Failed to load requests:', error);
			showToast('Не удалось загрузить заявки', 'error');
		} finally {
			isLoading = false;
			isLoadingMore = false;
		}
	};

	const loadMore = async () => {
		if (isLoadingMore || !hasMore) return;
		await fetchRequests(false);
	};

	const handleScroll = () => {
		if (isLoadingMore || !hasMore) return;
		
		const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
		if (scrollTop + clientHeight >= scrollHeight - 200) {
			loadMore();
		}
	};

	const handleSearchChange = () => {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			fetchRequests(true);
		}, 300);
	};

	const handleStatusChange = () => {
		fetchRequests(true);
	};

	$effect(() => {
		search;
		handleSearchChange();
	});

	$effect(() => {
		statusFilter;
		handleStatusChange();
	});

	onMount(() => {
		fetchRequests(true);
		window.addEventListener('scroll', handleScroll);
		
		const pullHandlers = createPullToRefresh(pullState, isLoading, () => fetchRequests(true));
		const cleanup = attachPullToRefresh(pullHandlers);
		
		return () => {
			window.removeEventListener('scroll', handleScroll);
			cleanup();
			if (searchTimeout) clearTimeout(searchTimeout);
		};
	});

	function handleCreateRequest() {
		goto('/requests/new');
	}
</script>

<div class="max-w-5xl mx-auto p-4 flex flex-col gap-4">
	{#if pullState.isPulling || pullState.pullProgress > 0}
		<div class="fixed top-0 left-0 right-0 h-1 bg-blue-500 z-50" style="width: {(pullState.pullProgress / PULL_THRESHOLD) * 100}%"></div>
	{/if}
	
	<div class="flex flex-col gap-2">
		<div class="flex justify-between items-start gap-2">
			<div class="flex flex-col gap-1">
				<h1 class="text-3xl font-bold">Заявки</h1>
				<p class="text-gray-600">Просматривайте и фильтруйте заявки по статусу и названию.</p>
			</div>
			{#if $canCreateRequests}
				<!-- header button removed in favor of FAB for a cleaner UI -->
			{/if}
		</div>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
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
		</div>
	</div>

	{#if isLoading && requests.length === 0}
		<div class="text-gray-500">Загрузка заявок...</div>
	{:else if requests.length === 0}
		<div class="text-gray-500">Заявки не найдены.</div>
	{:else}
		<div class="flex flex-col gap-3" bind:this={listContainer}>
			{#each requests as request (request.id)}
				<RequestCard request={request} />
			{/each}
		</div>
		{#if isLoadingMore}
			<div class="text-gray-500 text-center py-4">Загрузка...</div>
		{:else if hasMore}
			<div class="text-gray-400 text-center py-4 text-sm">Прокрутите вниз для загрузки ещё</div>
		{/if}
	{/if}
</div>

{#if $canCreateRequests}
	<FAB onclick={handleCreateRequest} ariaLabel="Создать заявку" title="Создать заявку" text="Создать заявку" />
{/if}
