import { describe, expect, it } from "vitest";
import { createSimilarityScore, isRelevant } from "../../../src/domain/model/search-result.js";

describe("createSimilarityScore", () => {
	it("creates a valid score", () => {
		const score = createSimilarityScore(0.85);
		expect(score.value).toBe(0.85);
	});

	it("allows -1", () => {
		expect(createSimilarityScore(-1).value).toBe(-1);
	});

	it("allows 1", () => {
		expect(createSimilarityScore(1).value).toBe(1);
	});

	it("throws on value below -1", () => {
		expect(() => createSimilarityScore(-1.1)).toThrow("between -1 and 1");
	});

	it("throws on value above 1", () => {
		expect(() => createSimilarityScore(1.1)).toThrow("between -1 and 1");
	});
});

describe("isRelevant", () => {
	it("returns true for score >= 0.3", () => {
		expect(isRelevant(createSimilarityScore(0.3))).toBe(true);
		expect(isRelevant(createSimilarityScore(0.8))).toBe(true);
	});

	it("returns false for score < 0.3", () => {
		expect(isRelevant(createSimilarityScore(0.29))).toBe(false);
		expect(isRelevant(createSimilarityScore(0))).toBe(false);
		expect(isRelevant(createSimilarityScore(-0.5))).toBe(false);
	});
});
