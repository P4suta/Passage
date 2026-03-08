import { describe, expect, it } from "vitest";
import { SearchError } from "../../src/port/error/search-error.js";

describe("SearchError", () => {
	it("has correct name", () => {
		const err = new SearchError("test", "EMBEDDING_FAILED");
		expect(err.name).toBe("SearchError");
	});

	it("has correct code", () => {
		const err = new SearchError("test", "VECTOR_SEARCH_FAILED");
		expect(err.code).toBe("VECTOR_SEARCH_FAILED");
	});

	it("preserves cause", () => {
		const cause = new Error("original");
		const err = new SearchError("wrapped", "CACHE_ERROR", cause);
		expect(err.cause).toBe(cause);
	});

	it("is an instance of Error", () => {
		const err = new SearchError("test", "STORAGE_ERROR");
		expect(err).toBeInstanceOf(Error);
	});
});
