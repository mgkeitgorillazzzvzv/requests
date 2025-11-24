<script lang="ts">
    let { children, onclick, className = '', variant = 'primary', disabled = false, ...restProps } = $props()
    
    type Variant = 'primary' | 'danger' | 'secondary';
    
    const variantClasses: Record<Variant, string> = {
        primary: 'bg-[#1357ff] hover:bg-[#0f49d6] text-white',
        danger: 'bg-red-600 hover:bg-red-700 text-white',
        secondary: 'bg-gray-500 hover:bg-gray-600 text-white'
    }
    
    const classes = variantClasses[variant as Variant] || variantClasses.primary
    const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-90'
</script>

<button 
    {onclick} 
    {disabled}
    class="{classes} {disabledClasses} rounded-2xl px-5 py-3 transition-colors {className}" 
    {...restProps}
>
    {@render children()}
</button>

