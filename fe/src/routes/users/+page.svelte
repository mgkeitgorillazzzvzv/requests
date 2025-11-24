<script lang="ts">
    import Button from "$lib/components/controls/Button.svelte";
    import Entry from "$lib/components/controls/Entry.svelte";
    import Modal from "$lib/components/ui/Modal.svelte";
    import UserCard from "$lib/components/ui/UserCard.svelte";
    import { api, type UserOut } from "$lib/api";
    import { showToast } from "$lib/stores/toast";
    import { getFullName } from "$lib/util";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let users = $state<UserOut[]>(data.users ?? []);
    let isLoading = $state(false);
    let showDeleteModal = $state(false);
    let isDeleting = $state(false);
    let userToDelete = $state<UserOut | null>(null);
    let search = $state('');

    const filteredUsers = $derived.by(() => {
        const term = search.trim().toLowerCase();
        if (!term) {
            return users;
        }
        return users.filter((user) =>
            [user.first_name, user.last_name, user.username]
                .filter(Boolean)
                .some((value) => value.toLowerCase().includes(term))
        );
    });

    const fetchUsers = async () => {
        isLoading = true;
        try {
            users = await api.listUsers();
        } catch (error) {
            console.error('Failed to load users:', error);
            showToast('Не удалось загрузить пользователей', 'error');
        } finally {
            isLoading = false;
        }
    };

    onMount(() => {
        fetchUsers();
    });

    const handleCreateClick = () => {
        goto('/users/new');
    };

    const handleEdit = (user: UserOut) => {
        goto(`/users/${user.id}/edit`);
    };

    const handleDeleteClick = (user: UserOut) => {
        userToDelete = user;
        showDeleteModal = true;
    };

    const handleDeleteConfirm = async () => {
        const target = userToDelete;
        if (!target) {
            return;
        }

        isDeleting = true;
        try {
            await api.deleteUser(target.id);
            users = users.filter((u) => u.id !== target.id);
            showToast('Пользователь удалён', 'success');
        } catch (error) {
            console.error('Failed to delete user:', error);
            showToast('Ошибка при удалении пользователя', 'error');
        } finally {
            isDeleting = false;
            showDeleteModal = false;
            userToDelete = null;
        }
    };

    const handleDeleteCancel = () => {
        showDeleteModal = false;
        userToDelete = null;
    };
</script>

<div class="max-w-4xl mx-auto p-4 flex flex-col gap-4">
    <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-3">
        <div class="w-full">
            <h1 class="text-3xl font-bold">Пользователи</h1>
        </div>
        <Button onclick={handleCreateClick} className="md:w-auto w-full">Добавить</Button>
    </div>

    <div class="flex flex-col md:flex-row gap-3">
        <Entry
            bind:value={search}
            placeholder="Поиск по пользователям"
            aria-label="Поиск по пользователям"
        />
    </div>

    {#if isLoading}
        <div class="text-gray-500">Загрузка пользователей...</div>
    {:else if filteredUsers.length === 0}
        <div class="text-gray-500">Пользователи не найдены.</div>
    {:else}
        <div class="flex flex-col gap-3">
            {#each filteredUsers as user (user.id)}
                <UserCard
                    user={user}
                    onEdit={() => handleEdit(user)}
                    onDelete={() => handleDeleteClick(user)}
                />
            {/each}
        </div>
    {/if}
</div>

<Modal
    bind:isOpen={showDeleteModal}
    title="Удалить пользователя?"
    message={userToDelete
        ? `Пользователь ${getFullName(userToDelete)} будет удалён безвозвратно.`
        : 'Пользователь будет удалён безвозвратно.'}
    confirmText={isDeleting ? 'Удаление...' : 'Удалить'}
    cancelText="Отмена"
    onConfirm={handleDeleteConfirm}
    onCancel={handleDeleteCancel}
    isDangerous={true}
/>
