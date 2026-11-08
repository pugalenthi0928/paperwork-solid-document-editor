# Paperwork — a SOLID document editor in Python

A small, working document editor built from the low-level design (LLD) lecture. Unlike a code-only diagram, this has a real local browser UI where you can add, edit, delete, reorder, preview, save, load, and export document blocks.

**Python 3.10+ · Standard library only · No installs or accounts required**

## Run it

From this project directory:

```bash
python3 server.py
```

Open **http://127.0.0.1:8765** in your browser.

To store your documents in a SQLite database instead of JSON files:

```bash
python3 server.py --storage sqlite
```

To run the original lecture-style terminal example:

```bash
python3 demo.py
```

To run all automated tests:

```bash
python3 -m unittest discover -s tests -v
```

## What you can do

- **Text** — type and edit paragraphs, with safe HTML output.
- **Images** — add an image by its public HTTP(S) URL and alt text. You need internet access for external images to load.
- **Line breaks and indents** — separate block types with their own rendering behaviour.
- **Reorder and remove** — move blocks up/down or delete them.
- **Preview** — the Python backend renders the blocks and returns HTML. The preview is not just a fake client-side mockup.
- **Save and reopen** — uses a named local JSON file or SQLite database, depending on startup setting.
- **Export HTML or TXT** — produces real downloadable files.

The web UI uses `my-document` as its default save ID. To open a different file by ID, use **Open saved**; subsequent Save/Export actions use the opened ID. Run this only on your own computer: it is intended as a local educational app, not a cloud service.

## Architecture

```text
Browser UI (client)
  |      |         |
  |      |         +--> Persistence (interface)
  |      |                    |-- FileStorage (JSON)
  |      |                    +-- SQLiteStorage (database)
  |      |
  |      +--> Document.render()
  |                    |
  |                    +--> DocumentElement.render() [polymorphism]
  |                              |-- TextElement
  |                              |-- ImageElement
  |                              |-- NewlineElement
  |                              +-- TabElement
  |
  +--> DocumentEditor --> Document.add/replace/remove/move
```

| File | Responsibility |
|---|---|
| `document_editor/elements.py` | Defines the `DocumentElement` abstraction and element types |
| `document_editor/document.py` | Holds ordered elements; delegates rendering to each object |
| `document_editor/editor.py` | Handles document edits; knows nothing about file/SQL storage |
| `document_editor/persistence.py` | Defines the storage abstraction and two implementations |
| `server.py` | HTTP client/orchestration layer, intentionally thin |
| `static/` | Browser UI (HTML, CSS, JavaScript) |
| `tests/` | Automated behaviour and design tests |

## What each SOLID principle looks like

**S — Single Responsibility:** `DocumentEditor` edits; `Document` manages content; `FileStorage` and `SQLiteStorage` store it. Each element defines how it renders.

**O — Open/Closed:** Add a new `DocumentElement` subclass and it can be added/rendered without changing `Document`. `DocumentElement.__init_subclass__` registers it for serialization.

**L — Liskov Substitution:** `Document` uses the `DocumentElement` contract, whether the block happens to be text, image, or a new type.

**I — Interface Segregation:** Each abstraction has a small, focused public contract. `Persistence` only requires `save` and `load`.

**D — Dependency Inversion:** Client code uses the `Persistence` abstraction. You can swap `FileStorage` for `SQLiteStorage` without changing the editor.

**Important nuance from the lecture:** There is no single mathematically 'perfect' SOLID diagram. The lecture first creates a separate `DocumentRenderer`, then brings rendering back into `Document` due to coupling and complexity tradeoffs. This build follows that *final* approach.

## Learn by changing the code

1. Run `python3 demo.py` and see how editor → document → element works.
2. Open `document_editor/elements.py`. Change how `TextElement.render()` formats a paragraph. Reload the browser.
3. Add a new `QuoteElement` subclass. See `test_new_element_type_without_changing_document` for a working example.
4. Run once with JSON storage, then with SQLite. Observe that **nothing in `DocumentEditor` changes**.
5. Write a failing unit test for a new feature, implement it, and rerun the suite.

## Boundaries

This is deliberately not Google Docs: no collaborative editing, file uploads, authentication, undo history, or rich inline selection. Image blocks use URLs rather than local file uploads. HTML export is a complete self-contained *page* but remote image URLs still need internet access.
