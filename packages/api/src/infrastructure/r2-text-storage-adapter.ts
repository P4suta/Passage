import { SearchError } from "../port/error/search-error.js";
import type { TextStoragePort } from "../port/text-storage-port.js";

export class R2TextStorageAdapter implements TextStoragePort {
	constructor(private readonly bucket: R2Bucket) {}

	async getFullText(bookId: string, chapter: string): Promise<string | null> {
		const safeBookId = bookId.replace(/[^a-z0-9-]/g, "");
		const safeChapter = chapter.replace(/[^a-z0-9-]/g, "");
		if (!safeBookId || !safeChapter) return null;
		const key = `${safeBookId}/${safeChapter}.txt`;
		try {
			const object = await this.bucket.get(key);
			if (!object) return null;
			return await object.text();
		} catch (error) {
			throw new SearchError(`Failed to retrieve text: ${key}`, "STORAGE_ERROR", error);
		}
	}
}
