import { describe, expect, it, vi } from "vitest";
import { createApp } from "../../../src/interface/app.js";

function createTestDeps() {
	return {
		searchUseCase: { execute: vi.fn() } as any,
		cache: {
			get: vi.fn().mockResolvedValue(null),
			set: vi.fn().mockResolvedValue(undefined),
			increment: vi.fn().mockResolvedValue(1),
		},
	};
}

describe("GET /api/health", () => {
	it("returns 200 with status ok", async () => {
		const app = createApp(createTestDeps());
		const res = await app.request("/api/health");
		expect(res.status).toBe(200);
		const body = await res.json();
		expect(body).toEqual({ status: "ok" });
	});
});
