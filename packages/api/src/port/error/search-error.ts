export class SearchError extends Error {
	constructor(
		message: string,
		public readonly code: SearchErrorCode,
		public readonly cause?: unknown,
	) {
		super(message);
		this.name = "SearchError";
	}
}

export type SearchErrorCode =
	| "EMBEDDING_FAILED"
	| "VECTOR_SEARCH_FAILED"
	| "CACHE_ERROR"
	| "STORAGE_ERROR"
	| "RATE_LIMITED"
	| "VALIDATION_ERROR";
