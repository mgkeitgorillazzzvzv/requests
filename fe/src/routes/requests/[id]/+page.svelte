<script lang="ts">
    import Button from "$lib/components/controls/Button.svelte";
    import Entry from "$lib/components/controls/Entry.svelte";
    import Dropdown from "$lib/components/controls/Dropdown.svelte";
    import Modal from "$lib/components/ui/Modal.svelte";
    import ImageGallery from "$lib/components/ui/ImageGallery.svelte";
    import BackButton from "$lib/components/ui/BackButton.svelte";
    import { toast } from "$lib/stores/toast";
    import { api, RequestStatus, Role } from "$lib/api";
    import { goto, invalidateAll } from "$app/navigation";
    import { createPullToRefresh, attachPullToRefresh, PULL_THRESHOLD } from "$lib/utils/pullToRefresh";
    import userCreated from "$lib/assets/user_created.svg";
    import userCompleted from "$lib/assets/user_completed.svg";
    import building from "$lib/assets/building.svg";
    import department from "$lib/assets/department.svg";
    import { capitalizeFirstLetter, formatDateWithoutSeconds, getFullName } from "$lib/util";
    import type { PageData } from "./$types";
    
    let { data }: { data: PageData } = $props();

    let isLoading = $state(false);
    let showStatusChangeModal = $state(false);
    let showRejectionModal = $state(false);
    let pullState = $state({ pullProgress: 0, isPulling: false, touchStartY: 0 });
    
    let requestedStatus = $state<RequestStatus>(RequestStatus.Completed);
    let statusChangeReason = $state('');
    let statusChangePhotoFile = $state<File | null>(null);
    let statusChangePhotoPreview = $state<string | null>(null);
    let photoInputRef = $state<HTMLInputElement | null>(null);
    
    
    let currentReviewId = $state<number | null>(null);
    let rejectionReason = $state('');
    let rejectionPhotoFile = $state<File | null>(null);
    let rejectionPhotoPreview = $state<string | null>(null);
    let rejectionPhotoInputRef = $state<HTMLInputElement | null>(null);


    const canEdit = $derived.by(() => {
        if (!data.user || !data.request) return false;
        if (data.user.role === Role.Admin) return true;
        if (data.user.role === Role.HeadOfDepartment) {
            return data.user.building === data.request.building && data.request.status === RequestStatus.Created;
        }
        if (data.user.role === Role.Specialist) {
            return data.request.status === RequestStatus.Created;
        }
        return false;
    });

    
    const canRequestStatusChange = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.Executor || data.user.role === Role.Specialist) && data.request.status === RequestStatus.Created;
    });

    
    const canReviewStatusChange = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.HeadOfDepartment || data.user.role === Role.Admin) && 
               data.request.pending_status_changes && 
               data.request.pending_status_changes.length > 0;
    });

    
    const canDirectlyChangeStatus = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.Admin || data.user.role === Role.HeadOfDepartment) && 
               data.request.status === RequestStatus.Created;
    });

    
    const canReturnToWork = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.Admin || data.user.role === Role.HeadOfDepartment) && 
               data.request.status === RequestStatus.Postponed;
    });

    
    const canApproveAnonymous = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.Admin || data.user.role === Role.HeadOfDepartment) && 
               data.request.is_anonymous &&
               data.request.status === RequestStatus.PendingCreationApproval;
    });

    
    const canEditAnonymous = $derived.by(() => {
        if (!data.user || !data.request) return false;
        return (data.user.role === Role.Admin || data.user.role === Role.HeadOfDepartment) && 
               data.request.is_anonymous &&
               data.request.status === RequestStatus.PendingCreationApproval;
    });

    const handleEditClick = () => {
        goto(`/requests/${data.request.id}/edit`);
    };

    const handleStatusChangePhotoInput = (event: Event) => {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            statusChangePhotoFile = target.files[0];
            if (statusChangePhotoPreview) URL.revokeObjectURL(statusChangePhotoPreview);
            statusChangePhotoPreview = URL.createObjectURL(target.files[0]);
        }
    };

    const triggerPhotoInput = () => {
        photoInputRef?.click();
    };

    const handleRejectionPhotoInput = (event: Event) => {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            rejectionPhotoFile = target.files[0];
            if (rejectionPhotoPreview) URL.revokeObjectURL(rejectionPhotoPreview);
            rejectionPhotoPreview = URL.createObjectURL(target.files[0]);
        }
    };

    const triggerRejectionPhotoInput = () => {
        rejectionPhotoInputRef?.click();
    };

    let thumbnailUrlCache: Record<number, string | null> = $state({});

    const getThumbnailUrl = async (photoId: number) => {
        if (thumbnailUrlCache[photoId] !== undefined) {
            return thumbnailUrlCache[photoId];
        }
        try {
            const blob = await api.getPhotoThumbnail(photoId, 200);
            thumbnailUrlCache[photoId] = URL.createObjectURL(blob);
            return thumbnailUrlCache[photoId];
        } catch (err) {
            console.error('Failed to load thumbnail', photoId, err);
            thumbnailUrlCache[photoId] = null;
            return null;
        }
    };

    const handleRequestStatusChange = async () => {
        if (!data.request) return;

        
        if (requestedStatus === RequestStatus.Postponed && !statusChangeReason.trim()) {
            toast.error('Для отложения обязательно укажите причину');
            return;
        }

        isLoading = true;
        try {
            
            let photoId: number | null = null;
            if (statusChangePhotoFile) {
                const uploadedPhoto = await api.uploadPhoto(data.request.id, {
                    file: statusChangePhotoFile,
                    caption: 'Фото выполненной работы'
                });
                photoId = uploadedPhoto.id;
            }

            
            await api.createStatusChangeRequest(data.request.id, {
                requested_status: requestedStatus,
                reason: requestedStatus === RequestStatus.Postponed ? statusChangeReason : undefined,
                photo_id: photoId || undefined
            });

            toast.success('Запрос на изменение статуса отправлен');
            showStatusChangeModal = false;
            statusChangeReason = '';
            statusChangePhotoFile = null;
            if (statusChangePhotoPreview) {
                URL.revokeObjectURL(statusChangePhotoPreview);
                statusChangePhotoPreview = null;
            }
            await invalidateAll();
        } catch (error) {
            console.error('Failed to create status change request:', error);
            toast.error('Ошибка при создании запроса');
        } finally {
            isLoading = false;
        }
    };

    const handleApproveStatusChange = async (changeRequestId: number) => {
        if (!data.request) return;
        
        isLoading = true;
        try {
            await api.reviewStatusChangeRequest(data.request.id, changeRequestId, {
                approved: true
            });
            toast.success('Запрос подтвержден');
            await invalidateAll();
        } catch (error) {
            console.error('Failed to approve status change:', error);
            toast.error('Ошибка при подтверждении');
        } finally {
            isLoading = false;
        }
    };

    const handleRejectStatusChange = async () => {
        if (!data.request || !currentReviewId) return;

        isLoading = true;
        try {
            
            let photoId: number | null = null;
            if (rejectionPhotoFile) {
                const uploadedPhoto = await api.uploadPhoto(data.request.id, {
                    file: rejectionPhotoFile,
                    caption: 'Причина отклонения'
                });
                photoId = uploadedPhoto.id;
            }

            await api.reviewStatusChangeRequest(data.request.id, currentReviewId, {
                approved: false,
                rejection_reason: rejectionReason.trim() || undefined,
                rejection_photo_id: photoId || undefined
            });

            toast.success('Запрос отклонен');
            showRejectionModal = false;
            currentReviewId = null;
            rejectionReason = '';
            rejectionPhotoFile = null;
            if (rejectionPhotoPreview) {
                URL.revokeObjectURL(rejectionPhotoPreview);
                rejectionPhotoPreview = null;
            }
            await invalidateAll();
        } catch (error) {
            console.error('Failed to reject status change:', error);
            toast.error('Ошибка при отклонении');
        } finally {
            isLoading = false;
        }
    };

    const openRejectModal = (changeRequestId: number) => {
        currentReviewId = changeRequestId;
        showRejectionModal = true;
    };

    const handleDirectStatusChange = async (newStatus: RequestStatus) => {
        if (!data.request) return;

        isLoading = true;
        try {
            await api.updateRequestStatus(data.request.id, newStatus);
            toast.success('Статус изменен');
            await invalidateAll();
        } catch (error) {
            console.error('Failed to change status:', error);
            toast.error('Ошибка при изменении статуса');
        } finally {
            isLoading = false;
        }
    };

    const handleReturnToWork = async () => {
        if (!data.request) return;

        isLoading = true;
        try {
            await api.returnPostponedToWork(data.request.id);
            toast.success('Заявка возвращена в работу');
            await invalidateAll();
        } catch (error) {
            console.error('Failed to return to work:', error);
            toast.error('Ошибка при возврате заявки в работу');
        } finally {
            isLoading = false;
        }
    };

    const handleApproveAnonymous = async () => {
        if (!data.request) return;

        isLoading = true;
        try {
            await api.approveAnonymousRequest(data.request.id);
            toast.success('Анонимная заявка одобрена');
            await invalidateAll();
        } catch (error) {
            console.error('Failed to approve anonymous request:', error);
            toast.error('Ошибка при одобрении заявки');
        } finally {
            isLoading = false;
        }
    };

    const handleDeleteAnonymous = async () => {
        if (!data.request) return;

        if (!confirm('Вы уверены, что хотите удалить эту заявку?')) return;

        isLoading = true;
        try {
            await api.deleteRequest(data.request.id);
            toast.success('Заявка удалена');
            goto('/requests');
        } catch (error) {
            console.error('Failed to delete request:', error);
            toast.error('Ошибка при удалении заявки');
        } finally {
            isLoading = false;
        }
    };

    const getStatusColor = (status: RequestStatus) => {
        switch (status) {
            case RequestStatus.Completed:
                return 'bg-green-500';
            case RequestStatus.PendingApproval:
                return 'bg-yellow-500';
            case RequestStatus.Postponed:
                return 'bg-gray-500';
            case RequestStatus.PendingCreationApproval:
                return 'bg-purple-500';
            default:
                return 'bg-blue-500';
        }
    };

    const formatHistoryAction = (historyItem: any) => {
        const userName = getFullName(historyItem.performed_by);
        
        switch (historyItem.action) {
            case 'created':
                return `${userName} создал(а) заявку`;
            
            case 'status_changed':
                if (historyItem.old_status && historyItem.new_status) {
                    const oldStatusRu = getStatusNameInRussian(historyItem.old_status);
                    const newStatusRu = getStatusNameInRussian(historyItem.new_status);
                    return `${userName} изменил статус с "${oldStatusRu}" на "${newStatusRu}"`;
                }
                return `${userName} изменил статус`;
            
            case 'status_change_requested':
                if (historyItem.new_status) {
                    const newStatusRu = getStatusNameInRussian(historyItem.new_status);
                    return `${userName} запросил изменение статуса на "${newStatusRu}"`;
                }
                return `${userName} запросил изменение статуса`;
            
            case 'status_change_approved':
                if (historyItem.new_status) {
                    const newStatusRu = getStatusNameInRussian(historyItem.new_status);
                    return `${userName} подтвердил изменение статуса на "${newStatusRu}"`;
                }
                return `${userName} подтвердил изменение статуса`;
            
            case 'status_change_rejected':
                return `${userName} отклонил запрос на изменение статуса`;
            
            case 'anonymous_request_approved':
                if (historyItem.new_status) {
                    const newStatusRu = getStatusNameInRussian(historyItem.new_status);
                    return `${userName} одобрил(а) анонимную заявку и изменил статус на "${newStatusRu}"`;
                }
                return `${userName} одобрил(а) анонимную заявку`;
            
            default:
                return `${userName} выполнил действие: ${historyItem.action}`;
        }
    };

    const getStatusNameInRussian = (status: string) => {
        switch (status) {
            case RequestStatus.Created:
            case 'created':
                return 'Создана';
            case RequestStatus.Completed:
            case 'completed':
                return 'Выполнена';
            case RequestStatus.Postponed:
            case 'postponed':
                return 'Отложена';
            case RequestStatus.PendingApproval:
            case 'pending_approval':
                return 'Ожидает подтверждения';
            default:
                return status;
        }
    };
