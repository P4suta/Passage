import { Hono } from "hono";
import { describe, expect, it, vi } from "vitest";
import { rateLimiter } from "../../../src/interface/middleware/rate-limiter.js";
import type { CachePort } from "../../../src/port/cache-port.js";

function createMockCache(count: number): CachePort {
	return {
		get: vi.fn().mockResolvedValue(null),
		set: vi.fn().mockResolvedValue(undefined),
		increment: vi.fn().mockResolvedValue(count),
	};
}

function createTestApp(cache: CachePort) {
	const app = new Hono();
	app.use("*", rateLimiter(cache));
	app.get("/test", (c) => c.json({ ok: true }));
	return app;
}

describe("rateLimiter", () => {
	it("allows requests under the limit", async () => {
		const app = createTestApp(createMockCache(1));
		const res = await app.request("/test");
		expect(res.status).toBe(200);
	});

	it("sets X-RateLimit headers", async () => {
		const app = createTestApp(createMockCache(5));
		const res = await app.request("/test");
		expect(res.headers.get("X-RateLimit-Limit")).toBe("30");
		expect(res.headers.get("X-RateLimit-Remaining")).toBe("25");
	});

	it("returns 429 when limit exceeded", async () => {
		const app = createTestApp(createMockCache(31));
		const res = await app.request("/test");
		expect(res.status).toBe(429);
		const body = (await res.json()) as any;
		expect(body.error).toBe("Too many requests");
		expect(body.retryAfter).toBe(60);
	});

	it("shows 0 remaining when at limit", async () => {
		const app = createTestApp(createMockCache(30));
		const res = await app.request("/test");
		expect(res.status).toBe(200);
		expect(res.headers.get("X-RateLimit-Remaining")).toBe("0");
	});
});
