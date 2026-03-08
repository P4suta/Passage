export interface BookInfo {
	bookId: string;
	title: string;
	author: string;
	year: number;
	language: string;
}

export interface SearchResult {
	passageId: string;
	text: string;
	book: BookInfo;
	chapter: string;
	score: number;
}

export interface SearchResponse {
	results: SearchResult[];
	count: number;
	query: string;
}
