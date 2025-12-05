
export enum Building {
	Millionschikova = 'Миллионщикова',
	Kolomenskaya = 'Коломенская',
	Sudostroitelnaya = 'Судостроительная',
	Kharkovskiy = 'Харьковский'
}

export enum RequestStatus {
	Created = 'создано',
	PendingApproval = 'ожидает подтверждения',
	Completed = 'выполнено',
	Postponed = 'отложено',
	PendingCreationApproval = 'ожидает создания'
}

export enum Role {
	Admin = 'администратор',
	HeadOfDepartment = 'заведующий отделением',
	Specialist = 'специалист',
	Executor = 'исполнитель'
}

export enum Department {
    IT = 'IT',
    Maintenance = 'АХЧ',
}
export interface Token {
	access_token: string;
	token_type: string;
}

export interface UserOut {
	id: number;
	username: string;
	first_name: string;
	last_name: string;
	role: Role;
	building?: Building | null;
	department?: string | null;
}

export interface PhotoOut {
	id: number;
	file_path: string;
	caption?: string | null;
	order: number;
	uploaded_at: string;
}

export interface RequestHistoryOut {
	id: number;
	request_id: number;
	action: string;
	performed_by: UserOut;
	old_status?: RequestStatus | null;
	new_status?: RequestStatus | null;
	details?: string | null;
	created_at: string;
}

export interface StatusChangeRequestOut {
	id: number;
	request_id: number;
	requested_by: UserOut;
	requested_status: RequestStatus;
	reason?: string | null;
	photo?: PhotoOut | null;
	created_at: string;
	reviewed_at?: string | null;
	reviewed_by?: UserOut | null;
	approved?: boolean | null;
	rejection_reason?: string | null;
	rejection_photo?: PhotoOut | null;
}

export interface RequestOut {
	id: number;
	status: RequestStatus;
	title: string;
	description?: string | null;
	building: Building;
	opened_by?: UserOut | null;
	closed_by?: UserOut | null;
	opened_at: string;
	closed_at?: string | null;
	department?: string | null;
	urgent: boolean;
	is_anonymous: boolean;
	photos: PhotoOut[];
	history: RequestHistoryOut[];
	pending_status_changes: StatusChangeRequestOut[];
}

export interface PaginatedRequestsOut {
	items: RequestOut[];
	total: number;
	offset: number;
	limit: number;
	has_more: boolean;
}


export interface LoginRequest {
	username: string;
	password: string;
}

export interface CreateUserRequest {
	username: string;
	password: string;
	first_name: string;
	last_name: string;
	role: Role;
	building?: Building | null;
	department?: string | null;
}

export interface UpdateUserRequest {
	username?: string;
	password?: string;
	first_name?: string;
	last_name?: string;
	role?: Role;
	building?: Building | null;
	department?: string | null;
}

export interface CreateRequestRequest {
	title: string;
	description?: string | null;
	building: Building;
	department?: string | null;
	status?: RequestStatus;
	urgent?: boolean;
}

export interface CreateAnonymousRequestRequest {
	title: string;
	description?: string | null;
	building: Building;
	department?: string | null;
}

export interface UpdateRequestRequest {
	title?: string | null;
	description?: string | null;
	building?: Building | null;
	department?: string | null;
	urgent?: boolean | null;
}

export interface UploadPhotoRequest {
	file: File;
	caption?: string | null;
	order?: number;
}

export interface CreateStatusChangeRequest {
	requested_status: RequestStatus;
	reason?: string | null;
	photo_id?: number | null;
}

export interface ReviewStatusChangeRequest {
	approved: boolean;
	rejection_reason?: string | null;
	rejection_photo_id?: number | null;
}

export interface StatsOut {
	total_requests: number;
	open_requests: number;
	closed_requests: number;
	ratio: number;
	avg_processing_time_hours: number;
}


class APIClient {
	private baseURL: string;
	private token: string | null = null;

	constructor(baseURL: string = 'http://localhost:8000') {
		this.baseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
	}

	setToken(token: string) {
		this.token = token;
	}

	clearToken() {
		this.token = null;
	}

