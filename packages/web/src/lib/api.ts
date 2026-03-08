import { getMockSearchResponse } from "./mock-data.js";
import type { SearchResponse } from "./types.js";

const API_BASE = import.meta.env.PUBLIC_API_URL;

export class SearchApiError extends Error {
	status: number;
	retryAfter?: number;

	constructor(status: number, retryAfter?: number) {
		const message =
			retryAfter != null
				? `Rate limited: retry after ${retryAfter}s`
				: `Search failed: HTTP ${status}`;
		super(message);
		this.name = "SearchApiError";
		this.status = status;
		this.retryAfter = retryAfter;
	}
}

export async function searchPassages(
	query: string,
	limit = 10,
	options?: { apiBase?: string; signal?: AbortSignal },
): Promise<SearchResponse> {
	const base = options?.apiBase ?? API_BASE;

	if (!base) {
		return getMockSearchResponse(query);
	}

	const url = new URL("/api/search", base);
	url.searchParams.set("q", query);
	url.searchParams.set("limit", String(limit));

	const res = await fetch(url.toString(), { signal: options?.signal });
	if (!res.ok) {
		if (res.status === 429) {
			let retryAfter: number | undefined;
			try {
				const body = await res.json();
				retryAfter = body.retryAfter;
			} catch {
				// ignore parse errors
			}
			throw new SearchApiError(429, retryAfter);
		}
		throw new SearchApiError(res.status);
	}

	return res.json();
}
