<script lang="ts">
    import type { PhotoOut } from "$lib/api";
    import { api } from "$lib/api";
    import { onDestroy } from 'svelte';

    interface Props {
        photos: PhotoOut[];
    }

    let { photos }: Props = $props();
    let selectedIndex = $state<number | null>(null);

    // Thumbnail URLs for grid view
    let thumbnailUrls: Record<number, string | null> = $state({});
    // Full resolution URLs
    let fullUrls: Record<number, string | null> = $state({});
    // Loading state for full images
    let fullImageLoading: Record<number, boolean> = $state({});

    // Load thumbnails first
    const loadThumbnails = async () => {
        for (const photo of photos) {
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

    // Load full resolution image for lightbox
    const loadFullImage = async (photoId: number) => {
        if (fullUrls[photoId]) return; // Already loaded
        
        fullImageLoading[photoId] = true;
        try {
            const blob = await api.getPhotoFile(photoId);
            fullUrls[photoId] = URL.createObjectURL(blob);
        } catch (err) {
            console.error('Failed to load full image', photoId, err);
            fullUrls[photoId] = null;
        } finally {
            fullImageLoading[photoId] = false;
        }
    };

    loadThumbnails();

    // When image is selected, start loading full resolution
    $effect(() => {
        if (selectedIndex !== null && photos[selectedIndex]) {
            loadFullImage(photos[selectedIndex].id);
        }
    });

    onDestroy(() => {
        for (const idStr in thumbnailUrls) {
            const url = thumbnailUrls[idStr];
            if (url) URL.revokeObjectURL(url);
        }
        for (const idStr in fullUrls) {
            const url = fullUrls[idStr];
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

    // Get the best available URL for the lightbox
    const getLightboxUrl = (photoId: number) => {
        return fullUrls[photoId] ?? thumbnailUrls[photoId] ?? '';
    };
</script>

<svelte:window onkeydown={handleKeyDown} />

<div class="grid grid-cols-3 gap-2">
    {#each photos as photo, index}
        <button
            onclick={() => (selectedIndex = index)}
            class="relative overflow-hidden rounded border border-gray-300 hover:border-[#1357ff] transition-colors cursor-pointer"
        >
            {#if thumbnailUrls[photo.id]}
                <img
                    src={thumbnailUrls[photo.id] ?? ''}
                    alt=""
                    class="w-full h-32 object-cover hover:scale-105 transition-transform"
                />
            {:else}
                <div class="w-full h-32 bg-gray-200 animate-pulse flex items-center justify-center">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                </div>
            {/if}
        </button>
    {/each}
</div>

{#if selectedIndex !== null}
    {@const currentPhoto = photos[selectedIndex]}
    {@const isFullLoaded = !!fullUrls[currentPhoto.id]}
    {@const isLoading = fullImageLoading[currentPhoto.id]}
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

            <!-- Main image container -->
            <div
                role="button"
                tabindex="0"
                onclick={(e) => e.stopPropagation()}
                onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()}
                class="relative max-w-full max-h-[85vh] flex items-center justify-center"
            >
                <!-- Thumbnail shown as blur while full image loads -->
                <img
                    src={getLightboxUrl(currentPhoto.id)}
                    alt=""
                    class="max-w-full max-h-[85vh] object-contain animate-in zoom-in-95 duration-200 transition-all {!isFullLoaded ? 'blur-sm scale-[0.99]' : ''}"
                />
                
                <!-- Loading indicator -->
                {#if isLoading}
                    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div class="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
                    </div>
                {/if}
            </div>

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
