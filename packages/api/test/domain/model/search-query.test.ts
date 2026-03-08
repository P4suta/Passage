import { describe, expect, it } from "vitest";
import {
	SearchQueryValidationError,
	createSearchQuery,
} from "../../../src/domain/model/search-query.js";

describe("createSearchQuery", () => {
	it("creates a valid query with defaults", () => {
		const query = createSearchQuery({ text: "lonely night" });
		expect(query.text).toBe("lonely night");
		expect(query.limit).toBe(10);
	});

	it("trims whitespace", () => {
		const query = createSearchQuery({ text: "  hello world  " });
		expect(query.text).toBe("hello world");
	});

	it("uses provided limit", () => {
		const query = createSearchQuery({ text: "test", limit: 5 });
		expect(query.limit).toBe(5);
	});

	it("throws on empty text", () => {
		expect(() => createSearchQuery({ text: "" })).toThrow(SearchQueryValidationError);
		expect(() => createSearchQuery({ text: "   " })).toThrow(SearchQueryValidationError);
	});

	it("throws on text exceeding 500 characters", () => {
		const longText = "a".repeat(501);
		expect(() => createSearchQuery({ text: longText })).toThrow(SearchQueryValidationError);
	});

	it("throws on limit below 1", () => {
		expect(() => createSearchQuery({ text: "test", limit: 0 })).toThrow(SearchQueryValidationError);
	});

	it("throws on limit above 20", () => {
		expect(() => createSearchQuery({ text: "test", limit: 21 })).toThrow(
			SearchQueryValidationError,
		);
	});
});
