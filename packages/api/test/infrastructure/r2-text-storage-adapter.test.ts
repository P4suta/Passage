import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import { R2TextStorageAdapter } from "../../src/infrastructure/r2-text-storage-adapter.js";

describe("R2TextStorageAdapter", () => {
	it("returns null for missing object", async () => {
		const adapter = new R2TextStorageAdapter(env.TEXTS);
		const result = await adapter.getFullText("nonexistent", "chapter-1");
		expect(result).toBeNull();
	});

	it("retrieves stored text", async () => {
		const adapter = new R2TextStorageAdapter(env.TEXTS);
		await env.TEXTS.put("book-001/chapter-1.txt", "Hello, World!");
		const result = await adapter.getFullText("book-001", "chapter-1");
		expect(result).toBe("Hello, World!");
	});

	it("prevents path traversal", async () => {
		const adapter = new R2TextStorageAdapter(env.TEXTS);
		const result = await adapter.getFullText("../etc", "passwd");
		expect(result).toBeNull();
	});

	it("returns null for empty bookId after sanitization", async () => {
		const adapter = new R2TextStorageAdapter(env.TEXTS);
		const result = await adapter.getFullText("../../", "test");
		expect(result).toBeNull();
	});
});
