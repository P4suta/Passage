import type { ErrorHandler } from "hono";
import { SearchQueryValidationError } from "../../domain/model/search-query.js";
import { SearchError } from "../../port/error/search-error.js";

export const errorHandler: ErrorHandler = (err, c) => {
	console.error(`[ERROR] ${err.message}`, err);

	if (err instanceof SearchQueryValidationError) {
		return c.json({ error: err.message }, 400);
	}

	if (err instanceof SearchError) {
		switch (err.code) {
			case "RATE_LIMITED":
				return c.json({ error: "Too many requests" }, 429);
			case "VALIDATION_ERROR":
				return c.json({ error: err.message }, 400);
			default:
				return c.json({ error: "Internal search error" }, 500);
		}
	}

	return c.json({ error: "Internal server error" }, 500);
};
