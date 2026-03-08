import solidPlugin from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

export default defineConfig({
	plugins: [solidPlugin()],
	test: {
		environment: "jsdom",
		globals: true,
		setupFiles: ["./src/test/setup.ts"],
		resolve: {
			conditions: ["development", "browser"],
		},
	},
	resolve: {
		conditions: ["development", "browser"],
	},
});
