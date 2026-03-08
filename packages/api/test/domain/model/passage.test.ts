import { describe, expect, it } from "vitest";
import { createBookMetadata } from "../../../src/domain/model/book-metadata.js";
import { createPassage } from "../../../src/domain/model/passage.js";

const validBook = createBookMetadata({
	bookId: "book-001",
	title: "Title",
	author: "Author",
	year: 1900,
	language: "en",
});

describe("createPassage", () => {
	it("creates a valid Passage", () => {
		const passage = createPassage({
			passageId: "chunk-001",
			text: "Some text",
			book: validBook,
			chapter: "Chapter 1",
			chunkIndex: 0,
		});
		expect(passage.passageId).toBe("chunk-001");
		expect(passage.text).toBe("Some text");
		expect(passage.book.bookId).toBe("book-001");
		expect(passage.chapter).toBe("Chapter 1");
		expect(passage.chunkIndex).toBe(0);
	});

	it("throws on empty passageId", () => {
		expect(() =>
			createPassage({
				passageId: "",
				text: "Some text",
				book: validBook,
				chapter: "Chapter 1",
				chunkIndex: 0,
			}),
		).toThrow("non-empty passageId and text");
	});

	it("throws on empty text", () => {
		expect(() =>
			createPassage({
				passageId: "id",
				text: "",
				book: validBook,
				chapter: "Chapter 1",
				chunkIndex: 0,
			}),
		).toThrow("non-empty passageId and text");
	});

	it("throws on negative chunkIndex", () => {
		expect(() =>
			createPassage({
				passageId: "id",
				text: "text",
				book: validBook,
				chapter: "Chapter 1",
				chunkIndex: -1,
			}),
		).toThrow("chunkIndex must be non-negative");
	});
});
