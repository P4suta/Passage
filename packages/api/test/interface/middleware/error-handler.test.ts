import { Hono } from "hono";
import { describe, expect, it } from "vitest";
import { SearchQueryValidationError } from "../../../src/domain/model/search-query.js";
import { errorHandler } from "../../../src/interface/middleware/error-handler.js";
import { SearchError } from "../../../src/port/error/search-error.js";

function createTestApp(error: Error) {
	const app = new Hono();
	app.onError(errorHandler);
	app.get("/test", () => {
		throw error;
	});
	return app;
}

describe("errorHandler", () => {
	it("returns 400 for SearchQueryValidationError", async () => {
		const app = createTestApp(new SearchQueryValidationError("bad query"));
		const res = await app.request("/test");
		expect(res.status).toBe(400);
		const body = (await res.json()) as any;
		expect(body.error).toBe("bad query");
	});

	it("returns 429 for RATE_LIMITED SearchError", async () => {
		const app = createTestApp(new SearchError("rate limited", "RATE_LIMITED"));
		const res = await app.request("/test");
		expect(res.status).toBe(429);
	});

	it("returns 400 for VALIDATION_ERROR SearchError", async () => {
		const app = createTestApp(new SearchError("invalid", "VALIDATION_ERROR"));
		const res = await app.request("/test");
		expect(res.status).toBe(400);
	});

	it("returns 500 for other SearchError codes", async () => {
		const app = createTestApp(new SearchError("fail", "EMBEDDING_FAILED"));
		const res = await app.request("/test");
		expect(res.status).toBe(500);
		const body = (await res.json()) as any;
		expect(body.error).toBe("Internal search error");
	});

	it("returns 500 for generic Error", async () => {
		const app = createTestApp(new Error("unknown"));
		const res = await app.request("/test");
		expect(res.status).toBe(500);
		const body = (await res.json()) as any;
		expect(body.error).toBe("Internal server error");
	});
});
