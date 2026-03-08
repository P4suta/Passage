import { describe, expect, it, vi } from "vitest";
import { WorkersAiEmbeddingAdapter } from "../../src/infrastructure/workers-ai-embedding-adapter.js";
import { SearchError } from "../../src/port/error/search-error.js";

function createMockAi(data: number[][] = [[0.1, 0.2, 0.3]]) {
	return {
		run: vi.fn().mockResolvedValue({ data }),
	} as unknown as Ai;
}

describe("WorkersAiEmbeddingAdapter", () => {
	it("embeds a single text", async () => {
		const ai = createMockAi([[0.1, 0.2, 0.3]]);
		const adapter = new WorkersAiEmbeddingAdapter(ai);
		const result = await adapter.embed("hello");
		expect(result).toEqual([0.1, 0.2, 0.3]);
		expect(ai.run).toHaveBeenCalledWith("@cf/baai/bge-m3", { text: ["hello"] });
	});

	it("embeds a batch of texts", async () => {
		const ai = createMockAi([
			[0.1, 0.2],
			[0.3, 0.4],
		]);
		const adapter = new WorkersAiEmbeddingAdapter(ai);
		const result = await adapter.embedBatch(["a", "b"]);
		expect(result).toEqual([
			[0.1, 0.2],
			[0.3, 0.4],
		]);
	});

	it("throws SearchError on AI failure", async () => {
		const ai = createMockAi();
		(ai.run as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("AI down"));
		const adapter = new WorkersAiEmbeddingAdapter(ai);
		await expect(adapter.embed("test")).rejects.toThrow(SearchError);
	});

	it("throws on empty response", async () => {
		const ai = createMockAi([]);
		const adapter = new WorkersAiEmbeddingAdapter(ai);
		await expect(adapter.embed("test")).rejects.toThrow(SearchError);
	});

	it("throws on batch size exceeding 100", async () => {
		const ai = createMockAi();
		const adapter = new WorkersAiEmbeddingAdapter(ai);
		const texts = Array.from({ length: 101 }, (_, i) => `text ${i}`);
		await expect(adapter.embedBatch(texts)).rejects.toThrow(SearchError);
	});
});
