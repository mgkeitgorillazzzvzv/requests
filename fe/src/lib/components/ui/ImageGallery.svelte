<script lang="ts">
    import type { PhotoOut } from "$lib/api";
    import { api } from "$lib/api";
    import { onDestroy } from 'svelte';

    interface Props {
        photos: PhotoOut[];
    }

    let { photos }: Props = $props();
    let selectedIndex = $state<number | null>(null);

    
    let photoUrls: Record<number, string | null> = $state({});

    
    const preload = async () => {
        for (const photo of photos) {
            if (!photoUrls[photo.id]) {
                try {
                    const blob = await api.getPhotoFile(photo.id);
                    photoUrls[photo.id] = URL.createObjectURL(blob);
                } catch (err) {
                    console.error('Failed to load photo', photo.id, err);
                    photoUrls[photo.id] = null;
                }
            }
        }
    };

    preload();

    onDestroy(() => {
        for (const idStr in photoUrls) {
            const url = photoUrls[idStr];
            if (url) URL.revokeObjectURL(url);
        }
    });

    const handlePrevious = () => {
        if (selectedIndex !== null && selectedIndex > 0) {
            selectedIndex--;
        }
    };

    const handleNext = () => {
        if (selectedIndex !== null && selectedIndex < photos.length - 1) {
            selectedIndex++;
        }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
        if (selectedIndex === null) return;
        
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            handlePrevious();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            handleNext();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            selectedIndex = null;
        }
    };

    const handleBackdropClick = () => {
        selectedIndex = null;
    };
</script>

<svelte:window onkeydown={handleKeyDown} />

<div class="grid grid-cols-3 gap-2">
    {#each photos as photo, index}
        <button
            onclick={() => (selectedIndex = index)}
            class="relative overflow-hidden rounded border border-gray-300 hover:border-[#1357ff] transition-colors cursor-pointer"
        >
            <img
                src={photoUrls[photo.id] ?? ''}
                alt=""
                class="w-full h-32 object-cover hover:scale-105 transition-transform"
            />
        </button>
    {/each}
</div>

{#if selectedIndex !== null}
    <div
        class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-in fade-in duration-200"
        role="presentation"
        onclick={handleBackdropClick}
    >
        <div class="relative w-full h-full flex items-center justify-center p-4">
            <!-- Close button -->
            <button
                onclick={() => (selectedIndex = null)}
                class="absolute top-4 right-4 text-white text-3xl hover:text-gray-300 transition-colors z-10"
                aria-label="Закрыть"
            >
                ✕
            </button>

            <!-- Main image -->
            <button
                onclick={(e) => e.stopPropagation()}
                class="max-w-full max-h-[85vh] object-contain animate-in zoom-in-95 duration-200 border-0 p-0 bg-transparent cursor-default"
                aria-label="Full size image"
            >
                <img
                    src={photoUrls[photos[selectedIndex].id] ?? ''}
                    alt=""
                    class="max-w-full max-h-[85vh] object-contain"
                />
            </button>

            <!-- Previous button -->
            {#if selectedIndex > 0}
                <button
                    onclick={(e) => {
                        e.stopPropagation();
                        handlePrevious();
                    }}
                    class="absolute left-4 text-white text-2xl hover:text-gray-300 transition-colors"
                    aria-label="Предыдущее изображение"
                >
                    ◀
                </button>
            {/if}

            <!-- Next button -->
            {#if selectedIndex < photos.length - 1}
                <button
                    onclick={(e) => {
                        e.stopPropagation();
                        handleNext();
                    }}
                    class="absolute right-4 text-white text-2xl hover:text-gray-300 transition-colors"
                    aria-label="Следующее изображение"
                >
                    ▶
                </button>
            {/if}

            <!-- Counter -->
            <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white text-sm">
                {selectedIndex + 1} / {photos.length}
            </div>
        </div>
    </div>
{/if}
