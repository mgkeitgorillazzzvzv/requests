<script lang="ts">
    import type { UserOut } from "$lib/api";
    import { getFullName, capitalizeFirstLetter } from "$lib/util";
    import userIcon from "$lib/assets/user.svg";
    import roleIcon from "$lib/assets/department.svg";
    import buildingIcon from "$lib/assets/building.svg";

    interface Props {
        user: UserOut;
        onEdit?: () => void;
        onDelete?: () => void;
    }

    let { user, onEdit, onDelete }: Props = $props();
</script>

<div class="flex flex-col md:flex-row border-2 rounded-2xl border-gray-300 p-4 gap-4 items-stretch">
    <div class="flex flex-col gap-3 flex-1 min-h-24">
        <div>
            <div class="font-bold text-2xl md:text-3xl">{getFullName(user)}</div>
            <div class="text-gray-500 text-sm md:text-base">{user.username}</div>
        </div>
        <div class="flex flex-row gap-3 flex-wrap items-center text-sm md:text-base text-gray-600">
            <div class="flex items-center gap-2">
                <img src={roleIcon} alt="Роль" class="w-4 h-4 md:w-5 md:h-5" />
                <span>{capitalizeFirstLetter(user.role)}</span>
            </div>
            <div class="flex items-center gap-2">
                <img src={userIcon} alt="Идентификатор" class="w-4 h-4 md:w-5 md:h-5" />
                <span>ID: {user.id}</span>
            </div>
            {#if user.building}
                <div class="flex items-center gap-2">
                    <img src={buildingIcon} alt="Корпус" class="w-4 h-4 md:w-5 md:h-5" />
                    <span>{user.building}</span>
                </div>
            {/if}
            {#if user.department}
                <div class="flex items-center gap-2">
                    <img src={roleIcon} alt="Отдел" class="w-4 h-4 md:w-5 md:h-5" />
                    <span>{user.department}</span>
                </div>
            {/if}
        </div>
    </div>
    {#if onEdit || onDelete}
        <div class="flex flex-row md:flex-col gap-2 md:justify-between md:items-end md:w-48">
            {#if onEdit}
                <button
                    onclick={onEdit}
                    class="bg-[#1357ff] hover:bg-[#0f49d6] text-white rounded-2xl px-4 py-2 transition-colors font-medium"
                >
                    Редактировать
                </button>
            {/if}
            {#if onDelete}
                <button
                    onclick={onDelete}
                    class="bg-red-500 hover:bg-red-600 text-white rounded-2xl px-4 py-2 transition-colors font-medium"
                >
                    Удалить
                </button>
            {/if}
        </div>
    {/if}
</div>
