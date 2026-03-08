import { defineConfig } from "astro/config";
import solidJs from "@astrojs/solid-js";
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
	integrations: [solidJs()],
	output: "static",
	adapter: cloudflare(),
});
