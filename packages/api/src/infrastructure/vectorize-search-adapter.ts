import { SearchError } from "../port/error/search-error.js";
import type { VectorMatch, VectorSearchPort } from "../port/vector-search-port.js";

export class VectorizeSearchAdapter implements VectorSearchPort {
	constructor(private readonly index: VectorizeIndex) {}

	async search(vector: number[], topK: number): Promise<VectorMatch[]> {
		try {
			const results = await this.index.query(vector, {
				topK,
				returnMetadata: "all",
			});

			return results.matches.map((match) => ({
				id: match.id,
				score: match.score ?? 0,
				metadata: (match.metadata ?? {}) as Record<string, string | number>,
			}));
		} catch (error) {
			throw new SearchError(`Vector search failed: ${error}`, "VECTOR_SEARCH_FAILED", error);
		}
	}
}
