import { createBookMetadata } from "../domain/model/book-metadata.js";
import { createPassage } from "../domain/model/passage.js";
import { type SearchQuery, createSearchQuery } from "../domain/model/search-query.js";
import { type SearchResult, createSimilarityScore } from "../domain/model/search-result.js";
import { ResultRanker } from "../domain/service/result-ranker.js";
import type { CachePort } from "../port/cache-port.js";
import type { EmbeddingPort } from "../port/embedding-port.js";
import type { VectorSearchPort } from "../port/vector-search-port.js";

const CACHE_TTL_SECONDS = 3600;

export class SearchUseCase {
	private readonly ranker = new ResultRanker();

	constructor(
		private readonly embedding: EmbeddingPort,
		private readonly vectorSearch: VectorSearchPort,
		private readonly cache: CachePort,
	) {}

	async execute(params: { text: string; limit?: number }): Promise<SearchResult[]> {
		const query = createSearchQuery(params);

		const cacheKey = this.buildCacheKey(query);
		const cached = await this.cache.get<SearchResult[]>(cacheKey);
		if (cached) return cached;

		const queryVector = await this.embedding.embed(query.text);

		const fetchSize = Math.min(query.limit * 3, 50);
		const matches = await this.vectorSearch.search(queryVector, fetchSize);

		const results: SearchResult[] = matches.map((match) => {
			const book = createBookMetadata({
				bookId: String(match.metadata.bookId ?? ""),
				title: String(match.metadata.title ?? ""),
				author: String(match.metadata.author ?? ""),
				year: Number(match.metadata.year ?? 0),
				language: String(match.metadata.language ?? "en"),
			});

			const passage = createPassage({
				passageId: match.id,
				text: String(match.metadata.text ?? ""),
				book,
				chapter: String(match.metadata.chapter ?? ""),
				chunkIndex: Number(match.metadata.chunkIndex ?? 0),
			});

			return {
				passage,
				score: createSimilarityScore(match.score),
			};
		});

		const filtered = this.ranker.filterByThreshold(results);
		const diversified = this.ranker.deduplicateByBook(filtered);
		const final = diversified.slice(0, query.limit);

		if (final.length > 0) {
			await this.cache
				.set(cacheKey, final, CACHE_TTL_SECONDS)
				.catch((e) => console.error("[WARN] Cache write failed:", e));
		}

		return final;
	}

	private buildCacheKey(query: SearchQuery): string {
		const normalized = query.text.replace(/\s+/g, " ");
		return `search:${normalized}:${query.limit}`;
	}
}
