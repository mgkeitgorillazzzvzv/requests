<script lang="ts">
    type Option = string | { label: string; value: string };

    let { value = $bindable<string>(), options = [] as Option[], className = '', ...restProps } = $props();
    let open = $state(false);
    let buttonEl: HTMLButtonElement;

    function getDisplayLabel(val: string): string {
        const opt = options.find((o) => (typeof o === 'string' ? o === val : o.value === val));
        return opt ? (typeof opt === 'string' ? opt : opt.label) : '';
    }

    function selectOption(opt: Option) {
        value = typeof opt === 'string' ? opt : opt.value;
        open = false;
        buttonEl?.focus();
    }

    function toggleOpen() {
        open = !open;
    }

    function handleBlur() {
        setTimeout(() => {
            open = false;
        }, 150);
    }
</script>

<div class="relative inline-block w-full">
    <button
        bind:this={buttonEl}
        onclick={toggleOpen}
        onblur={handleBlur}
        class="w-full border border-gray-300 rounded-xl px-4 py-3 bg-white text-gray-900 text-left transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 {className}"
        type="button"
        {...restProps}
    >
        {getDisplayLabel(value) || (restProps.placeholder || 'Выберите опцию')}
    </button>
    {#if open}
        <ul class="absolute left-0 right-0 mt-1 max-h-56 overflow-auto rounded-xl bg-white border border-gray-300 shadow-lg z-10">
            {#each options as option (option)}
                <li
                    class="px-4 py-3 hover:bg-blue-50 cursor-pointer text-sm text-gray-700 transition duration-150"
                    role="option"
                    tabindex="0"
                    aria-selected={typeof option === 'string' ? value === option : value === option.value}
                    onclick={() => selectOption(option)}
                    onkeydown={(e) => e.key === 'Enter' && selectOption(option)}
                >
                    {typeof option === 'string' ? option : option.label}
                </li>
            {/each}
        </ul>
    {/if}
</div>

