export interface TextStoragePort {
	getFullText(bookId: string, chapter: string): Promise<string | null>;
}
