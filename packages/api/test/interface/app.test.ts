import { describe, expect, it, vi } from "vitest";
import { createApp } from "../../src/interface/app.js";

function createTestDeps() {
	return {
		searchUseCase: { execute: vi.fn().mockResolvedValue([]) } as any,
		cache: {
			get: vi.fn().mockResolvedValue(null),
			set: vi.fn().mockResolvedValue(undefined),
			increment: vi.fn().mockResolvedValue(1),
		},
	};
}

describe("App", () => {
	it("sets CORS headers", async () => {
		const app = createApp(createTestDeps());
		const res = await app.request("/api/health", {
			headers: { Origin: "http://example.com" },
		});
		expect(res.headers.get("Access-Control-Allow-Origin")).toBe("*");
	});

	it("serves OpenAPI spec", async () => {
		const app = createApp(createTestDeps());
		const res = await app.request("/openapi.json");
		expect(res.status).toBe(200);
		const body = (await res.json()) as any;
		expect(body.openapi).toBe("3.1.0");
		expect(body.info.title).toBe("Passage API");
	});
});
