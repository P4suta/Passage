import type { SearchResponse } from "./types.js";

export function getMockSearchResponse(query: string): SearchResponse {
	return {
		query,
		count: 3,
		results: [
			{
				passageId: "mock-1",
				text: "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
				book: {
					bookId: "pride-and-prejudice",
					title: "Pride and Prejudice",
					author: "Jane Austen",
					year: 1813,
					language: "en",
				},
				chapter: "Chapter 1",
				score: 0.92,
			},
			{
				passageId: "mock-2",
				text: "Call me Ishmael. Some years ago\u2014never mind how long precisely\u2014having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world.",
				book: {
					bookId: "moby-dick",
					title: "Moby-Dick",
					author: "Herman Melville",
					year: 1851,
					language: "en",
				},
				chapter: "Loomings",
				score: 0.87,
			},
			{
				passageId: "mock-3",
				text: "In my younger and more vulnerable years my father gave me some advice that I\u2019ve been turning over in my mind ever since.",
				book: {
					bookId: "great-gatsby",
					title: "The Great Gatsby",
					author: "F. Scott Fitzgerald",
					year: 1925,
					language: "en",
				},
				chapter: "Chapter 1",
				score: 0.81,
			},
		],
	};
}
