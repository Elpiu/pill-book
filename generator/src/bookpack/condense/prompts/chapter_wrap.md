These are the study cards of the chapter "{{chapter_title}}" of "{{book_title}}" (pages {{page_start}}-{{page_end}}). The reader has just gone through them. Use only what is in these cards.

Write:
- `tldr`: one sentence with the core of the chapter.
- `summary`: the end-of-chapter summary found in good textbooks. About {{summary_words}} words, in flowing paragraphs separated by a blank line. It must recap the whole chapter and how its ideas connect. Repeating the content is intended, but say it differently from the cards: a new order and different words help the reader consolidate it. No bullet points and no headings.
- `takeaway`: at most 60 words answering "what do I take away from this chapter?".
- `mindmap`: hierarchical markdown for a mind map: one `#` heading with the chapter topic, `##` headings for the main branches, `-` items below them. At most 4 levels of depth and about {{mindmap_nodes}} nodes. Node labels are a few words, not sentences.
- `flashcards`: about {{flashcards}} questions to review this chapter in the coming days, between 3 and 15. Every question must be answerable from the cards below: never ask about anything they do not explain. Mix recall of what matters most with application ("what would you do if", "why"). No yes/no questions and no trivia. Answers are 1 to 2 sentences. Each has the `page` of the card it comes from.

<chapter_cards>
{{cards}}
</chapter_cards>
