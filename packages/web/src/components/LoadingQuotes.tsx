import { createSignal, onCleanup, onMount } from "solid-js";

const QUOTES = [
	{ text: "It is a truth universally acknowledged...", author: "Jane Austen" },
	{ text: "Call me Ishmael.", author: "Herman Melville" },
	{ text: "All happy families are alike.", author: "Leo Tolstoy" },
	{ text: "It was the best of times, it was the worst of times.", author: "Charles Dickens" },
	{ text: "I am no bird; and no net ensnares me.", author: "Charlotte Bront\u00eb" },
	{ text: "Not all those who wander are lost.", author: "J. R. R. Tolkien" },
	{ text: "Whatever our souls are made of, his and mine are the same.", author: "Emily Bront\u00eb" },
	{ text: "One must imagine Sisyphus happy.", author: "Albert Camus" },
	{ text: "The only way out of the labyrinth of suffering is to forgive.", author: "John Green" },
	{ text: "To live is the rarest thing in the world.", author: "Oscar Wilde" },
	{ text: "We are such stuff as dreams are made on.", author: "William Shakespeare" },
	{ text: "There is no greater agony than bearing an untold story inside you.", author: "Maya Angelou" },
	{ text: "So we beat on, boats against the current.", author: "F. Scott Fitzgerald" },
	{ text: "I think, therefore I am.", author: "Ren\u00e9 Descartes" },
	{ text: "The unexamined life is not worth living.", author: "Socrates" },
	{ text: "In the middle of difficulty lies opportunity.", author: "Albert Einstein" },
	{ text: "Beware; for I am fearless, and therefore powerful.", author: "Mary Shelley" },
	{ text: "It does not do to dwell on dreams and forget to live.", author: "J. K. Rowling" },
	{ text: "Who, being loved, is poor?", author: "Oscar Wilde" },
	{ text: "The wound is the place where the Light enters you.", author: "Rumi" },
	{ text: "Hope is the thing with feathers.", author: "Emily Dickinson" },
	{ text: "To err is human; to forgive, divine.", author: "Alexander Pope" },
	{ text: "The world breaks everyone, and afterward, some are strong at the broken places.", author: "Ernest Hemingway" },
	{ text: "I took the one less traveled by, and that has made all the difference.", author: "Robert Frost" },
];

const CYCLE_MS = 3200;

export function LoadingQuotes() {
	const [index, setIndex] = createSignal(Math.floor(Math.random() * QUOTES.length));
	const [phase, setPhase] = createSignal<"in" | "out">("in");

	let timer: ReturnType<typeof setInterval>;

	onMount(() => {
		timer = setInterval(() => {
			setPhase("out");
			setTimeout(() => {
				setIndex((i) => (i + 1) % QUOTES.length);
				setPhase("in");
			}, 800);
		}, CYCLE_MS);
	});

	onCleanup(() => clearInterval(timer));

	const quote = () => QUOTES[index()];

	return (
		<div class="loading-quotes" aria-label="Searching...">
			<p class={`loading-quote ${phase() === "in" ? "ink-in" : "ink-out"}`}>
				<span class="loading-quote-text">{quote().text}</span>
				<span class="loading-quote-author">{quote().author}</span>
			</p>
		</div>
	);
}
