<script lang="ts">
    import type { HTMLInputAttributes } from "svelte/elements";
    import showPasswordIcon from "$lib/assets/show_password.svg";
    import hidePasswordIcon from "$lib/assets/hide_password.svg";
    let { value = $bindable(), className = '', type= '', ...restProps }: { value?: string, className?: string } & HTMLInputAttributes = $props()
    
    let showPassword = $state(false);
    
    const inputType = $derived(type === 'password' && !showPassword ? 'password' : type === 'password' ? 'text' : type);
    const isPasswordField = $derived(type === 'password');
    
    function togglePassword() {
        showPassword = !showPassword;
    }
</script>

<div class="relative w-full">
    <input bind:value={value} type={inputType} class="{className} w-full border border-gray-300 rounded-xl px-4 py-3 transition duration-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 placeholder:text-gray-400 {isPasswordField ? 'pr-12' : ''}" {...restProps}/>
    {#if isPasswordField}
        <button
            type="button"
            onclick={togglePassword}
            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition"
            aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
        >
            {#if showPassword}
                <img src={hidePasswordIcon} alt="Скрыть пароль">
            {:else}
                <img src={showPasswordIcon} alt="Показать пароль">
            {/if}
        </button>
    {/if}
</div>