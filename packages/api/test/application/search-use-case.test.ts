import { describe, expect, it, vi } from "vitest";
import { SearchUseCase } from "../../src/application/search-use-case.js";
import { SearchQueryValidationError } from "../../src/domain/model/search-query.js";
import type { CachePort } from "../../src/port/cache-port.js";
import type { EmbeddingPort } from "../../src/port/embedding-port.js";
import type { VectorSearchPort } from "../../src/port/vector-search-port.js";
import { createTestVectorMatch } from "../helpers.js";

function createStubEmbedding(): EmbeddingPort {
	return {
		embed: vi.fn().mockResolvedValue(new Array(1024).fill(0.1)),
		embedBatch: vi.fn().mockResolvedValue([new Array(1024).fill(0.1)]),
	};
}

function createStubVectorSearch(matches = [createTestVectorMatch()]): VectorSearchPort {
	return {
		search: vi.fn().mockResolvedValue(matches),
	};
}

function createStubCache(): CachePort {
	const store = new Map<string, unknown>();
	return {
		get: vi.fn().mockResolvedValue(null),
		set: vi.fn().mockImplementation(async (key, value) => {
			store.set(key, value);
		}),
		increment: vi.fn().mockResolvedValue(1),
	};
}

describe("SearchUseCase", () => {
	it("returns search results for a valid query", async () => {
		const useCase = new SearchUseCase(
			createStubEmbedding(),
			createStubVectorSearch(),
			createStubCache(),
		);
		const results = await useCase.execute({ text: "lonely night" });
		expect(results.length).toBeGreaterThan(0);
		expect(results[0].passage.text).toBeTruthy();
		expect(results[0].score.value).toBeGreaterThan(0);
	});

	it("returns cached results on cache hit", async () => {
		const cachedResults = [
			{
				passage: {
					passageId: "cached-1",
					text: "cached text",
					book: {
						bookId: "b1",
						title: "T",
						author: "A",
						year: 1900,
						language: "en",
					},
					chapter: "Ch1",
					chunkIndex: 0,
				},
				score: { value: 0.9 },
			},
		];
		const cache = createStubCache();
		(cache.get as ReturnType<typeof vi.fn>).mockResolvedValue(cachedResults);

		const embedding = createStubEmbedding();
		const useCase = new SearchUseCase(embedding, createStubVectorSearch(), cache);

		const results = await useCase.execute({ text: "test query" });
		expect(results).toEqual(cachedResults);
		expect(embedding.embed).not.toHaveBeenCalled();
	});

	it("calls embedding and vector search on cache miss", async () => {
		const embedding = createStubEmbedding();
		const vectorSearch = createStubVectorSearch();
		const cache = createStubCache();

		const useCase = new SearchUseCase(embedding, vectorSearch, cache);
		await useCase.execute({ text: "test" });

		expect(embedding.embed).toHaveBeenCalledWith("test");
		expect(vectorSearch.search).toHaveBeenCalled();
	});

	it("uses fetchSize = limit * 3 (max 50)", async () => {
		const vectorSearch = createStubVectorSearch();
		const useCase = new SearchUseCase(createStubEmbedding(), vectorSearch, createStubCache());

		await useCase.execute({ text: "test", limit: 10 });
		expect(vectorSearch.search).toHaveBeenCalledWith(expect.any(Array), 30);

		await useCase.execute({ text: "test2", limit: 20 });
		expect(vectorSearch.search).toHaveBeenCalledWith(expect.any(Array), 50);
	});

	it("filters by relevance threshold", async () => {
		const matches = [
			createTestVectorMatch({ id: "1", score: 0.8 }),
			createTestVectorMatch({ id: "2", score: 0.1 }),
		];
		const useCase = new SearchUseCase(
			createStubEmbedding(),
			createStubVectorSearch(matches),
			createStubCache(),
		);

		const results = await useCase.execute({ text: "test" });
		expect(results).toHaveLength(1);
		expect(results[0].score.value).toBe(0.8);
	});

	it("applies diversity filter", async () => {
		const matches = Array.from({ length: 5 }, (_, i) =>
			createTestVectorMatch({
				id: `chunk-${i}`,
				score: 0.9 - i * 0.01,
				metadata: {
					text: `text ${i}`,
					bookId: "same-book",
					title: "Same Book",
					author: "Author",
					year: 1900,
					language: "en",
					chapter: "Ch1",
					chunkIndex: i,
				},
			}),
		);
		const useCase = new SearchUseCase(
			createStubEmbedding(),
			createStubVectorSearch(matches),
			createStubCache(),
		);

		const results = await useCase.execute({ text: "test" });
		expect(results.length).toBeLessThanOrEqual(3);
	});

	it("writes results to cache", async () => {
		const cache = createStubCache();
		const useCase = new SearchUseCase(createStubEmbedding(), createStubVectorSearch(), cache);

		await useCase.execute({ text: "test" });
		expect(cache.set).toHaveBeenCalled();
	});

	it("handles cache write failure gracefully", async () => {
		const cache = createStubCache();
		(cache.set as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("KV down"));

		const useCase = new SearchUseCase(createStubEmbedding(), createStubVectorSearch(), cache);

		const results = await useCase.execute({ text: "test" });
		expect(results.length).toBeGreaterThan(0);
	});

	it("throws SearchQueryValidationError for invalid query", async () => {
		const useCase = new SearchUseCase(
			createStubEmbedding(),
			createStubVectorSearch(),
			createStubCache(),
		);

		await expect(useCase.execute({ text: "" })).rejects.toThrow(SearchQueryValidationError);
	});
});
