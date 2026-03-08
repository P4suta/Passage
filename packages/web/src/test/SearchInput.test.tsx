import { fireEvent, render, screen } from "@solidjs/testing-library";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SearchInput } from "../components/SearchInput.js";

vi.mock("../lib/api.js", () => ({
	searchPassages: vi.fn().mockResolvedValue({
		results: [
			{
				passageId: "1",
				text: "Test passage",
				book: {
					bookId: "b1",
					title: "Test Book",
					author: "Author",
					year: 1900,
					language: "en",
				},
				chapter: "Ch1",
				score: 0.9,
			},
		],
		count: 1,
		query: "test",
	}),
}));

describe("SearchInput", () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it("renders a textarea", () => {
		render(() => <SearchInput />);
		expect(screen.getByRole("textbox")).toBeInTheDocument();
	});

	it("debounces search calls", async () => {
		const { searchPassages } = await import("../lib/api.js");
		render(() => <SearchInput />);

		const input = screen.getByRole("textbox");
		fireEvent.input(input, { target: { value: "hello" } });

		expect(searchPassages).not.toHaveBeenCalled();

		await vi.advanceTimersByTimeAsync(400);

		expect(searchPassages).toHaveBeenCalledWith("hello");
	});

	it("does not search on empty input", async () => {
		const { searchPassages } = await import("../lib/api.js");
		vi.mocked(searchPassages).mockClear();

		render(() => <SearchInput />);

		const input = screen.getByRole("textbox");
		fireEvent.input(input, { target: { value: "   " } });

		await vi.advanceTimersByTimeAsync(400);

		expect(searchPassages).not.toHaveBeenCalled();
	});

	it("shows loading indicator during search", async () => {
		const { searchPassages } = await import("../lib/api.js");
		let resolveSearch: (value: any) => void;
		vi.mocked(searchPassages).mockImplementation(
			() =>
				new Promise((resolve) => {
					resolveSearch = resolve;
				}),
		);

		render(() => <SearchInput />);

		const input = screen.getByRole("textbox");
		fireEvent.input(input, { target: { value: "test" } });

		await vi.advanceTimersByTimeAsync(400);

		expect(screen.getByLabelText("Searching...")).toBeInTheDocument();

		resolveSearch?.({ results: [], count: 0, query: "test" });
		await vi.advanceTimersByTimeAsync(0);
	});

	it("shows error message on failure", async () => {
		const { searchPassages } = await import("../lib/api.js");
		vi.mocked(searchPassages).mockRejectedValueOnce(new Error("fail"));

		render(() => <SearchInput />);

		const input = screen.getByRole("textbox");
		fireEvent.input(input, { target: { value: "test" } });

		await vi.advanceTimersByTimeAsync(400);
		await vi.advanceTimersByTimeAsync(0);

		expect(screen.getByRole("alert")).toHaveTextContent("Search failed");
	});
});
