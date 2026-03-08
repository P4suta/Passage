import type { BookMetadata } from "./book-metadata.js";

export interface Passage {
	readonly passageId: string;
	readonly text: string;
	readonly book: BookMetadata;
	readonly chapter: string;
	readonly chunkIndex: number;
}

export function createPassage(params: {
	passageId: string;
	text: string;
	book: BookMetadata;
	chapter: string;
	chunkIndex: number;
}): Passage {
	if (!params.passageId || !params.text) {
		throw new Error("Passage requires non-empty passageId and text");
	}
	if (params.chunkIndex < 0) {
		throw new Error("chunkIndex must be non-negative");
	}
	return Object.freeze({
		...params,
		book: Object.freeze(params.book),
	});
}
