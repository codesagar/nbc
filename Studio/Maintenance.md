# Maintain this collection

Use lowercase hyphenated titles and meaningful extensions. Stories use `S###-title.md`; these stable shelf IDs are editorial navigation, not historical chapter order. Character photographs retain original filenames in `Characters/<Name>/Photos/`. Episode folders use independent `E###-title` IDs and versioned creative artifacts. Historical identifiers belong in provenance at the end of stories and in [migration-map.json](migration-map.json).

## Add or revise a story

Read the whole proposed text and search for existing events. Compare competing versions in full. Use one working story per distinct narrative; put a meaningful alternative under a labeled heading in that file when practical. Split joined chapters; preserve supported fragment relationships. Strip acquisition wrappers, normalize formatting and record consequential editorial choices without inventing narrative. Add one link and a short browse description to [Stories/README.md](../Stories/README.md), the sole story listing. Original chronology and approval stay unknown unless supported.

Before replacing source bytes, save the originals in a dated compressed archive **outside NBC**, with paths and SHA-256 hashes. Keep the verified pre-reorganization archive immutable. A new source/revision gets concise provenance; add its recovery reference to the migration map. No need to duplicate the expanded source collection inside NBC.

## Add a reference or asset

Open the actual image or relevant animation frames. Decide its concrete NBC use. Store only useful source art and required prompts/settings; game installers, binaries, caches and failed generations belong outside the active collection. For a photo, retain filename, hash, source, visible observations, limitations, intended uses, permission ceiling and exposure group in `Characters/reference-policy.json`; update its character guide. Restrictions can be narrowed by observed suitability, never cleared by file renaming or an old approval label. Add generated studies to [Assets](../Assets/README.md) only with explicit purpose and limitations. Generated art never controls original anatomy.

## Finish an edit

Inspect the exact file changes and read/open changed material. Run `python3 Studio/library.py verify` to see additions, removals or changed bytes. After inspecting those expected differences, run `python3 Studio/library.py seal`, then `python3 Studio/library.py verify`. Seal updates the single current accounting file and checks links and photo pins; it cannot validate prose quality or grant approval. Finder `.DS_Store` and Python `__pycache__` are incidental and excluded from current accounting.

Run isolated tool fixtures after changing the tool: `python3 -B -m unittest discover -s Studio -p 'test_*.py'`. Production stages and review live in one episode record; [Production](Production.md) explains when work can advance. External publication and owner adoption remain distinct decisions.

## Browser reader and authoring clones

After editing a story, run `python3 Studio/build_reader.py` and inspect its browser page. `Reader/` is generated, portable and tracked for immediate reading after a clone; edit source/design files rather than generated pages. See [Reader](Reader.md) for setup, sharing and GitHub Pages publishing.

Active accounting excludes `.git`, `.venv`, caches and `Productions/Library-Refinement/delivery-v###/`. Frozen deliveries retain their own original accounting and manifests; they are optional local archives, excluded from Git, and must not be rewritten. Current sources, original working artwork, policies and `Reader/` are still fully accounted. A clone therefore verifies without bringing the frozen duplicates. Historical absolute links into `NBC_Archives` are treated as external recovery dependencies, not required clone files. `archive-check` and original recovery require the separate archive set.
