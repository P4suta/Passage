import { For, Show } from "solid-js";
import type { SearchResult } from "../lib/types.js";
import { ResultCard } from "./ResultCard.js";

interface ResultListProps {
	results: SearchResult[];
	hasSearched: boolean;
}

export function ResultList(props: ResultListProps) {
	return (
		<>
			<Show when={props.results.length > 0}>
				<ul class="result-list" aria-label="Search results">
					<For each={props.results}>
						{(result, index) => (
							<li>
								<ResultCard result={result} index={index()} />
							</li>
						)}
					</For>
				</ul>
			</Show>
			<Show when={props.hasSearched && props.results.length === 0}>
				<p class="no-results">No passages found.</p>
			</Show>
		</>
	);
}
