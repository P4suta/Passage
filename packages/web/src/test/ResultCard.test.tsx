import { render, screen } from "@solidjs/testing-library";
import { describe, expect, it } from "vitest";
import { ResultCard } from "../components/ResultCard.js";
import type { SearchResult } from "../lib/types.js";

const mockResult: SearchResult = {
	passageId: "test-1",
	text: "It was a dark and stormy night.",
	book: {
		bookId: "book-1",
		title: "Test Novel",
		author: "Test Author",
		year: 1900,
		language: "en",
	},
	chapter: "Chapter 1",
	score: 0.85,
};

describe("ResultCard", () => {
	it("displays passage text in a blockquote", () => {
		render(() => <ResultCard result={mockResult} index={0} />);
		const blockquote = screen.getByText("It was a dark and stormy night.");
		expect(blockquote.tagName).toBe("BLOCKQUOTE");
	});

	it("displays book title and author", () => {
		render(() => <ResultCard result={mockResult} index={0} />);
		expect(screen.getByText("Test Novel")).toBeInTheDocument();
		expect(screen.getByText(/Test Author/)).toBeInTheDocument();
	});

	it("displays year and chapter", () => {
		render(() => <ResultCard result={mockResult} index={0} />);
		expect(screen.getByText("(1900)")).toBeInTheDocument();
		expect(screen.getByText(/Chapter 1/)).toBeInTheDocument();
	});

	it("displays score as percentage", () => {
		render(() => <ResultCard result={mockResult} index={0} />);
		expect(screen.getByText("85% match")).toBeInTheDocument();
	});

	it("has aria-label with book title", () => {
		render(() => <ResultCard result={mockResult} index={0} />);
		expect(screen.getByRole("article")).toHaveAttribute("aria-label", "Passage from Test Novel");
	});
});
