import type { EmbeddingPort } from "../port/embedding-port.js";
import { SearchError } from "../port/error/search-error.js";

const MODEL = "@cf/baai/bge-m3" as const;
const MAX_BATCH_SIZE = 100;

export class WorkersAiEmbeddingAdapter implements EmbeddingPort {
	constructor(private readonly ai: Ai) {}

	async embed(text: string): Promise<number[]> {
		try {
			const response = (await this.ai.run(MODEL, {
				text: [text],
			})) as { data?: number[][] };
			const vectors = response.data;
			if (!vectors || vectors.length === 0) {
				throw new Error("Empty embedding response");
			}
			return vectors[0];
		} catch (error) {
			if (error instanceof SearchError) throw error;
			throw new SearchError(`Failed to generate embedding: ${error}`, "EMBEDDING_FAILED", error);
		}
	}

	async embedBatch(texts: string[]): Promise<number[][]> {
		if (texts.length > MAX_BATCH_SIZE) {
			throw new SearchError(
				`Batch size ${texts.length} exceeds maximum ${MAX_BATCH_SIZE}`,
				"EMBEDDING_FAILED",
			);
		}
		try {
			const response = (await this.ai.run(MODEL, {
				text: texts,
			})) as { data: number[][] };
			return response.data;
		} catch (error) {
			if (error instanceof SearchError) throw error;
			throw new SearchError(
				`Failed to generate batch embeddings: ${error}`,
				"EMBEDDING_FAILED",
				error,
			);
		}
	}
}
