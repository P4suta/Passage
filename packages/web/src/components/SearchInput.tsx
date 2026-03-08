import { Show, createSignal, onCleanup } from "solid-js";
import { SearchApiError, searchPassages } from "../lib/api.js";
import type { SearchResult } from "../lib/types.js";
import { ResultList } from "./ResultList.js";

const DEBOUNCE_MS = 400;

export function SearchInput() {
	const [query, setQuery] = createSignal("");
	const [results, setResults] = createSignal<SearchResult[]>([]);
	const [loading, setLoading] = createSignal(false);
	const [error, setError] = createSignal<string | null>(null);
	let debounceTimer: ReturnType<typeof setTimeout>;
	let abortController: AbortController | undefined;
	onCleanup(() => {
		clearTimeout(debounceTimer);
		abortController?.abort();
	});

	function handleInput(text: string) {
		setQuery(text);
		clearTimeout(debounceTimer);
		abortController?.abort();

		if (text.trim().length === 0) {
			setResults([]);
			setError(null);
			return;
		}

		debounceTimer = setTimeout(async () => {
			abortController = new AbortController();
			setLoading(true);
			setError(null);
			try {
				const response = await searchPassages(text.trim(), 10, {
					signal: abortController.signal,
				});
				setResults(response.results);
			} catch (e) {
				if (e instanceof DOMException && e.name === "AbortError") return;
				if (e instanceof SearchApiError && e.status === 429) {
					const seconds = e.retryAfter ?? 60;
					setError(`Too many searches. Please wait ${seconds} seconds.`);
				} else {
					setError("Search failed. Please try again.");
				}
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
