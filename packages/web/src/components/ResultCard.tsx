import type { SearchResult } from "../lib/types.js";

interface ResultCardProps {
	result: SearchResult;
	index: number;
}

export function ResultCard(props: ResultCardProps) {
	return (
		<article
			class="result-card"
			style={{ "animation-delay": `${props.index * 0.08}s` }}
			aria-label={`Passage from ${props.result.book.title}`}
		>
			<blockquote>{props.result.text}</blockquote>
			<div class="result-meta">
				<span class="result-title">{props.result.book.title}</span>
				<span>&mdash; {props.result.book.author}</span>
				<span>({props.result.book.year})</span>
				<span>&middot; {props.result.chapter}</span>
				<span class="result-score">{(props.result.score * 100).toFixed(0)}% match</span>
			</div>
		</article>
	);
}
