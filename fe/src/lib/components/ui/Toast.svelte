<script lang="ts">
    import { fly } from "svelte/transition";
    import { toast, type ToastData } from "$lib/stores/toast";

    const typeClasses: Record<string, string> = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    }

    const close = (id: number) => {
        toast.remove(id);
    };
</script>

<div class="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
    {#each $toast as item (item.id)}
        <div 
            class="{typeClasses[item.type]} text-white rounded-2xl px-5 py-3 shadow-lg" 
            transition:fly={{ x: 400, duration: 300 }}
        >
            <div class="flex items-center justify-between gap-3">
                <span>{item.message}</span>
                <button onclick={() => close(item.id)} class="ml-2 text-lg hover:opacity-75 transition-opacity">×</button>
            </div>
        </div>
    {/each}
</div>
