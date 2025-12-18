<script lang="ts">
    import Entry from "$lib/components/controls/Entry.svelte";
    import Modal from "$lib/components/ui/Modal.svelte";
    import FAB from "$lib/components/ui/FAB.svelte";
    import UserCard from "$lib/components/ui/UserCard.svelte";
    import { api, type UserOut } from "$lib/api";
    import { showToast } from "$lib/stores/toast";
    import { getFullName } from "$lib/util";
    import { createPullToRefresh, attachPullToRefresh, PULL_THRESHOLD } from "$lib/utils/pullToRefresh";
    import { goto } from "$app/navigation";
    import { canCreateUsers } from "$lib/stores/auth";
    import { onMount } from "svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let users = $state<UserOut[]>(data.users ?? []);
    let isLoading = $state(false);
    let showDeleteModal = $state(false);
    let isDeleting = $state(false);
    let userToDelete = $state<UserOut | null>(null);
    let search = $state('');
    let pullState = $state({ pullProgress: 0, isPulling: false, touchStartY: 0 });

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
        
        const pullHandlers = createPullToRefresh(pullState, () => isLoading, () => fetchUsers());
        const cleanup = attachPullToRefresh(pullHandlers);
        
        return () => {
            cleanup();
        };
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
    {#if pullState.isPulling || pullState.pullProgress > 0}
        <div class="fixed top-0 left-0 right-0 h-1 bg-blue-500 z-50" style="width: {(pullState.pullProgress / PULL_THRESHOLD) * 100}%"></div>
    {/if}
    
    <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-3">
        <div class="w-full">
            <h1 class="text-3xl font-bold">Пользователи</h1>
            <p class="text-gray-600">Просматривайте и управляйте пользователями.</p>
        </div>
        <!-- header button removed in favor of FAB -->
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

{#if $canCreateUsers}
    <FAB onclick={handleCreateClick} ariaLabel="Создать пользователя" title="Создать пользователя" text="Создать пользователя" />
{/if}

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
