import { describe, expect, it } from "vitest";
import { ResultRanker } from "../../../src/domain/service/result-ranker.js";
import { createTestSearchResult } from "../../helpers.js";

const ranker = new ResultRanker();

describe("ResultRanker", () => {
	describe("filterByThreshold", () => {
		it("keeps results with score >= 0.3", () => {
			const results = [
				createTestSearchResult({ score: 0.8 }),
				createTestSearchResult({ score: 0.5 }),
				createTestSearchResult({ score: 0.3 }),
			];
			expect(ranker.filterByThreshold(results)).toHaveLength(3);
		});

		it("removes results with score < 0.3", () => {
			const results = [
				createTestSearchResult({ score: 0.8 }),
				createTestSearchResult({ score: 0.2 }),
				createTestSearchResult({ score: 0.1 }),
			];
			expect(ranker.filterByThreshold(results)).toHaveLength(1);
		});

		it("returns empty array for empty input", () => {
			expect(ranker.filterByThreshold([])).toEqual([]);
		});
	});

	describe("deduplicateByBook", () => {
		it("limits results per book to maxPerBook", () => {
			const results = [
				createTestSearchResult({ passage: { bookId: "book-a" } as any, score: 0.9 }),
				createTestSearchResult({ passage: { bookId: "book-a" } as any, score: 0.85 }),
				createTestSearchResult({ passage: { bookId: "book-a" } as any, score: 0.8 }),
				createTestSearchResult({ passage: { bookId: "book-a" } as any, score: 0.75 }),
			].map((r, i) => ({
				...r,
				passage: {
					...r.passage,
					passageId: `chunk-${i}`,
					text: `text ${i}`,
					book: {
						bookId: "book-a",
						title: "Book A",
						author: "Author A",
						year: 1900,
						language: "en",
					},
					chapter: "Ch1",
					chunkIndex: i,
				},
			}));
			const deduped = ranker.deduplicateByBook(results, 3);
			expect(deduped).toHaveLength(3);
		});

		it("preserves order", () => {
			const results = [
				createTestSearchResult({ score: 0.9 }),
				createTestSearchResult({ score: 0.7 }),
			];
			const deduped = ranker.deduplicateByBook(results);
			expect(deduped[0].score.value).toBe(0.9);
			expect(deduped[1].score.value).toBe(0.7);
		});

		it("returns empty array for empty input", () => {
			expect(ranker.deduplicateByBook([])).toEqual([]);
		});
	});
});