	private async request<T>(
		path: string,
		options: RequestInit = {}
	): Promise<T> {
		const headers: Record<string, string> = {
			...(options.headers as Record<string, string>)
		};

		if (this.token) {
			headers['Authorization'] = `Bearer ${this.token}`;
		}

		if (!(options.body instanceof FormData)) {
			headers['Content-Type'] = 'application/json';
		}

		const response = await fetch(`${this.baseURL}${path}`, {
			...options,
			headers
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({}));
			throw new Error(error.detail || `HTTP error! status: ${response.status}`);
		}

		return response.json();
	}

	
	async login(data: LoginRequest): Promise<Token> {
		const formData = new URLSearchParams();
		formData.append('username', data.username);
		formData.append('password', data.password);

		const response = await fetch(`${this.baseURL}/users/login`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded'
			},
			body: formData
		});

		if (!response.ok) {
			throw new Error(`Login failed: ${response.status}`);
		}

		const token = await response.json();
		this.setToken(token.access_token);
		return token;
	}

	async listUsers(): Promise<UserOut[]> {
		return this.request<UserOut[]>('/users/');
	}

	async createUser(data: CreateUserRequest): Promise<UserOut> {
		return this.request<UserOut>('/users/', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async updateUser(userId: number, data: UpdateUserRequest): Promise<UserOut> {
		return this.request<UserOut>(`/users/${userId}`, {
			method: 'PATCH',
			body: JSON.stringify(data)
		});
	}

	async getCurrentUser(): Promise<UserOut> {
		return this.request<UserOut>('/users/me');
	}

	async getUser(userId: number): Promise<UserOut> {
		return this.request<UserOut>(`/users/${userId}`);
	}

	async deleteUser(userId: number): Promise<void> {
		return this.request<void>(`/users/${userId}`, {
			method: 'DELETE'
		});
	}

	
	async createRequest(data: CreateRequestRequest | FormData): Promise<RequestOut> {
		if (data instanceof FormData) {
			const headers: Record<string, string> = {};
			if (this.token) {
				headers['Authorization'] = `Bearer ${this.token}`;
			}

			const response = await fetch(`${this.baseURL}/requests/`, {
				method: 'POST',
				headers,
				body: data
			});

			if (!response.ok) {
				const error = await response.json().catch(() => ({}));
				throw new Error(error.detail || `HTTP error! status: ${response.status}`);
			}

			return response.json();
		} else {
			return this.request<RequestOut>('/requests/', {
				method: 'POST',
				body: JSON.stringify(data)
			});
		}
	}

	async listRequests(options?: {
		building?: Building | null;
		status?: RequestStatus | null;
		search?: string | null;
		offset?: number;
		limit?: number;
	}): Promise<PaginatedRequestsOut> {
		const params = new URLSearchParams();
		if (options?.building) params.append('building', options.building);
		if (options?.status) params.append('status', options.status);
		if (options?.search) params.append('search', options.search);
		if (options?.offset !== undefined) params.append('offset', options.offset.toString());
		if (options?.limit !== undefined) params.append('limit', options.limit.toString());
		const queryString = params.toString();
		return this.request<PaginatedRequestsOut>(`/requests/${queryString ? '?' + queryString : ''}`);
	}

	async getRequest(requestId: number): Promise<RequestOut> {
		return this.request<RequestOut>(`/requests/${requestId}`);
	}

	async deleteRequest(requestId: number): Promise<void> {
		return this.request<void>(`/requests/${requestId}`, {
			method: 'DELETE'
		});
	}

	async updateRequest(
		requestId: number,
		data: UpdateRequestRequest
	): Promise<RequestOut> {
		return this.request<RequestOut>(`/requests/${requestId}`, {
			method: 'PATCH',
			body: JSON.stringify(data)
		});
	}

	async updateRequestStatus(
		requestId: number,
		status: RequestStatus
	): Promise<RequestOut> {
		return this.request<RequestOut>(
			`/requests/${requestId}/status?status=${encodeURIComponent(status)}`,
			{
				method: 'PUT'
			}
		);
	}

	
	async uploadPhoto(
		requestId: number,
		data: UploadPhotoRequest
	): Promise<PhotoOut> {
		const formData = new FormData();
		formData.append('file', data.file);
		if (data.caption) {
			formData.append('caption', data.caption);
		}
		if (data.order !== undefined) {
			formData.append('order', data.order.toString());
		}

		const headers: Record<string, string> = {};
		if (this.token) {
			headers['Authorization'] = `Bearer ${this.token}`;
		}

		const response = await fetch(
			`${this.baseURL}/requests/${requestId}/photos`,
			{
				method: 'POST',
				headers,
				body: formData
			}
		);

		if (!response.ok) {
			throw new Error(`Upload failed: ${response.status}`);
		}

		return response.json();
	}

	async getRequestPhotos(requestId: number): Promise<PhotoOut[]> {
		return this.request<PhotoOut[]>(`/requests/${requestId}/photos`);
	}

	async getPhotoFile(photoId: number): Promise<Blob> {
		const headers: Record<string, string> = {};
		if (this.token) {
			headers['Authorization'] = `Bearer ${this.token}`;
		}

		const response = await fetch(
			`${this.baseURL}/requests/photos/${photoId}/file`,
			{ headers }
		);

		if (!response.ok) {
			throw new Error(`Failed to fetch photo: ${response.status}`);
		}

		return response.blob();
	}

	async getPhotoThumbnail(photoId: number, size: number = 200): Promise<Blob> {
		const headers: Record<string, string> = {};
		if (this.token) {
			headers['Authorization'] = `Bearer ${this.token}`;
		}

		const response = await fetch(
			`${this.baseURL}/requests/photos/${photoId}/thumbnail?size=${size}`,
			{ headers }
		);

		if (!response.ok) {
			throw new Error(`Failed to fetch thumbnail: ${response.status}`);
		}

		return response.blob();
	}

	async deletePhoto(photoId: number): Promise<void> {
		return this.request<void>(`/requests/photos/${photoId}`, {
			method: 'DELETE'
		});
	}

	
	async createStatusChangeRequest(
		requestId: number,
		data: CreateStatusChangeRequest
	): Promise<StatusChangeRequestOut> {
		return this.request<StatusChangeRequestOut>(
			`/requests/${requestId}/status-change-request`,
			{
				method: 'POST',
				body: JSON.stringify(data)
			}
		);
	}

	async reviewStatusChangeRequest(
		requestId: number,
		changeRequestId: number,
		data: ReviewStatusChangeRequest
	): Promise<RequestOut> {
		return this.request<RequestOut>(
			`/requests/${requestId}/status-change-request/${changeRequestId}/review`,
			{
				method: 'POST',
				body: JSON.stringify(data)
			}
		);
	}

	async returnPostponedToWork(requestId: number): Promise<RequestOut> {
		return this.request<RequestOut>(
			`/requests/${requestId}/return-to-work`,
			{
				method: 'POST'
			}
		);
	}

	// Anonymous Requests
	async createAnonymousRequest(data: CreateAnonymousRequestRequest | FormData): Promise<RequestOut> {
		if (data instanceof FormData) {
			const response = await fetch(`${this.baseURL}/requests/anonymous`, {
				method: 'POST',
				body: data
			});

			if (!response.ok) {
				const error = await response.json().catch(() => ({}));
				throw new Error(error.detail || `HTTP error! status: ${response.status}`);
			}

			return response.json();
		} else {
			// Без токена для анонимных запросов
			const response = await fetch(`${this.baseURL}/requests/anonymous`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(data)
			});

			if (!response.ok) {
				const error = await response.json().catch(() => ({}));
				throw new Error(error.detail || `HTTP error! status: ${response.status}`);
			}

			return response.json();
		}
	}

	async approveAnonymousRequest(requestId: number): Promise<RequestOut> {
		return this.request<RequestOut>(
			`/requests/${requestId}/approve-anonymous`,
			{
				method: 'POST'
			}
		);
	}

	
	async getStats(
		building?: Building | null,
		department?: Department | null,
		period: 'day' | 'week' | 'month' = 'month'
	): Promise<StatsOut> {
		const params = new URLSearchParams();
		if (building) params.append('building', building);
		if (department) params.append('department', department);
		params.append('period', period);

		return this.request<StatsOut>(`/stats/?${params.toString()}`);
	}
}


export const api = new APIClient(import.meta.env.VITE_API_URL || 'http://localhost:8000');
