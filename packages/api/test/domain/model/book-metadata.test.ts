import { describe, expect, it } from "vitest";
import { createBookMetadata } from "../../../src/domain/model/book-metadata.js";

describe("createBookMetadata", () => {
	it("creates a valid BookMetadata", () => {
		const meta = createBookMetadata({
			bookId: "book-001",
			title: "Great Expectations",
			author: "Charles Dickens",
			year: 1861,
			language: "en",
		});
		expect(meta.bookId).toBe("book-001");
		expect(meta.title).toBe("Great Expectations");
		expect(meta.author).toBe("Charles Dickens");
		expect(meta.year).toBe(1861);
		expect(meta.language).toBe("en");
	});

	it("throws on empty bookId", () => {
		expect(() =>
			createBookMetadata({
				bookId: "",
				title: "Title",
				author: "Author",
				year: 1900,
				language: "en",
			}),
		).toThrow("non-empty bookId");
	});

	it("throws on empty title", () => {
		expect(() =>
			createBookMetadata({
				bookId: "id",
				title: "",
				author: "Author",
				year: 1900,
				language: "en",
			}),
		).toThrow("non-empty bookId, title, and author");
	});

	it("throws on empty author", () => {
		expect(() =>
			createBookMetadata({
				bookId: "id",
				title: "Title",
				author: "",
				year: 1900,
				language: "en",
			}),
		).toThrow("non-empty bookId, title, and author");
	});

	it("throws on negative year", () => {
		expect(() =>
			createBookMetadata({
				bookId: "id",
				title: "Title",
				author: "Author",
				year: -1,
				language: "en",
			}),
		).toThrow("non-negative integer");
	});

	it("throws on non-integer year", () => {
		expect(() =>
			createBookMetadata({
				bookId: "id",
				title: "Title",
				author: "Author",
				year: 19.5,
				language: "en",
			}),
		).toThrow("non-negative integer");
	});

	it("returns a frozen object", () => {
		const meta = createBookMetadata({
			bookId: "id",
			title: "Title",
			author: "Author",
			year: 0,
			language: "en",
		});
		expect(Object.isFrozen(meta)).toBe(true);
	});
});
