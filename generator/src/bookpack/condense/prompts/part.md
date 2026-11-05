Write the study cards for part {{part}} of {{parts}} of the chapter "{{chapter_title}}" of "{{book_title}}". This part covers about {{words}} words of the book.

Target: {{target}} content cards, between {{low}} and {{high}}. Cover the whole part evenly, from its first page to its last, in reading order, without skipping sections. Add {{checks}} comprehension checks on top of those.

Let the form follow the content:
- If the text teaches how to do something (commands, tools, configuration, attacks, recipes, techniques to apply), prefer `procedure` cards with real steps, and include the commands or code from the book.
- If the text argues ideas, prefer `concept` and `definition` cards, with their reasons and consequences.
- Use `example` whenever the book works through a concrete case: an example often teaches more than the rule it illustrates.

Card fields:
- `type`: `concept`, `definition`, `example`, `procedure`, `quote` or `check`.
- `title`: at most 8 words naming the idea, not the topic. Required except for `quote` and `check`, where it is null.
- `body`: the idea itself, in one or two sentences, at most 60 words.
- `details`: the part that makes it stick, 40 to 120 words: why it is true or why it matters, how it works, and the concrete case, number or consequence from the text. Null only for `quote` and `check`.
- `steps`: only for `procedure`: 2 to 10 steps in order, each one an action with its purpose. Null otherwise.
- `code`: commands or code copied literally from the text, at most 20 lines, when they help. Null otherwise.
- `answer`: only for `check`. Null otherwise.
- `page`: the page number from the `[p. N]` markers, within pages {{page_start}}-{{page_end}}.

A `quote` is at most 25 words, copied literally from the text, and at most one per part, only if it is really worth keeping.

A `check` is a question placed right after the cards it tests, with the question in `body` and an answer of 1 to 3 sentences in `answer`. It tests only what the previous cards of this part explained. Prefer "why", "how" and "what would you do if" over facts to recite, and never ask yes/no questions.

Also give this part a short `title` of at most 8 words naming its subject, and an `intro` of one sentence saying what the reader will get out of it.

<chapter_part>
{{text}}
</chapter_part>
