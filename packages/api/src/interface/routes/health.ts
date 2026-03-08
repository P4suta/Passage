import type { OpenAPIHono } from "@hono/zod-openapi";

export function healthRoute(app: OpenAPIHono) {
	app.get("/api/health", (c) => {
		return c.json({ status: "ok" });
	});
}
