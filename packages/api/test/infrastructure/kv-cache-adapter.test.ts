import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import { KvCacheAdapter } from "../../src/infrastructure/kv-cache-adapter.js";

describe("KvCacheAdapter", () => {
	it("returns null for missing key", async () => {
		const adapter = new KvCacheAdapter(env.CACHE);
		const result = await adapter.get("nonexistent");
		expect(result).toBeNull();
	});

	it("stores and retrieves a value", async () => {
		const adapter = new KvCacheAdapter(env.CACHE);
		await adapter.set("test-key", { data: "hello" }, 60);
		const result = await adapter.get<{ data: string }>("test-key");
		expect(result).toEqual({ data: "hello" });
	});

	it("increments a counter", async () => {
		const adapter = new KvCacheAdapter(env.CACHE);
		const first = await adapter.increment("counter-key", 60);
		expect(first).toBe(1);
		const second = await adapter.increment("counter-key", 60);
		expect(second).toBe(2);
	});
});
