import { createRoute, z } from "@hono/zod-openapi";
import type { OpenAPIHono } from "@hono/zod-openapi";
import type { SearchUseCase } from "../../application/search-use-case.js";

const SearchQuerySchema = z.object({
	q: z
		.string()
		.min(1, "Query must not be empty")
		.max(500, "Query must not exceed 500 characters")
		.openapi({
			description: "Search query text",
			example: "lonely night, yet strangely refreshing",
		}),
	limit: z.coerce
		.number()
		.int()
		.min(1)
		.max(20)
		.default(10)
		.openapi({ description: "Maximum number of results" }),
});

const PassageSchema = z.object({
	passageId: z.string(),
	text: z.string(),
	book: z.object({
		bookId: z.string(),
		title: z.string(),
		author: z.string(),
		year: z.number(),
		language: z.string(),
	}),
	chapter: z.string(),
	score: z.number(),
});

const SearchResponseSchema = z.object({
	results: z.array(PassageSchema),
	count: z.number(),
	query: z.string(),
});

const route = createRoute({
	method: "get",
	path: "/api/search",
	request: { query: SearchQuerySchema },
	responses: {
		200: {
			content: {
				"application/json": { schema: SearchResponseSchema },
			},
			description: "Search results",
		},
	},
});

export function searchRoute(app: OpenAPIHono, useCase: SearchUseCase) {
	app.openapi(route, async (c) => {
		const { q, limit } = c.req.valid("query");

		const results = await useCase.execute({
			text: q,
			limit,
		});

		return c.json({
			results: results.map((r) => ({
				passageId: r.passage.passageId,
				text: r.passage.text,
				book: {
					bookId: r.passage.book.bookId,
					title: r.passage.book.title,
					author: r.passage.book.author,
					year: r.passage.book.year,
					language: r.passage.book.language,
				},
				chapter: r.passage.chapter,
				score: r.score.value,
			})),
			count: results.length,
			query: q,
		});
	});
}
