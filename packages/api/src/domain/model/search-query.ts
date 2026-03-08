export interface SearchQuery {
	readonly text: string;
	readonly limit: number;
}

const MAX_QUERY_LENGTH = 500;
const MIN_LIMIT = 1;
const MAX_LIMIT = 20;
const DEFAULT_LIMIT = 10;

export function createSearchQuery(params: { text: string; limit?: number }): SearchQuery {
	const trimmed = params.text.trim();

	if (trimmed.length === 0) {
		throw new SearchQueryValidationError("Search query must not be empty");
	}
	if (trimmed.length > MAX_QUERY_LENGTH) {
		throw new SearchQueryValidationError(
			`Search query must not exceed ${MAX_QUERY_LENGTH} characters`,
		);
	}

	const limit = params.limit ?? DEFAULT_LIMIT;
	if (limit < MIN_LIMIT || limit > MAX_LIMIT) {
		throw new SearchQueryValidationError(`Limit must be between ${MIN_LIMIT} and ${MAX_LIMIT}`);
	}

	return Object.freeze({ text: trimmed, limit });
}

export class SearchQueryValidationError extends Error {
	constructor(message: string) {
		super(message);
		this.name = "SearchQueryValidationError";
	}
}
