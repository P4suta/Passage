import { Show, createSignal, onCleanup } from "solid-js";
import { searchPassages } from "../lib/api.js";
import type { SearchResult } from "../lib/types.js";
import { ResultList } from "./ResultList.js";

const DEBOUNCE_MS = 400;

export function SearchInput() {
	const [query, setQuery] = createSignal("");
	const [results, setResults] = createSignal<SearchResult[]>([]);
	const [loading, setLoading] = createSignal(false);
	const [error, setError] = createSignal<string | null>(null);
	let debounceTimer: ReturnType<typeof setTimeout>;
	onCleanup(() => clearTimeout(debounceTimer));

	function handleInput(text: string) {
		setQuery(text);
		clearTimeout(debounceTimer);

		if (text.trim().length === 0) {
			setResults([]);
			setError(null);
			return;
		}

		debounceTimer = setTimeout(async () => {
			setLoading(true);
			setError(null);
			try {
				const response = await searchPassages(text.trim());
				setResults(response.results);
			} catch {
				setError("Search failed. Please try again.");
				setResults([]);
			} finally {
				setLoading(false);
			}
		}, DEBOUNCE_MS);
	}

	return (
		<div class="search-container">
			<textarea
				class="search-input"
				placeholder="Describe a feeling, a scene, a mood..."
				value={query()}
				onInput={(e) => handleInput(e.currentTarget.value)}
				rows={3}
				aria-label="Search query"
			/>
			<Show when={loading()}>
				<div class="loading-indicator" aria-label="Searching..." />
			</Show>
			<Show when={error()}>
				<p class="error-message" role="alert">
					{error()}
				</p>
			</Show>
			<ResultList results={results()} />
		</div>
	);
}
