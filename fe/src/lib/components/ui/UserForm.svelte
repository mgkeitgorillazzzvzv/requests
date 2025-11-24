<script lang="ts">
    import Button from "$lib/components/controls/Button.svelte";
    import Dropdown from "$lib/components/controls/Dropdown.svelte";
    import Entry from "$lib/components/controls/Entry.svelte";
    import { Building, Role, Department, type UserOut } from "$lib/api";
    import { capitalizeFirstLetter } from "$lib/util";
    import { toast } from "$lib/stores/toast";

    export interface UserFormValues {
        first_name: string;
        last_name: string;
        username: string;
        role: Role;
        building?: Building | null;
        department?: Department | null;
        password?: string;
    }

    interface Props {
        initialUser?: UserOut | null;
        submitLabel?: string;
        onSubmit: (values: UserFormValues) => Promise<void> | void;
        showPasswordField?: boolean;
        requirePassword?: boolean;
        isSubmitting?: boolean;
    }

    let {
        initialUser = null,
        submitLabel = 'Сохранить',
        onSubmit,
        showPasswordField = true,
        requirePassword = true,
        isSubmitting: externalIsSubmitting = false
    }: Props = $props();

    let firstName = $state(initialUser?.first_name ?? '');
    let lastName = $state(initialUser?.last_name ?? '');
    let username = $state(initialUser?.username ?? '');
    let role = $state<Role>(initialUser?.role ?? Role.Specialist);
    let building = $state<Building | ''>(initialUser?.building ?? Building.Millionschikova);
    let department = $state<Department>(initialUser?.department ? (initialUser.department as Department) : Department.Maintenance);
    let password = $state('');
    let internalIsSubmitting = $state(false);
    
    const isSubmitting = $derived(externalIsSubmitting || internalIsSubmitting);

    const roleOptions = Object.values(Role).map((value) => ({ label: capitalizeFirstLetter(value), value }));
    const buildingOptions = Object.values(Building).map((value) => ({ label: value, value }));
    
    
    const departmentOptions = [
        { label: 'АХЧ', value: Department.Maintenance }
    ];

    
    const showDepartmentField = $derived(role !== Role.Admin && role !== Role.HeadOfDepartment);

    $effect(() => {
        if (initialUser) {
            firstName = initialUser.first_name;
            lastName = initialUser.last_name;
            username = initialUser.username;
            role = initialUser.role;
            building = initialUser.building ?? Building.Millionschikova;
            department = initialUser.department ? (initialUser.department as Department) : Department.Maintenance;
            password = '';
        }
    });

    const handleSubmit = async () => {
        if (isSubmitting) {
            return;
        }

        if (!firstName.trim()) {
            toast.error('Введите имя');
            return;
        }

        if (!lastName.trim()) {
            toast.error('Введите фамилию');
            return;
        }

        if (!username.trim()) {
            toast.error('Введите логин');
            return;
        }

        if (!role) {
            toast.error('Выберите роль');
            return;
        }

        if (showDepartmentField && !department) {
            toast.error('Выберите отдел');
            return;
        }

        if (showPasswordField && requirePassword && !password) {
            toast.error('Введите пароль');
            return;
        }

        const payload: UserFormValues = {
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            username: username.trim(),
            role,
            building: building || null,
            department: showDepartmentField ? department : undefined
        };

        if (showPasswordField && password) {
            payload.password = password;
        }

        internalIsSubmitting = true;
        try {
            await onSubmit(payload);
        } finally {
            internalIsSubmitting = false;
        }
    };
</script>

<div class="flex flex-col gap-4">
    <Entry
        bind:value={firstName}
        placeholder="Имя"
        aria-label="Имя"
        disabled={isSubmitting}
    />
    <Entry
        bind:value={lastName}
        placeholder="Фамилия"
        aria-label="Фамилия"
        disabled={isSubmitting}
    />
    <Entry 
        bind:value={username} 
        placeholder="Логин" 
        aria-label="Логин"
        disabled={isSubmitting}
    />
    <Dropdown
        bind:value={role}
        options={roleOptions}
        placeholder="Выберите роль"
        aria-label="Роль"
        disabled={isSubmitting}
    />
    <Dropdown
        bind:value={building}
        options={buildingOptions}
        placeholder="Выберите корпус"
        aria-label="Корпус"
        disabled={isSubmitting}
    />

    {#if showDepartmentField}
        <Dropdown
            bind:value={department}
            options={departmentOptions}
            placeholder="Выберите отдел"
            aria-label="Отдел"
            disabled={isSubmitting}
        />
    {/if}

    {#if showPasswordField}
        <div class="flex flex-col gap-1">
            <Entry
                bind:value={password}
                type="password"
                placeholder={requirePassword ? 'Пароль' : 'Новый пароль (необязательно)'}
                aria-label="Пароль"
                disabled={isSubmitting}
            />
            {#if !requirePassword}
                <p class="text-sm text-gray-500">Оставьте поле пустым, чтобы сохранить текущий пароль.</p>
            {/if}
        </div>
    {/if}

    <Button onclick={handleSubmit} disabled={isSubmitting}>
        {isSubmitting ? 'Сохранение...' : submitLabel}
    </Button>
</div>
