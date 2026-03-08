import { describe, expect, it, vi } from "vitest";
import { SearchUseCase } from "../../src/application/search-use-case.js";
import type { CachePort } from "../../src/port/cache-port.js";
import type { EmbeddingPort } from "../../src/port/embedding-port.js";
import type { VectorSearchPort } from "../../src/port/vector-search-port.js";
import { createApp } from "../../src/interface/app.js";
import { createTestVectorMatch } from "../helpers.js";

/**
 * Contract tests verifying the API response matches the shape
 * expected by the web frontend (packages/web/src/lib/types.ts).
 *
 * Web frontend expects:
 *   SearchResponse { results: SearchResult[], count: number, query: string }
 *   SearchResult   { passageId: string, text: string, book: BookInfo, chapter: string, score: number }
 *   BookInfo       { bookId: string, title: string, author: string, year: number, language: string }
 */

function createFullStack(matches = [createTestVectorMatch()]) {
	const embedding: EmbeddingPort = {
		embed: vi.fn().mockResolvedValue(new Array(1024).fill(0.1)),
		embedBatch: vi.fn().mockResolvedValue([new Array(1024).fill(0.1)]),
	};
	const vectorSearch: VectorSearchPort = {
		search: vi.fn().mockResolvedValue(matches),
	};
	const cache: CachePort = {
		get: vi.fn().mockResolvedValue(null),
		set: vi.fn().mockResolvedValue(undefined),
		increment: vi.fn().mockResolvedValue(1),
	};

	const searchUseCase = new SearchUseCase(embedding, vectorSearch, cache);
	const app = createApp({ searchUseCase, cache });
	return { app, embedding, vectorSearch, cache };
}

describe("Search API contract", () => {
	it("response matches web frontend SearchResponse type", async () => {
		const { app } = createFullStack();
		const res = await app.request("/api/search?q=lonely+night");

		expect(res.status).toBe(200);
		expect(res.headers.get("content-type")).toContain("application/json");

		const body = (await res.json()) as any;

		// Top-level shape
		expect(body).toHaveProperty("results");
		expect(body).toHaveProperty("count");
		expect(body).toHaveProperty("query");
		expect(typeof body.count).toBe("number");
		expect(typeof body.query).toBe("string");
		expect(Array.isArray(body.results)).toBe(true);

		// SearchResult shape
		const result = body.results[0];
		expect(typeof result.passageId).toBe("string");
		expect(typeof result.text).toBe("string");
		expect(typeof result.chapter).toBe("string");
		expect(typeof result.score).toBe("number");

		// BookInfo shape
		expect(typeof result.book.bookId).toBe("string");
		expect(typeof result.book.title).toBe("string");
		expect(typeof result.book.author).toBe("string");
		expect(typeof result.book.year).toBe("number");
		expect(typeof result.book.language).toBe("string");
	});

	it("count matches results array length", async () => {
		const matches = [
			createTestVectorMatch({ id: "a", score: 0.9 }),
			createTestVectorMatch({
				id: "b",
				score: 0.8,
				metadata: {
					text: "Another passage",
					bookId: "book-002",
					title: "Other Book",
					author: "Other Author",
					year: 1920,
					language: "en",
					chapter: "Chapter 2",
					chunkIndex: 1,
				},
			}),
		];
		const { app } = createFullStack(matches);
		const res = await app.request("/api/search?q=test");
		const body = (await res.json()) as any;

		expect(body.count).toBe(body.results.length);
	});

	it("query field echoes back the input", async () => {
		const { app } = createFullStack();
		const res = await app.request("/api/search?q=the+ocean+was+quiet");
		const body = (await res.json()) as any;

		expect(body.query).toBe("the ocean was quiet");
	});

	it("respects limit parameter", async () => {
		const matches = Array.from({ length: 10 }, (_, i) =>
			createTestVectorMatch({
				id: `chunk-${i}`,
				score: 0.9 - i * 0.01,
				metadata: {
					text: `Passage text ${i}`,
					bookId: `book-${i}`,
					title: `Book ${i}`,
					author: `Author ${i}`,
					year: 1900 + i,
					language: "en",
					chapter: "Chapter 1",
					chunkIndex: 0,
				},
			}),
		);
		const { app } = createFullStack(matches);
		const res = await app.request("/api/search?q=test&limit=3");
		const body = (await res.json()) as any;

		expect(body.results.length).toBeLessThanOrEqual(3);
		expect(body.count).toBeLessThanOrEqual(3);
	});

	it("returns 400 for missing query parameter", async () => {
		const { app } = createFullStack();
		const res = await app.request("/api/search");
		expect(res.status).toBe(400);
	});

	it("filters low-relevance results", async () => {
		const matches = [
			createTestVectorMatch({ id: "high", score: 0.9 }),
			createTestVectorMatch({ id: "low", score: 0.1 }),
		];
		const { app } = createFullStack(matches);
		const res = await app.request("/api/search?q=test");
		const body = (await res.json()) as any;

		for (const result of body.results) {
			expect(result.score).toBeGreaterThanOrEqual(0.3);
		}
	});

	it("includes CORS headers for cross-origin requests", async () => {
		const { app } = createFullStack();
		const res = await app.request("/api/search?q=test", {
			headers: { Origin: "https://passage.pages.dev" },
		});

		expect(res.headers.get("Access-Control-Allow-Origin")).toBe("*");
	});
});
