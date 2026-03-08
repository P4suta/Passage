import { getMockSearchResponse } from "./mock-data.js";
import type { SearchResponse } from "./types.js";

const API_BASE = import.meta.env.PUBLIC_API_URL;

export async function searchPassages(
	query: string,
	limit = 10,
	apiBase?: string,
): Promise<SearchResponse> {
	const base = apiBase ?? API_BASE;

	if (!base) {
		return getMockSearchResponse(query);
	}

	const url = new URL("/api/search", base);
	url.searchParams.set("q", query);
	url.searchParams.set("limit", String(limit));

	const res = await fetch(url.toString());
	if (!res.ok) {
		throw new Error(`Search failed: HTTP ${res.status}`);
	}

	return res.json();
}
