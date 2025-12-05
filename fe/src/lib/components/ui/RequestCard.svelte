<script lang="ts">
    import type { RequestOut } from "$lib/api";
    import { RequestStatus, api, Role } from "$lib/api";
    import { goto } from '$app/navigation';
    import userCreated from "$lib/assets/user_created.svg";
    import userCompleted from "$lib/assets/user_completed.svg";
    import building from "$lib/assets/building.svg";
    import department from "$lib/assets/department.svg";
    import {isMobile} from "$lib/platform"
    import { capitalizeFirstLetter, getFullName } from "$lib/util";
    
    let { request }: { request: RequestOut } = $props();
    let mobile = $state(false)
    
    $effect(() => {
        mobile = isMobile();
    });
    
    const getStatusColor = (status: RequestStatus): string => {
        switch(status) {
            case RequestStatus.Completed:
                return 'bg-green-500';
            case RequestStatus.PendingApproval:
                return 'bg-yellow-500';
            case RequestStatus.Postponed:
                return 'bg-red-500';
            case RequestStatus.PendingCreationApproval:
                return 'bg-purple-500';
            case RequestStatus.Created:
            default:
                return 'bg-blue-500';
        }
    };
</script>

<div
    class="flex flex-col md:flex-row border-2 rounded-2xl border-gray-300 p-4 justify-between gap-4 items-stretch cursor-pointer {request.urgent ? 'bg-red-50' : ''}"
    role="link"
    tabindex="0"
    onclick={() => goto(`/requests/${request.id}`)}
    onkeydown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            goto(`/requests/${request.id}`);
        }
    }}
>
    <div class="flex flex-col gap-2 flex-1 justify-between min-h-24">
        <div>
            <div class="font-bold text-2xl md:text-3xl flex items-center gap-2">
                {request.title}
                {#if request.urgent}
                    <span class="text-red-600 text-sm font-normal bg-red-100 px-2 py-1 rounded">Срочно</span>
                {/if}
            </div>
            <div class="text-gray-600 text-base md:text-xl">{request.description}</div>
        </div>
        <div class="flex flex-row gap-2 flex-wrap items-center">
            <div
                class="text-white rounded-2xl px-3 py-1 text-sm md:text-base {getStatusColor(request.status)}"
            >
                {capitalizeFirstLetter(request.status)}
            </div>
            {#if !request.is_anonymous && request.opened_by}
                <div class="flex flex-row items-center gap-1 text-sm md:text-lg">
                    <img
                        src={userCreated}
                        alt="Создано пользователем"
                        class="w-4 h-4 md:w-5 md:h-5"
                    />
                    <div class="text-gray-600 text-sm md:text-lg">
                        {getFullName(request.opened_by)}
                    </div>
                </div>
            {:else if request.is_anonymous}
                <div class="flex flex-row items-center gap-1 text-sm md:text-lg">
                    <div class="text-gray-500 italic text-sm md:text-lg">Анонимная заявка</div>
                </div>
            {/if}
            {#if request.status === RequestStatus.Completed && request.closed_by}
                <div class="flex flex-row items-center gap-1 text-sm md:text-lg">
                    <img
                        src={userCompleted}
                        alt="Завершено пользователем"
                        class="w-4 h-4 md:w-5 md:h-5"
                    />
                    <div class="text-gray-600 text-sm md:text-lg">
                        {getFullName(request.closed_by)}
                    </div>
                </div>
            {/if}
            <div class="flex flex-row items-center gap-1 text-sm md:text-lg">
                <img src={building} alt="Корпус" class="w-4 h-4 md:w-5 md:h-5" />
                <div class="text-gray-600 text-sm md:text-lg">{request.building}</div>
            </div>
            <div class="flex flex-row items-center gap-1">
                <img src={department} alt="Отдел" class="w-4 h-4 md:w-5 md:h-5"/>
                <div class="text-gray-600 text-sm md:text-lg">{request.department}</div>
            </div>
        </div>
    </div>
</div>
