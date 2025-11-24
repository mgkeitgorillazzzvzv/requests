<script lang="ts">
    let { checked = $bindable(false), disabled = false, className = '', ...restProps } = $props()
</script>

<button
    type="button"
    role="switch"
    aria-checked={checked}
    {disabled}
    onclick={() => (checked = !checked)}
    class="relative inline-flex h-8 w-16 items-center rounded-full transition-colors {checked
        ? 'bg-[#1357ff]'
        : 'bg-gray-300'} {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} {className}"
    {...restProps}
>
    <span
        class="inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform {checked
            ? 'translate-x-9'
            : 'translate-x-1'}"
    ></span>
</button>
