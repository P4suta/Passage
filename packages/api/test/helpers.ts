import type { BookMetadata } from "../src/domain/model/book-metadata.js";
import type { Passage } from "../src/domain/model/passage.js";
import type { SearchResult, SimilarityScore } from "../src/domain/model/search-result.js";
import type { VectorMatch } from "../src/port/vector-search-port.js";

export function createTestBookMetadata(overrides: Partial<BookMetadata> = {}): BookMetadata {
	return Object.freeze({
		bookId: "book-001",
		title: "Great Expectations",
		author: "Charles Dickens",
		year: 1861,
		language: "en",
		...overrides,
	});
}

export function createTestPassage(overrides: Partial<Passage> = {}): Passage {
	return Object.freeze({
		passageId: "chunk-001",
		text: "It was the best of times, it was the worst of times.",
		book: createTestBookMetadata(),
		chapter: "Chapter 1",
		chunkIndex: 0,
		...overrides,
	});
}

export function createTestSearchResult(
	overrides: { passage?: Partial<Passage>; score?: number } = {},
): SearchResult {
	return {
		passage: createTestPassage(overrides.passage),
		score: Object.freeze({ value: overrides.score ?? 0.8 }),
	};
}

export function createTestVectorMatch(overrides: Partial<VectorMatch> = {}): VectorMatch {
	return {
		id: "chunk-001",
		score: 0.85,
		metadata: {
			text: "It was the best of times.",
			bookId: "book-001",
			title: "A Tale of Two Cities",
			author: "Charles Dickens",
			year: 1859,
			language: "en",
			chapter: "Chapter 1",
			chunkIndex: 0,
		},
		...overrides,
	};
}
