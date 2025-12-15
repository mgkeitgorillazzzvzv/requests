<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, Building, Department, buildingOptions, departmentOptions } from '$lib/api';
	import { normalizeBuilding } from '$lib/util';
	import Button from '$lib/components/controls/Button.svelte';
	import Entry from '$lib/components/controls/Entry.svelte';
	import Dropdown from '$lib/components/controls/Dropdown.svelte';
	import { showToast } from '$lib/stores/toast';
	import { isAuthenticated } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import { isPWA } from '$lib';
	let title = $state('');
	let description = $state('');
	let building = $state<Building>(Building.Millionschikova);
	let department = $state<Department>(Department.Maintenance);
	let photos = $state<File[]>([]);
	let photoPreviewUrls = $state<string[]>([]);
	let isSubmitting = $state(false);
	
	onMount(() => {
		if ($isAuthenticated || isPWA()) {
			goto('/requests', { replaceState: true });
		}
		
		const savedBuilding = normalizeBuilding(localStorage.getItem('selectedBuilding'));
		const savedDepartment = localStorage.getItem('selectedDepartment');
		
		if (savedBuilding && Object.values(Building).includes(savedBuilding as Building)) {
			building = savedBuilding as Building;
		}
		
		if (savedDepartment && Object.values(Department).includes(savedDepartment as Department)) {
			department = savedDepartment as Department;
		}
	});
	
	$effect(() => {
		if (building) {
			localStorage.setItem('selectedBuilding', building);
		}
	});
	
	$effect(() => {
		if (department) {
			localStorage.setItem('selectedDepartment', department);
		}
	});
	
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
		if (!title.trim()) {
			showToast('Введите название заявки', 'error');
			return;
		}
		
		if (!building) {
			showToast('Выберите корпус', 'error');
			return;
		}
		
		isSubmitting = true;
		
		try {
			const formData = new FormData();
			formData.append('title', title);
			formData.append('description', description);
			formData.append('building', building);
			formData.append('department', department);
			
			photos.forEach((photo) => {
				formData.append('photos', photo);
			});
			
			await api.createAnonymousRequest(formData);
			
			showToast('Спасибо за сообщение о проблеме!', 'success');
			
			title = '';
			description = '';
			building = Building.Millionschikova;
			department = Department.Maintenance;
			photos = [];
			photoPreviewUrls.forEach(url => URL.revokeObjectURL(url));
			photoPreviewUrls = [];
			
		} catch (error) {
			console.error('Failed to create anonymous request:', error);
			showToast('Ошибка при создании заявки', 'error');
		} finally {
			isSubmitting = false;
		}
	};
</script>

<div class="min-h-screen flex items-center justify-center p-4">
	<div class="max-w-2xl w-full">
		<div class="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
			<div class="text-center mb-8">
				<h1 class="text-3xl md:text-4xl font-bold text-gray-800 mb-3">
					Сообщить о проблеме
				</h1>

			</div>
			
			<div class="space-y-6">
				<div>
					<label for="title" class="block text-sm font-medium text-gray-700 mb-2">
						Название заявки <span class="text-red-500">*</span>
					</label>
					<Entry
						id="title"
						bind:value={title}
						placeholder="Краткое описание проблемы"
						required
						disabled={isSubmitting}
					/>
				</div>
				
				<div>
					<label for="building" class="block text-sm font-medium text-gray-700 mb-2">
						Корпус <span class="text-red-500">*</span>
					</label>
					<Dropdown
						id="building"
						bind:value={building}
						options={buildingOptions}
						placeholder="Выберите корпус"
						disabled={isSubmitting}
					/>
				</div>
				
				<div>
					<label for="department" class="block text-sm font-medium text-gray-700 mb-2">
						Отдел <span class="text-red-500">*</span>
					</label>
					<Dropdown
						id="department"
						bind:value={department}
						options={departmentOptions}
						placeholder="Выберите отдел"
						disabled={isSubmitting}
					/>
				</div>
				
				<div class="border-2 border-gray-200 rounded-xl p-4">
					<h3 class="text-lg font-semibold mb-3">Фотографии</h3>
					
					<label class="cursor-pointer block">
						<div class="bg-[#1357ff] hover:bg-[#0f49d6] text-white rounded-xl px-5 py-3 transition-colors text-center font-medium">
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
											type="button"
											onclick={() => removePhoto(index)}
											class="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600"
											disabled={isSubmitting}
										>
											×
										</button>
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
				
				<div>
					<label for="description" class="block text-sm font-medium text-gray-700 mb-2">
						Комментарий
					</label>
					<Entry
						id="description"
						bind:value={description}
						placeholder="Дополнительная информация"
						disabled={isSubmitting}
					/>
				</div>
				
				<div class="flex flex-col gap-3 pt-4">
					<Button
						onclick={handleSubmit}
						disabled={isSubmitting}						
						class="w-full py-3 px-4 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-colors"

					>
						{isSubmitting ? 'Отправка...' : 'Отправить заявку'}
					</Button>
					
					<button
						type="button"
						onclick={() => goto('/login')}
						disabled={isSubmitting}
						class="w-full py-4 font-semibold"

					>
						Войти в систему
					</button>
				</div>
			</div>
		</div>
		
		<div class="text-center mt-6 text-gray-600">
			<p class="text-sm">
				После отправки ваша заявка будет рассмотрена администратором
			</p>
		</div>
	</div>
</div>

