/* Generato da scripts/gen-types.mjs: non modificare. Rigenera con `pnpm gen:types`. */

export type Schemaversion = 2
export type Version = string
export type Model = string
/**
 * Data di generazione, ISO-8601
 */
export type Generatedat = string
/**
 * Slug stabile del libro
 */
export type Id = string
export type Title = string
export type Author = string | null
/**
 * Lingua di output, codice ISO 639-1
 */
export type Lang = string
export type Sourcepages = number
export type Covercolor = string | null
/**
 * 5-8 frasi sul libro intero
 */
export type Summary = string
/**
 * @minItems 3
 * @maxItems 7
 */
export type Keyideas = [string, string, string, ...string[]]
/**
 * Markdown gerarchico per markmap
 */
export type Mindmap = string
/**
 * @minItems 1
 */
export type Chapters = [Chapter, ...Chapter[]]
export type Id1 = string
export type Index = number
export type Title1 = string
export type Pagestart = number
export type Pageend = number
export type Estminutes = number
export type Tldr = string
/**
 * Riassunto di fine capitolo, a paragrafi
 */
export type Summary1 = string
/**
 * @minItems 3
 * @maxItems 200
 */
export type Cards = [Card, Card, Card, ...Card[]]
export type Id2 = string
export type CardType = 'concept' | 'definition' | 'example' | 'quote' | 'procedure' | 'check' | 'section' | 'takeaway'
export type Title2 = string | null
/**
 * L'idea in breve, o la domanda per `check`
 */
export type Body = string
/**
 * Perché, come ed esempio concreto
 */
export type Details = string | null
/**
 * Passi di una `procedure`
 */
export type Steps = string[] | null
/**
 * Comandi o codice, letterali dal libro
 */
export type Code = string | null
/**
 * Risposta di una `check`
 */
export type Answer = string | null
/**
 * Pagina del PDF, a partire da 1
 */
export type Page = number | null
export type Mindmap1 = string
/**
 * @minItems 3
 * @maxItems 20
 */
export type Flashcards = [Flashcard, Flashcard, Flashcard, ...Flashcard[]]
export type Id3 = string
export type Q = string
export type A = string
export type Page1 = number
export type Glossary = GlossaryEntry[] | null
export type Term = string
export type Definition = string
export type Chapterid = string | null

export interface BookPack {
  schemaVersion: Schemaversion
  generator: GeneratorInfo
  book: Book
  overview: Overview
  chapters: Chapters
  glossary?: Glossary
}
export interface GeneratorInfo {
  version: Version
  model: Model
  generatedAt: Generatedat
}
export interface Book {
  id: Id
  title: Title
  author?: Author
  lang: Lang
  sourcePages: Sourcepages
  coverColor?: Covercolor
}
export interface Overview {
  summary: Summary
  keyIdeas: Keyideas
  mindmap: Mindmap
}
export interface Chapter {
  id: Id1
  index: Index
  title: Title1
  pageStart: Pagestart
  pageEnd: Pageend
  estMinutes: Estminutes
  tldr: Tldr
  summary: Summary1
  cards: Cards
  mindmap: Mindmap1
  flashcards: Flashcards
}
export interface Card {
  id: Id2
  type: CardType
  title?: Title2
  body: Body
  details?: Details
  steps?: Steps
  code?: Code
  answer?: Answer
  page?: Page
}
export interface Flashcard {
  id: Id3
  q: Q
  a: A
  page: Page1
}
export interface GlossaryEntry {
  term: Term
  definition: Definition
  chapterId?: Chapterid
}
