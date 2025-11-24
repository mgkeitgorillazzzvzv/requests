<script lang="ts">
    import UserForm, { type UserFormValues } from "$lib/components/ui/UserForm.svelte";
    import Modal from "$lib/components/ui/Modal.svelte";
    import BackButton from "$lib/components/ui/BackButton.svelte";
    import { toast } from "$lib/stores/toast";
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let isLoading = $state(false);
    let showDeleteModal = $state(false);

    const handleSubmit = async (values: UserFormValues) => {
        if (isLoading) {
            return;
        }

        isLoading = true;
        try {
            await api.updateUser(data.user.id, {
                username: values.username,
                first_name: values.first_name,
                last_name: values.last_name,
                role: values.role,
                building: values.building || null,
                department: values.department || null,
                password: values.password || undefined
            });

            toast.success('Пользователь обновлен успешно');
            await goto('/users');
        } catch (error) {
            console.error('Failed to update user:', error);
            toast.error('Ошибка при обновлении пользователя');
            isLoading = false;
            throw error;
        }
    };

    const handleDeleteClick = () => {
        showDeleteModal = true;
    };

    const handleDeleteConfirm = async () => {
        if (isLoading) {
            return;
        }

        isLoading = true;
        try {
            await api.deleteUser(data.user.id);

            toast.success('Пользователь удален успешно');
            await goto('/users');
        } catch (error) {
            console.error('Failed to delete user:', error);
            toast.error('Ошибка при удалении пользователя');
            isLoading = false;
        }
    };

    const handleDeleteCancel = () => {
        showDeleteModal = false;
    };
</script>

<div class="flex flex-col gap-4 max-w-2xl mx-auto p-4">
    <BackButton />
    <h1 class="text-2xl font-bold">Редактирование пользователя</h1>

    <UserForm
        initialUser={data.user}
        submitLabel="Сохранить изменения"
        onSubmit={handleSubmit}
        showPasswordField={true}
        requirePassword={false}
        isSubmitting={isLoading}
    />

    <button
        onclick={handleDeleteClick}
        disabled={isLoading}
        class="bg-red-500 hover:bg-red-600 disabled:bg-red-400 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
    >
        {isLoading ? 'Удаление...' : 'Удалить пользователя'}
    </button>
</div>

<Modal
    bind:isOpen={showDeleteModal}
    title="Удалить пользователя?"
    message="Это действие невозможно отменить. Пользователь будет удален безвозвратно."
    confirmText="Удалить"
    cancelText="Отмена"
    onConfirm={handleDeleteConfirm}
    onCancel={handleDeleteCancel}
    isDangerous={true}
/>
