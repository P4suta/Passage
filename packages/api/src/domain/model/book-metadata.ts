export interface BookMetadata {
	readonly bookId: string;
	readonly title: string;
	readonly author: string;
	readonly year: number;
	readonly language: string;
}

export function createBookMetadata(params: {
	bookId: string;
	title: string;
	author: string;
	year: number;
	language: string;
}): BookMetadata {
	if (!params.bookId || !params.title || !params.author) {
		throw new Error("BookMetadata requires non-empty bookId, title, and author");
	}
	if (!Number.isInteger(params.year) || params.year < 0) {
		throw new Error(`BookMetadata year must be a non-negative integer: ${params.year}`);
	}
	return Object.freeze(params);
}
