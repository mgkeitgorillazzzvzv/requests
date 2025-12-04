<script lang="ts">
    interface Props {
        isOpen: boolean;
        title: string;
        message?: string;
        confirmText?: string;
        cancelText?: string;
        onConfirm?: () => void;
        onCancel?: () => void;
        isDangerous?: boolean;
        children?: () => any;
    }

    let {
        isOpen = $bindable(),
        title,
        message,
        confirmText = 'Подтвердить',
        cancelText = 'Отмена',
        onConfirm,
        onCancel,
        isDangerous = false,
        children
    }: Props = $props();

    const handleConfirm = () => {
        onConfirm?.();
        isOpen = false;
    };

    const handleCancel = () => {
        onCancel?.();
        isOpen = false;
    };

    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
            handleCancel();
        }
    };
</script>

{#if isOpen}
    <div 
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in duration-200"
        role="presentation"
        onkeydown={handleKeyDown}
        onclick={() => handleCancel()}
    >
        <div 
            class="bg-white rounded-lg shadow-lg p-6 max-w-sm w-full mx-4 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            tabindex="0"
            onkeydown={handleKeyDown}
            onclick={(e) => e.stopPropagation()}
        >
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">{title}</h2>
                {#if !onCancel && !onConfirm}
                    <button
                        onclick={handleCancel}
                        class="text-gray-400 hover:text-gray-600 transition-colors"
                        aria-label="Close"
                    >
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                {/if}
            </div>
            
            {#if message}
                <p class="text-gray-600 mb-6">{message}</p>
            {/if}
            
            {#if children}
                {@render children()}
            {/if}
            {#if onCancel && onConfirm}
            <div class="flex gap-2 justify-end mt-6">
                <button
                    onclick={handleCancel}
                    class="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors font-medium"
                >
                    {cancelText}
                </button>
                <button
                    onclick={handleConfirm}
                    class={`px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                        isDangerous
                            ? 'bg-red-500 hover:bg-red-600'
                            : 'bg-[#1357ff] hover:bg-[#0f49d6]'
                    }`}
                >
                    {confirmText}
                </button>
            </div>
                    {/if}

        </div>
    </div>
{/if}
