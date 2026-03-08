import type { MiddlewareHandler } from "hono";
import type { CachePort } from "../../port/cache-port.js";

const MAX_REQUESTS_PER_MINUTE = 30;
const WINDOW_SECONDS = 60;

export function rateLimiter(cache: CachePort): MiddlewareHandler {
	return async (c, next) => {
		const ip = c.req.header("cf-connecting-ip") ?? "unknown";
		const key = `ratelimit:${ip}`;

		const count = await cache.increment(key, WINDOW_SECONDS);

		c.header("X-RateLimit-Limit", String(MAX_REQUESTS_PER_MINUTE));
		c.header("X-RateLimit-Remaining", String(Math.max(0, MAX_REQUESTS_PER_MINUTE - count)));

		if (count > MAX_REQUESTS_PER_MINUTE) {
			return c.json(
				{
					error: "Too many requests",
					retryAfter: WINDOW_SECONDS,
				},
				429,
			);
		}

		await next();
	};
}
