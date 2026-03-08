import type { Env } from "../src/config/bindings.js";

declare module "cloudflare:test" {
	interface ProvidedEnv extends Env {}
}
