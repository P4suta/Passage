export interface VectorMatch {
	readonly id: string;
	readonly score: number;
	readonly metadata: Record<string, string | number>;
}

export interface VectorSearchPort {
	search(vector: number[], topK: number): Promise<VectorMatch[]>;
}