</script>

<div class="max-w-4xl mx-auto p-4">
    {#if pullState.isPulling || pullState.pullProgress > 0}
        <div class="fixed top-0 left-0 right-0 h-1 bg-blue-500 z-50" style="width: {(pullState.pullProgress / PULL_THRESHOLD) * 100}%"></div>
    {/if}
    
    <BackButton />
    
    <div class="mb-4 md:mb-6 {data.request.urgent ? 'bg-red-50 p-4 rounded-lg' : ''}">
        <div class="flex items-start gap-3 mb-3">
            <h1 class="text-2xl md:text-3xl font-bold flex-1">{data.request.title}</h1>
            {#if data.request.urgent}
                <span class="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-semibold">Срочно</span>
            {/if}
        </div>



        
        <div class="flex flex-wrap gap-3 mb-4">
            <span class="{getStatusColor(data.request.status)} text-white rounded-2xl px-4 py-1.5 text-sm font-medium">
                {capitalizeFirstLetter(data.request.status)}
            </span>
            
            {#if data.request.opened_by}
                <div class="flex items-center gap-2">
                    <img src={userCreated} alt="" class="w-5 h-5" />
                    <span class="text-gray-600"><strong>{getFullName(data.request.opened_by)}</strong></span>
                    <span class="text-gray-500 text-sm">{formatDateWithoutSeconds(data.request.opened_at)}</span>
                </div>
            {:else if data.request.is_anonymous}
                <div class="flex items-center gap-2">
                    <img src={userCreated} alt="" class="w-5 h-5" />
                    <span class="text-gray-500 italic">Анонимная заявка</span>
                    <span class="text-gray-500 text-sm">{formatDateWithoutSeconds(data.request.opened_at)}</span>
                </div>
            {/if}

            {#if (data.request.status === RequestStatus.Completed || data.request.status === RequestStatus.Postponed) && data.request.closed_by}
                <div class="flex items-center gap-2">
                    <img src={userCompleted} alt="" class="w-5 h-5" />
                    <span class="text-gray-600"><strong>{getFullName(data.request.closed_by)}</strong></span>
                    {#if data.request.closed_at}
                        <span class="text-gray-500 text-sm">{formatDateWithoutSeconds(data.request.closed_at)}</span>
                    {/if}
                </div>
            {/if}

            <div class="flex items-center gap-2">
                <img src={building} alt="" class="w-5 h-5" />
                <span class="text-gray-600"><strong>{data.request.building}</strong></span>
            </div>

            <div class="flex items-center gap-2">
                <img src={department} alt="" class="w-5 h-5" />
                <span class="text-gray-600"><strong>{data.request.department}</strong></span>
            </div>
        </div>
    </div>

    
    {#if data.request.pending_status_changes && data.request.pending_status_changes.length > 0}
        <div class="mb-6 border-2 border-yellow-300 bg-yellow-50 rounded-lg p-4">
            <h2 class="text-lg md:text-xl font-semibold mb-3 text-yellow-800">Ожидает подтверждения</h2>
            {#each data.request.pending_status_changes as change}
                <div class="bg-white rounded-lg p-4 mb-3 last:mb-0">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <p class="font-semibold">
                                {getFullName(change.requested_by)} запросил изменение статуса на 
                                <span class="text-blue-600">{change.requested_status}</span>
                            </p>
                            <p class="text-sm text-gray-500">{formatDateWithoutSeconds(change.created_at)}</p>
                        </div>
                    </div>
                    
                    {#if change.reason}
                        <p class="mt-2 text-gray-700"><strong>Причина:</strong> {change.reason}</p>
                    {/if}
                    
                    {#if change.photo}
                        <div class="mt-2">
                            <p class="text-sm font-semibold mb-1">Прикрепленное фото:</p>
                            {#await getThumbnailUrl(change.photo.id)}
                                <div class="w-48 h-48 bg-gray-200 rounded animate-pulse"></div>
                            {:then url}
                                {#if url}
                                    <img src={url} alt="" class="w-48 h-48 object-cover rounded" />
                                {:else}
                                    <p class="text-sm text-gray-500">Не удалось загрузить фото</p>
                                {/if}
                            {:catch error}
                                <p class="text-sm text-gray-500">Ошибка загрузки: {error.message}</p>
                            {/await}
                        </div>
                    {/if}

                    {#if canReviewStatusChange}
                        <div class="flex gap-2 mt-3">
                            <button
                                onclick={() => handleApproveStatusChange(change.id)}
                                disabled={isLoading}
                                class="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white rounded-lg px-4 py-2 text-sm"
                            >
                                Подтвердить
                            </button>
                            <button
                                onclick={() => openRejectModal(change.id)}
                                disabled={isLoading}
                                class="bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white rounded-lg px-4 py-2 text-sm"
                            >
                                Отклонить
                            </button>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}

    
    {#if data.request.history && data.request.history.length > 0}
        <div class="mb-6">
            <h2 class="text-lg md:text-xl font-semibold mb-3">История изменений</h2>
            <div class="space-y-3">
                {#each data.request.history as historyItem}
                    <div class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                        <div class="flex items-start gap-3">
                            <div class="shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold">
                                {historyItem.performed_by.first_name[0]}{historyItem.performed_by.last_name[0]}
                            </div>
                            <div class="flex-1 min-w-0">
                                <p class="text-gray-900 font-medium">{formatHistoryAction(historyItem)}</p>
  
                                <p class="text-xs text-gray-500 mt-2">{formatDateWithoutSeconds(historyItem.created_at)}</p>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}

    
    {#if data.request.photos && data.request.photos.length > 0}
        {@const filteredPhotos = data.request.photos.filter(p => !p.caption?.includes('выполненной работы'))}
        {#if filteredPhotos.length > 0}
            <div class="mb-6">
                <h2 class="text-lg md:text-xl font-semibold mb-3">Фотографии ({filteredPhotos.length})</h2>
                <ImageGallery photos={filteredPhotos} />
            </div>
        {/if}
    {/if}
        {#if data.request.description}
            <p class="text-gray-700 text-base leading-relaxed mb-4">{data.request.description}</p>
        {/if}
    
    <div class="flex flex-wrap gap-2">
        {#if canEdit}
            <Button onclick={handleEditClick}>Редактировать</Button>
        {/if}
        
        {#if canRequestStatusChange}
            <button
                onclick={() => (showStatusChangeModal = true)}
                disabled={isLoading}
                class="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Изменить статус
            </button>
        {/if}

        {#if canDirectlyChangeStatus}
            <button
                onclick={() => handleDirectStatusChange(RequestStatus.Completed)}
                disabled={isLoading}
                class="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Завершить
            </button>
            <button
                onclick={() => handleDirectStatusChange(RequestStatus.Postponed)}
                disabled={isLoading}
                class="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Отложить
            </button>
        {/if}

        {#if canReturnToWork}
            <button
                onclick={handleReturnToWork}
                disabled={isLoading}
                class="bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Вернуть в работу
            </button>
        {/if}

        
        {#if canEditAnonymous}
            <button
                onclick={handleEditClick}
                disabled={isLoading}
                class="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Редактировать
            </button>
        {/if}

        {#if canApproveAnonymous}
            <button
                onclick={handleApproveAnonymous}
                disabled={isLoading}
                class="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                {isLoading ? 'Одобряю...' : 'Одобрить'}
            </button>
            <button
                onclick={handleDeleteAnonymous}
                disabled={isLoading}
                class="bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                Удалить
            </button>
        {/if}
    </div>
</div>

<Modal
    bind:isOpen={showStatusChangeModal}
    title="Запрос на изменение статуса"
    confirmText={isLoading ? 'Отправка...' : 'Отправить'}
    cancelText="Отмена"
    onConfirm={handleRequestStatusChange}
    onCancel={() => {
        showStatusChangeModal = false;
        statusChangeReason = '';
        statusChangePhotoFile = null;
        if (statusChangePhotoPreview) {
            URL.revokeObjectURL(statusChangePhotoPreview);
            statusChangePhotoPreview = null;
        }
    }}
    isDangerous={false}
>
    <div class="flex flex-col gap-4">
        <div>
            <label for="status-dropdown" class="block text-sm font-medium mb-2">Новый статус</label>
            <Dropdown
                id="status-dropdown"
                bind:value={requestedStatus}
                options={[
                    { label: 'Выполнено', value: RequestStatus.Completed },
                    { label: 'Отложено', value: RequestStatus.Postponed }
                ]}
                placeholder="Выберите статус"
            />
        </div>

        {#if requestedStatus === RequestStatus.Postponed}
            <div>
                <label for="reason-input" class="block text-sm font-medium mb-2">Причина отложения *</label>
                <Entry id="reason-input" bind:value={statusChangeReason} placeholder="Укажите причину" />
            </div>
        {/if}

        {#if requestedStatus === RequestStatus.Completed}
            <div>
                <label for="photo-input" class="block text-sm font-medium mb-2">Фото выполненной работы (необязательно)</label>
                <input
                    bind:this={photoInputRef}
                    id="photo-input"
                    type="file"
                    accept="image/*"
                    onchange={handleStatusChangePhotoInput}
                    class="hidden"
                />
                <button
                    type="button"
                    onclick={triggerPhotoInput}
                    class="bg-[#1357ff] hover:bg-[#0f49d6] text-white rounded-2xl px-5 py-3 transition-colors font-medium"
                >
                    📷 Выбрать фото
                </button>
                {#if statusChangePhotoFile}
                    <p class="mt-2 text-sm text-gray-600">Выбран файл: {statusChangePhotoFile.name}</p>
                {/if}
                {#if statusChangePhotoPreview}
                    <img src={statusChangePhotoPreview} alt="Preview" class="mt-2 w-full h-48 object-cover rounded" />
                {/if}
            </div>
        {/if}
    </div>
</Modal>


<Modal
    bind:isOpen={showRejectionModal}
    title="Отклонение запроса"
    confirmText={isLoading ? 'Отклонение...' : 'Отклонить'}
    cancelText="Отмена"
    onConfirm={handleRejectStatusChange}
    onCancel={() => {
        showRejectionModal = false;
        currentReviewId = null;
        rejectionReason = '';
        rejectionPhotoFile = null;
        if (rejectionPhotoPreview) {
            URL.revokeObjectURL(rejectionPhotoPreview);
            rejectionPhotoPreview = null;
        }
    }}
    isDangerous={true}
>
    <div class="flex flex-col gap-4">
        <div>
            <label for="rejection-reason" class="block text-sm font-medium mb-2">Причина отклонения (необязательно)</label>
            <Entry id="rejection-reason" bind:value={rejectionReason} placeholder="Укажите причину отклонения" />
        </div>

        <div>
            <label for="rejection-photo" class="block text-sm font-medium mb-2">Фото с пояснением (необязательно)</label>
            <input
                bind:this={rejectionPhotoInputRef}
                id="rejection-photo"
                type="file"
                accept="image/*"
                onchange={handleRejectionPhotoInput}
                class="hidden"
            />
            <button
                type="button"
                onclick={triggerRejectionPhotoInput}
                class="bg-[#1357ff] hover:bg-[#0f49d6] text-white rounded-2xl px-5 py-3 transition-colors font-medium"
            >
                📷 Выбрать фото
            </button>
            {#if rejectionPhotoFile}
                <p class="mt-2 text-sm text-gray-600">Выбран файл: {rejectionPhotoFile.name}</p>
            {/if}
            {#if rejectionPhotoPreview}
                <img src={rejectionPhotoPreview} alt="Preview" class="mt-2 w-full h-48 object-cover rounded" />
            {/if}
        </div>
    </div>
</Modal>
