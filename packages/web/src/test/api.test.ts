import { beforeEach, describe, expect, it, vi } from "vitest";
import { searchPassages } from "../lib/api.js";

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
});
