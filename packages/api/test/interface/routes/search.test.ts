import { describe, expect, it, vi } from "vitest";
import { createApp } from "../../../src/interface/app.js";

function createTestDeps(results: any[] = []) {
	return {
		searchUseCase: {
			execute: vi.fn().mockResolvedValue(
				results.length > 0
					? results
					: [
							{
								passage: {
									passageId: "p1",
									text: "Some literary text",
									book: {
										bookId: "b1",
										title: "Great Book",
										author: "Author",
										year: 1900,
										language: "en",
									},
									chapter: "Chapter 1",
									chunkIndex: 0,
								},
								score: { value: 0.85 },
							},
						],
			),
		} as any,
		cache: {
			get: vi.fn().mockResolvedValue(null),
			set: vi.fn().mockResolvedValue(undefined),
			increment: vi.fn().mockResolvedValue(1),
		},
	};
}

describe("GET /api/search", () => {
	it("returns search results with correct shape", async () => {
		const deps = createTestDeps();
		const app = createApp(deps);
		const res = await app.request("/api/search?q=lonely+night");
		expect(res.status).toBe(200);

		const body = (await res.json()) as any;
		expect(body.results).toHaveLength(1);
		expect(body.count).toBe(1);
		expect(body.query).toBe("lonely night");
		expect(body.results[0]).toMatchObject({
			passageId: "p1",
			text: "Some literary text",
			book: { bookId: "b1", title: "Great Book" },
			score: 0.85,
		});
	});

	it("requires q parameter", async () => {
		const app = createApp(createTestDeps());
		const res = await app.request("/api/search");
		expect(res.status).toBe(400);
	});

	it("passes limit parameter to use case", async () => {
		const deps = createTestDeps();
		const app = createApp(deps);
		await app.request("/api/search?q=test&limit=5");
		expect(deps.searchUseCase.execute).toHaveBeenCalledWith({
			text: "test",
			limit: 5,
		});
	});
});
