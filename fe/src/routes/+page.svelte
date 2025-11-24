<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/requests');
	});
</script>

<div class="flex items-center justify-center min-h-screen">
	<div class="text-gray-500">Загрузка...</div>
</div>

