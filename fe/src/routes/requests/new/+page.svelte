<script lang="ts">
    import Button from "$lib/components/controls/Button.svelte";
    import Entry from "$lib/components/controls/Entry.svelte";
    import Dropdown from "$lib/components/controls/Dropdown.svelte";
    import Toggle from "$lib/components/controls/Toggle.svelte";
    import {toast} from "$lib/stores/toast";
    import { Department, Building, api, Role } from "$lib/api";
    import { onMount } from "svelte";
    import { currentUser } from "$lib/stores/auth";
    import { goto } from "$app/navigation";
    import BackButton from "$lib/components/ui/BackButton.svelte";

    let title = $state('');
    let description = $state('');
    let department = $state<Department>(Department.Maintenance); 
    let building = $state<Building>(Building.Millionschikova);
    let urgent = $state(false);
    let photos = $state<File[]>([]);
    let photoPreviewUrls = $state<string[]>([]);
    let isAdmin = $state(false);
    let userRole = $state<Role | null>(null);
    let isSubmitting = $state(false);

    const handleFileInput = (event: Event) => {
        const target = event.target as HTMLInputElement;
        if (target.files) {
            const newFiles = Array.from(target.files);
            photos = [...photos, ...newFiles];
            
            
            newFiles.forEach(file => {
                const url = URL.createObjectURL(file);
                photoPreviewUrls = [...photoPreviewUrls, url];
            });
        }
    };

    const removePhoto = (index: number) => {
        
        URL.revokeObjectURL(photoPreviewUrls[index]);
        
        photos = photos.filter((_, i) => i !== index);
        photoPreviewUrls = photoPreviewUrls.filter((_, i) => i !== index);
    };

    const handleSubmit = async () => {
        if (isSubmitting) {
            return;
        }

        if (!title) {
            toast.error('Введите заголовок');
            return;
        }
        
        isSubmitting = true;
        try {
            const formData = new FormData();
            formData.append('title', title);
            if (description) formData.append('description', description);
            formData.append('building', building);
            formData.append('department', department);
            formData.append('urgent', urgent.toString());
            
            
            photos.forEach((photo) => {
                formData.append('photos', photo);
            });

            await api.createRequest(formData);
            
            
            photoPreviewUrls.forEach(url => URL.revokeObjectURL(url));
            toast.success('Заявка успешно создана');
            goto('/requests');
            
            
            title = '';
            description = '';
            department = Department.Maintenance;
            urgent = false;
            photos = [];
            photoPreviewUrls = [];
        } catch (error) {
            console.error('Failed to create request:', error);
            toast.error('Ошибка при создании заявки');
            isSubmitting = false;
        }
    };

    
    onMount(() => {
        
        const unsubscribe = currentUser.subscribe(user => {
            if (user) {
                userRole = user.role;
                isAdmin = user.role === Role.Admin;
                
                if (user.role === Role.HeadOfDepartment && user.building) {
                    building = user.building as Building;
                }
            }
        });

        return () => {
            photoPreviewUrls.forEach(url => URL.revokeObjectURL(url));
            unsubscribe();
        };
    });
</script>

<div class="flex flex-col gap-2 max-w-2xl mx-auto p-4">
    <BackButton />
    <Entry bind:value={title} placeholder="Опишите проблему" disabled={isSubmitting}/>
    
    {#if isAdmin}
        <Dropdown
            bind:value={building}
            options={[
                { label: 'Миллионщикова', value: Building.Millionschikova },
                { label: 'Коломенская', value: Building.Kolomenskaya },
                { label: 'Судостроительная', value: Building.Sudostroitelnaya },
                { label: 'Харьковский', value: Building.Kharkovskiy },
            ]}
            placeholder="Выберите корпус"
            disabled={isSubmitting}
        />
    {/if}
    
    <Dropdown
        bind:value={department}
        options={[
        { label: 'АХЧ', value: Department.Maintenance },{label: 'IT', value: Department.IT}
        ]}
        placeholder="Выберите отдел"
        disabled={isSubmitting}
    />

    <div class="flex items-center gap-3">
        <Toggle bind:checked={urgent} disabled={isSubmitting} />
        <span class="text-lg">Срочная заявка</span>
    </div>

    <div class="border-2 border-gray-200 rounded p-4">
        <h3 class="text-xl font-semibold mb-2">Фотографии</h3>
        
        <label class="cursor-pointer block">
            <div class="bg-[#1357ff] hover:bg-[#0f49d6] text-white rounded-2xl px-5 py-3 transition-colors ">
                📷 Прикрепить фото
            </div>
            <input 
                type="file" 
                accept="image/*" 
                multiple 
                capture="environment"
                class="hidden" 
                onchange={handleFileInput}
                disabled={isSubmitting}
            />
        </label>

        {#if photoPreviewUrls.length > 0}
            <div class="mt-4">
                <p class="font-semibold mb-2">Прикрепленные фото ({photoPreviewUrls.length}):</p>
                <div class="grid grid-cols-3 gap-2">
                    {#each photoPreviewUrls as photoUrl, index}
                        <div class="relative">
                            <img src={photoUrl} alt="Preview {index + 1}" class="w-full h-32 object-cover rounded border" />
                            <button 
                                onclick={() => removePhoto(index)}
                                class="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
                            >
                                ×
                            </button>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
        <Entry bind:value={description} placeholder="Комментарий" disabled={isSubmitting} className="mt-2"/>

    </div>

    <Button onclick={handleSubmit} disabled={isSubmitting}>
        {isSubmitting ? 'Создание...' : 'Создать заявку'}
    </Button>
</div>

