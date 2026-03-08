import { describe, expect, it, vi } from "vitest";
import { VectorizeSearchAdapter } from "../../src/infrastructure/vectorize-search-adapter.js";
import { SearchError } from "../../src/port/error/search-error.js";

function createMockIndex(
	matches: Array<{ id: string; score: number; metadata?: Record<string, unknown> }> = [],
) {
	return {
		query: vi.fn().mockResolvedValue({ matches }),
	} as unknown as VectorizeIndex;
}

describe("VectorizeSearchAdapter", () => {
	it("returns mapped results", async () => {
		const index = createMockIndex([
			{
				id: "chunk-1",
				score: 0.9,
				metadata: { text: "hello", bookId: "b1", title: "T", author: "A" },
			},
		]);
		const adapter = new VectorizeSearchAdapter(index);
		const results = await adapter.search([0.1], 10);

		expect(results).toHaveLength(1);
		expect(results[0].id).toBe("chunk-1");
		expect(results[0].score).toBe(0.9);
		expect(results[0].metadata.text).toBe("hello");
	});

	it("passes topK and returnMetadata options", async () => {
		const index = createMockIndex();
		const adapter = new VectorizeSearchAdapter(index);
		await adapter.search([0.1, 0.2], 5);

		expect(index.query).toHaveBeenCalledWith([0.1, 0.2], {
			topK: 5,
			returnMetadata: "all",
		});
	});

	it("handles missing score as 0", async () => {
		const index = createMockIndex([{ id: "chunk-1", score: undefined as unknown as number }]);
		const adapter = new VectorizeSearchAdapter(index);
		const results = await adapter.search([0.1], 1);
		expect(results[0].score).toBe(0);
	});

	it("throws SearchError on failure", async () => {
		const index = createMockIndex();
		(index.query as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("Vectorize down"));
		const adapter = new VectorizeSearchAdapter(index);
		await expect(adapter.search([0.1], 10)).rejects.toThrow(SearchError);
	});
});
