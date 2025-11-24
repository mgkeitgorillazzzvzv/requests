<script lang="ts">
    import UserForm, { type UserFormValues } from "$lib/components/ui/UserForm.svelte";
    import { toast } from "$lib/stores/toast";
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import BackButton from "$lib/components/ui/BackButton.svelte";

    let isSubmitting = $state(false);

    const handleSubmit = async (values: UserFormValues) => {
        if (isSubmitting) {
            return;
        }

        isSubmitting = true;
        try {
            await api.createUser({
                username: values.username,
                password: values.password!,
                first_name: values.first_name,
                last_name: values.last_name,
                role: values.role,
                building: values.building || null,
                department: values.department || null
            });

            toast.success('Пользователь создан успешно');
            await goto('/users');
        } catch (error) {
            console.error('Failed to create user:', error);
            toast.error('Ошибка при создании пользователя');
            isSubmitting = false;
            throw error;
        }
    };

    const handleCancel = () => {
        goto('/users');
    };
</script>

<div class="flex flex-col gap-4 max-w-2xl mx-auto p-4">
    <BackButton />
    <h1 class="text-2xl font-bold">Создание пользователя</h1>
    
    <UserForm
        submitLabel="Создать пользователя"
        onSubmit={handleSubmit}
        showPasswordField={true}
        requirePassword={true}
        isSubmitting={isSubmitting}
    />

</div>