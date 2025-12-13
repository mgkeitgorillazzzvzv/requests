<script lang="ts">
    export let ariaLabel: string = 'Create';
    export let title: string = '';
    export let text: string = '';
    export let href: string | null = null;
    export let disabled: boolean = false;
    export let variant: 'primary' | 'danger' | 'secondary' = 'primary';
    export let onclick: ((e: MouseEvent) => void) | null = null;

    const base = 'fixed z-50 bottom-28 left-1/2 -translate-x-1/2';

    const variantClasses = {
        primary: 'bg-[#1357ff] hover:bg-[#0f49d6] text-white',
        danger: 'bg-red-600 hover:bg-red-700 text-white',
        secondary: 'bg-gray-500 hover:bg-gray-600 text-white'
    } as Record<string, string>;

    function handleClick(e: MouseEvent) {
        if (disabled) return;
        onclick?.(e);
    }
</script>

<style>
    .fab-shadow { box-shadow: 0 8px 24px rgba(8, 17, 51, 0.12); }
</style>

{#if href}
    <a
        href={href}
        class="{base} focus:outline-none"
        aria-label={ariaLabel}
        title={title || ariaLabel}
    >
        <button
            class="{variantClasses[variant]} fab-shadow rounded-full px-4 h-14 flex items-center justify-center gap-2 transition-colors active:scale-95"
            aria-hidden="true"
            onclick={handleClick}
            disabled={disabled}
        >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="pointer-events-none shrink-0">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            {#if text}<span class="text-sm font-medium whitespace-nowrap">{text}</span>{/if}
        </button>
    </a>
{:else}
    <div class={base}>
        <button
            class="{variantClasses[variant]} fab-shadow rounded-full px-4 h-14 flex items-center justify-center gap-2 transition-colors active:scale-95 focus:outline-none"
            aria-label={ariaLabel}
            title={title || ariaLabel}
            {disabled}
            onclick={handleClick}
        >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="pointer-events-none shrink-0">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            {#if text}<span class="text-sm font-medium whitespace-nowrap">{text}</span>{/if}
        </button>
    </div>
{/if}
