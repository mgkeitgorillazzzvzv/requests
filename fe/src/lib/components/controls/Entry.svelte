<script lang="ts">
    import type { HTMLInputAttributes } from "svelte/elements";

    let { value = $bindable(), className = '', ...restProps }: { value?: string, className?: string } & HTMLInputAttributes = $props()
</script>

<input bind:value={value} class="{className} w-full border border-gray-300 rounded-xl px-4 py-3 transition duration-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 placeholder:text-gray-400" {...restProps}/>