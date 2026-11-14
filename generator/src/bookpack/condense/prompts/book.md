Below are the chapter syntheses of "{{book_title}}"{{author_clause}}. Write the book-level material from these syntheses only.

- `summary`: 5 to 8 sentences on the whole book: its thesis and how it develops.
- `keyIdeas`: 3 to 7 load-bearing ideas of the book, one short sentence each.
- `title`: the book title written in the same language as your `summary`. The original title is "{{book_title}}": if it is in a different language, translate it faithfully; keep it unchanged only if it is already in that language. Keep any subtitle or note in brackets.
- `mindmap`: hierarchical markdown for a mind map of the book. Exactly one `#` heading with the book title as written in `title`. Below it, one `##` heading per chapter whose text is exactly the chapter title as written below, in the same order, with 1 to 3 short `-` items under each. At most 4 levels of depth.
- `glossary`: the terms a reader needs, with the definition given in the book and the `chapterId` where they are introduced (the `ch-NN` code below). Use an empty list if the book introduces no special terminology.

Write in this language: {{lang}}. The chapter titles in the mind map stay exactly as written below.

<chapters>
{{chapters}}
</chapters>
