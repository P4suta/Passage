import { render, screen } from "@solidjs/testing-library";
import { describe, expect, it } from "vitest";
import { ResultList } from "../components/ResultList.js";
import type { SearchResult } from "../lib/types.js";

const mockResults: SearchResult[] = [
	{
		passageId: "1",
		text: "First passage",
		book: { bookId: "b1", title: "Book One", author: "Author 1", year: 1900, language: "en" },
		chapter: "Ch1",
		score: 0.9,
	},
	{
		passageId: "2",
		text: "Second passage",
		book: { bookId: "b2", title: "Book Two", author: "Author 2", year: 1950, language: "en" },
		chapter: "Ch2",
		score: 0.8,
	},
];

describe("ResultList", () => {
	it("renders nothing for empty results", () => {
		const { container } = render(() => <ResultList results={[]} />);
		expect(container.querySelector(".result-list")).toBeNull();
	});

	it("renders correct number of cards", () => {
		render(() => <ResultList results={mockResults} />);
		const articles = screen.getAllByRole("article");
		expect(articles).toHaveLength(2);
	});

	it("has aria-label on the list", () => {
		render(() => <ResultList results={mockResults} />);
		expect(screen.getByRole("list")).toHaveAttribute("aria-label", "Search results");
	});
});
