import { SearchUseCase } from "./application/search-use-case.js";
import type { Env } from "./config/bindings.js";
import { KvCacheAdapter } from "./infrastructure/kv-cache-adapter.js";
import { VectorizeSearchAdapter } from "./infrastructure/vectorize-search-adapter.js";
import { WorkersAiEmbeddingAdapter } from "./infrastructure/workers-ai-embedding-adapter.js";
import { createApp } from "./interface/app.js";

let cachedApp: ReturnType<typeof createApp> | null = null;
let cachedEnv: Env | null = null;

function getApp(env: Env) {
	if (cachedApp && cachedEnv === env) return cachedApp;

	const embedding = new WorkersAiEmbeddingAdapter(env.AI);
	const vectorSearch = new VectorizeSearchAdapter(env.VECTORIZE);
	const cache = new KvCacheAdapter(env.CACHE);
	const searchUseCase = new SearchUseCase(embedding, vectorSearch, cache);

	cachedApp = createApp({ searchUseCase, cache });
	cachedEnv = env;
	return cachedApp;
}

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const app = getApp(env);
		return app.fetch(request, env, ctx);
	},
};
