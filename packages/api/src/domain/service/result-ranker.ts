import type { SearchResult } from "../model/search-result.js";
import { isRelevant } from "../model/search-result.js";

export class ResultRanker {
	filterByThreshold(results: readonly SearchResult[]): SearchResult[] {
		return results.filter((r) => isRelevant(r.score));
	}

	deduplicateByBook(results: readonly SearchResult[], maxPerBook = 3): SearchResult[] {
		const bookCounts = new Map<string, number>();
		const diversified: SearchResult[] = [];

		for (const result of results) {
			const bookId = result.passage.book.bookId;
			const count = bookCounts.get(bookId) ?? 0;

			if (count < maxPerBook) {
				diversified.push(result);
				bookCounts.set(bookId, count + 1);
			}
		}

		return diversified;
	}
}
