import { beforeEach, describe, expect, it, vi } from "vitest";
import { SearchApiError, searchPassages } from "../lib/api.js";

describe("searchPassages", () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it("returns mock data when no apiBase is configured", async () => {
		const result = await searchPassages("test query");
		expect(result.query).toBe("test query");
		expect(result.results.length).toBeGreaterThan(0);
	});

	it("constructs URL correctly with apiBase", async () => {
		const mockResponse = { results: [], count: 0, query: "test" };
		globalThis.fetch = vi.fn().mockResolvedValue({
			ok: true,
			json: () => Promise.resolve(mockResponse),
		});

		const result = await searchPassages("lonely night", 5, {
			apiBase: "http://localhost:8787",
		});
		expect(globalThis.fetch).toHaveBeenCalledWith(
			"http://localhost:8787/api/search?q=lonely+night&limit=5",
			{ signal: undefined },
		);
		expect(result).toEqual(mockResponse);
	});

	it("throws on HTTP error", async () => {
		globalThis.fetch = vi.fn().mockResolvedValue({
			ok: false,
			status: 500,
		});

		await expect(searchPassages("test", 10, { apiBase: "http://localhost:8787" })).rejects.toThrow(
			"HTTP 500",
		);
	});

	it("throws SearchApiError with retryAfter on 429", async () => {
		globalThis.fetch = vi.fn().mockResolvedValue({
			ok: false,
			status: 429,
			json: () => Promise.resolve({ retryAfter: 30 }),
		});

		try {
			await searchPassages("test", 10, { apiBase: "http://localhost:8787" });
			expect.fail("should have thrown");
		} catch (e) {
			expect(e).toBeInstanceOf(SearchApiError);
			expect((e as SearchApiError).status).toBe(429);
			expect((e as SearchApiError).retryAfter).toBe(30);
		}
	});

	it("throws SearchApiError on 429 even if body parse fails", async () => {
		globalThis.fetch = vi.fn().mockResolvedValue({
			ok: false,
			status: 429,
			json: () => Promise.reject(new Error("invalid json")),
		});

		try {
			await searchPassages("test", 10, { apiBase: "http://localhost:8787" });
			expect.fail("should have thrown");
		} catch (e) {
			expect(e).toBeInstanceOf(SearchApiError);
			expect((e as SearchApiError).status).toBe(429);
			expect((e as SearchApiError).retryAfter).toBeUndefined();
		}
	});
});
