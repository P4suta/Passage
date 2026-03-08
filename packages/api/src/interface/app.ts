import { OpenAPIHono } from "@hono/zod-openapi";
import { cors } from "hono/cors";
import type { SearchUseCase } from "../application/search-use-case.js";
import type { CachePort } from "../port/cache-port.js";
import { errorHandler } from "./middleware/error-handler.js";
import { rateLimiter } from "./middleware/rate-limiter.js";
import { healthRoute } from "./routes/health.js";
import { searchRoute } from "./routes/search.js";

interface AppDeps {
	searchUseCase: SearchUseCase;
	cache: CachePort;
}

export function createApp(deps: AppDeps) {
	const app = new OpenAPIHono();

	app.use("*", cors({ origin: "*" }));
	app.use("/api/*", rateLimiter(deps.cache));
	app.onError(errorHandler);

	searchRoute(app, deps.searchUseCase);
	healthRoute(app);

	app.doc("/openapi.json", {
		openapi: "3.1.0",
		info: {
			title: "Passage API",
			version: "1.0.0",
			description: "Semantic search across world literature",
		},
	});

	return app;
}
