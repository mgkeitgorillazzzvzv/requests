<script lang="ts">
    import Button from "$lib/components/controls/Button.svelte";
    import Entry from "$lib/components/controls/Entry.svelte";
    import Dropdown from "$lib/components/controls/Dropdown.svelte";
    import Toggle from "$lib/components/controls/Toggle.svelte";
    import Modal from "$lib/components/ui/Modal.svelte";
    import BackButton from "$lib/components/ui/BackButton.svelte";
    import {toast} from "$lib/stores/toast";
    import { Department, Building, Role, api } from "$lib/api";
    import { goto } from "$app/navigation";
    import { onMount, onDestroy } from "svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();

    let title = $state('');
    let description = $state('');
    let department = $state<Department>(Department.Maintenance);
    let building = $state<Building>(Building.Millionschikova);
    let urgent = $state(false);
    let isLoading = $state(false);
    let showDeleteModal = $state(false);
    
    let thumbnailUrls: Record<number, string | null> = $state({});

    const buildingOptions = [
        { label: 'Миллионщикова', value: Building.Millionschikova },
        { label: 'Коломенская', value: Building.Kolomenskaya },
        { label: 'Судостроительная', value: Building.Sudostroitelnaya },
        { label: 'Харьковский', value: Building.Kharkovskiy }
    ];

    onMount(() => {
        if (data?.request) {
            title = data.request.title;
            description = data.request.description || '';
            department = (data.request.department as Department) || Department.Maintenance;
            building = data.request.building;
            urgent = data.request.urgent || false;
        }
        
        const loadThumbnails = async () => {
            if (!data?.request?.photos) return;

            for (const photo of data.request.photos) {
                if (!thumbnailUrls[photo.id]) {
                    try {
                        const blob = await api.getPhotoThumbnail(photo.id, 200);
                        thumbnailUrls[photo.id] = URL.createObjectURL(blob);
                    } catch (err) {
                        console.error('Failed to load thumbnail', photo.id, err);
                        thumbnailUrls[photo.id] = null;
                    }
                }
            }
        };

        loadThumbnails();
    });

    const handleSubmit = async () => {
        if (isLoading) {
            return;
        }

        if (!title) {
            toast.error('Введите заголовок');
            return;
        }
        
        isLoading = true;
        try {
            await api.updateRequest(data.request.id, {
                title,
                description: description || null,
                building,
                department,
                urgent
            });
            
            toast.success('Заявка обновлена успешно');
            await goto(`/requests/${data.request.id}`);
        } catch (error) {
            console.error('Failed to update request:', error);
            toast.error('Ошибка при обновлении заявки');
            isLoading = false;
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
            await api.deleteRequest(data.request.id);
            
            toast.success('Заявка удалена успешно');
            await goto('/requests');
        } catch (error) {
            console.error('Failed to delete request:', error);
            toast.error('Ошибка при удалении заявки');
            isLoading = false;
        }
    };

    const handleDeleteCancel = () => {
        showDeleteModal = false;
    };

    
    onDestroy(() => {
        for (const idStr in thumbnailUrls) {
            const url = thumbnailUrls[idStr];
            if (url) URL.revokeObjectURL(url);
        }
    });
</script>

<div class="flex flex-col gap-4 max-w-2xl mx-auto p-4">
    <BackButton />
    <h1 class="text-2xl font-bold">Редактирование заявки</h1>
    
    <Entry bind:value={title} placeholder="Опишите проблему" disabled={isLoading}/>
    
    <!-- Department selection - только АХЧ в UI (IT появится позже) -->
    <Dropdown
        bind:value={department}
        options={[
            { label: 'АХЧ', value: Department.Maintenance },
        ]}
        placeholder="Выберите отдел"
        disabled={isLoading}
    />

    {#if data.user?.role === Role.Admin}
        <Dropdown
            bind:value={building}
            options={buildingOptions}
            placeholder="Выберите корпус"
            disabled={isLoading}
        />
    {/if}

    <!-- Urgent checkbox -->
    <div class="flex items-center gap-3">
        <Toggle bind:checked={urgent} disabled={isLoading} />
        <span class="text-lg">Срочная заявка</span>
    </div>

    <!-- Existing Photos Section -->
    {#if data?.request?.photos && data.request.photos.length > 0}
        <div class="border-2 border-gray-200 rounded p-4">
            <h3 class="text-xl font-semibold mb-2">Загруженные фотографии</h3>
            <div class="grid grid-cols-3 gap-2">
                {#each data.request.photos as photo}
                    <div class="relative">
                        {#if thumbnailUrls[photo.id]}
                            <img
                                src={thumbnailUrls[photo.id] ?? ''}
                                alt=""
                                class="w-full h-32 object-cover rounded border"
                            />
                        {:else}
                            <div class="w-full h-32 bg-gray-200 animate-pulse rounded border flex items-center justify-center">
                                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        </div>
    {/if}
            <Entry bind:value={description} placeholder="Комментарий" disabled={isLoading}/>

    <div class="flex gap-2">
        <Button onclick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
        </Button>
        <button 
            onclick={handleDeleteClick} 
            disabled={isLoading}
            class="bg-red-500 hover:bg-red-600 disabled:bg-red-400 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
        >
            {isLoading ? 'Удаление...' : 'Удалить заявку'}
        </button>
    </div>
</div>

<Modal 
    bind:isOpen={showDeleteModal}
    title="Удалить заявку?"
    message="Это действие невозможно отменить. Заявка будет удалена безвозвратно."
    confirmText="Удалить"
    cancelText="Отмена"
    onConfirm={handleDeleteConfirm}
    onCancel={handleDeleteCancel}
    isDangerous={true}
/>

