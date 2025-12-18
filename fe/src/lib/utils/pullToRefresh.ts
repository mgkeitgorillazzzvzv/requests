
const PULL_THRESHOLD = 80;

export interface PullToRefreshState {
	pullProgress: number;
	isPulling: boolean;
	touchStartY: number;
}

export interface PullToRefreshHandlers {
	handleTouchStart: (e: TouchEvent) => void;
	handleTouchMove: (e: TouchEvent) => void;
	handleTouchEnd: () => void;
}

export function createPullToRefresh(
	state: PullToRefreshState,
	getIsLoading: () => boolean,
	onRefresh: () => void | Promise<void>
): PullToRefreshHandlers {
	const handleTouchStart = (e: TouchEvent) => {
		const scrollTop = document.documentElement.scrollTop || window.scrollY || document.body.scrollTop;
		if (scrollTop !== 0) return;
		state.touchStartY = e.touches[0].clientY;
	};

	const handleTouchMove = (e: TouchEvent) => {
		const scrollTop = document.documentElement.scrollTop || window.scrollY || document.body.scrollTop;
		if (scrollTop !== 0) return;

		const touchCurrentY = e.touches[0].clientY;
		const diff = touchCurrentY - state.touchStartY;

		if (diff > 0 && !getIsLoading()) {
			if (e.cancelable) {
				e.preventDefault();
			}
			state.isPulling = true;
			state.pullProgress = Math.min(diff, PULL_THRESHOLD);
		}
	};

	const handleTouchEnd = () => {
		if (state.pullProgress >= PULL_THRESHOLD && !getIsLoading()) {
			onRefresh();
		}
		state.pullProgress = 0;
		state.isPulling = false;
	};

	return {
		handleTouchStart,
		handleTouchMove,
		handleTouchEnd
	};
}


export function attachPullToRefresh(handlers: PullToRefreshHandlers): () => void {
	const touchMoveOptions: AddEventListenerOptions = { passive: false };

	document.addEventListener('touchstart', handlers.handleTouchStart);
	document.addEventListener('touchmove', handlers.handleTouchMove, touchMoveOptions);
	document.addEventListener('touchend', handlers.handleTouchEnd);

	return () => {
		document.removeEventListener('touchstart', handlers.handleTouchStart);
		document.removeEventListener('touchmove', handlers.handleTouchMove, touchMoveOptions);
		document.removeEventListener('touchend', handlers.handleTouchEnd);
	};
}

export { PULL_THRESHOLD };
