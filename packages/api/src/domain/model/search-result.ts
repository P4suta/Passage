import type { Passage } from "./passage.js";

export interface SimilarityScore {
	readonly value: number;
}

const RELEVANCE_THRESHOLD = 0.3;

export function createSimilarityScore(value: number): SimilarityScore {
	if (value < -1 || value > 1) {
		throw new Error(`Similarity score must be between -1 and 1: ${value}`);
	}
	return Object.freeze({ value });
}

export function isRelevant(score: SimilarityScore): boolean {
	return score.value >= RELEVANCE_THRESHOLD;
}

export interface SearchResult {
	readonly passage: Passage;
	readonly score: SimilarityScore;
}
