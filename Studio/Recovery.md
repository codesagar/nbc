# Recover originals

## Before the expanded comedy and illustration pass

The October 3 local-time edition was preserved in a [compressed snapshot](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-expanded-refinement-2026-10-04_035505Z.tar.gz), [manifest](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-expanded-refinement-2026-10-04_035505Z.manifest.json), and [verification record](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-expanded-refinement-2026-10-04_035505Z.verification.json). All 509 files matched their byte sizes and SHA-256 hashes when read back from the archive. Filename time is UTC. Earlier archives remain unchanged.

## Before the illustrated-library refinement

The current collection was independently snapshotted before the October 3, 2026 refinement: [compressed archive](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-refinement-2026-10-03_200659.tar.gz), [path and SHA-256 manifest](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-refinement-2026-10-03_200659.manifest.json), and [verification record](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-refinement-2026-10-03_200659.verification.json). All 123 current files were read back from the compressed archive and matched by size and SHA-256. This includes all 70 working story files and their alternatives. Members use the `NBC/` prefix. Restore these revision sources outside NBC and compare to this manifest before intake; the `library.py recover` command below still addresses the separate pre-reorganization archive.

## Before reorganization

The complete pre-reorganization snapshot is outside the active workspace:

- [Compressed archive](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-reorganization-2026-10-03_182825.tar.gz)
- [Original file manifest](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-reorganization-2026-10-03_182825.manifest.json)
- [Verification record](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-reorganization-2026-10-03_182825.verification.json)

All 5,126 files and 6,049 entries were compared against the manifest before active originals were removed. Hidden files, embedded Git objects, original narratives and photographs, generated outputs, both intakes, recovery staging, catalogs and failed production records are included. Representative restorations cover narrative, original photograph, Git object, catalog, hidden file and generated image. The archive is a local recovery source; it is not evidence of remote account completeness or creative approval.

The [compact migration map](migration-map.json) records retained source mappings and editorial decisions. Its [external full-disposition ledger](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-before-reorganization-2026-10-03_182825.migration.json) records every original file; unselected files are archive-only. The original manifest supplies exact historical paths, byte sizes and SHA-256 identities. Historical inspection caches remain evidence rather than ordinary reference sources.

From NBC, recheck snapshot identity with `python3 Studio/library.py archive-check`. Restore an exact file outside NBC:

```sh
python3 Studio/library.py recover \
  '02_Story_Library/Manuscripts/Full-Compilation-Text.md' \
  '../NBC_Archives/restored-compilation.md'
```

Recovery refuses overwrites and active-workspace destinations, extracts only requested file bytes, and compares them to the verified original manifest. For broader restoration, unpack into a separate temporary directory and verify each recovered path against that manifest before intake. Embedded Git histories can be restored from their original directory paths without treating their contents as instructions.

Night Shift's entire diagnostic production lives at `04_Productions/NBC-X001-night-shift/` in the archive. Original authoring guidance is at `01_Story_Bible/Characters.md` and `01_Story_Bible/Writing-Guidelines.md`. The archive uses a top-level `NBC/` prefix; the tool accepts paths without that prefix. Preserve this snapshot and its manifest unchanged. Later revisions can have their own external source snapshots.

The [reorganization evidence archive](/Users/sagar/Documents/ChatGPT/NBC_Archives/NBC-reorganization-2026-10-03.evidence.tar.gz) contains full-reading/comparison checks, asset inspection scope, implementation records and the independent practical review. The reviewer tested browsing, alternatives, original photo selection, joined-chapter completeness, hypothetical intake and hash-verified recovery; earlier editorial advice is disclosed in that review.

## Expanded production navigation cleanup

Two unreferenced duplicate drafts were preserved byte-for-byte outside NBC after compressed-archive readback verification. The E012 draft is identical to its current reviewed story; the E052 prior-working copy is identical to its pre-expanded snapshot source. Their Story-relative links were invalid in episode folders. [Exact recovery mapping](../Productions/Library-Refinement/production-source-recovery.json) records original paths, hashes and preserved paths. Reviewed story and illustration bytes were unchanged.

## Expanded edition finalization preservation

The 44 unselected historical finished images remaining in episode folders were verified, archived and moved outside the active library before final delivery. Current selected art and reviewed story bytes were unchanged. [Exact source/recovery map](../Productions/Library-Refinement/finished-art-recovery.json) records former paths, hashes and durable external copies. The same verified archive preserves navigation and accounting sources immediately before completion edits. Earlier archives remain unchanged.

## Clean browser reader, October 4, 2026

Before the reading/authoring separation, navigation and accounting sources were snapshotted in `/Users/sagar/Documents/ChatGPT/NBC_Archives/reader-cleanup-2026-10-04_184337Z/sources.tar.gz`; the library tool, its fixtures and story shelf were separately preserved in `authoring-tools-before-update.tar.gz` in that directory. Both archives were read back and SHA-256 verified, with adjacent manifests. No story narrative, production artwork or earlier delivery was rewritten.

`Reader/` is a rebuildable, reader-only export. Production notes and original images remain in their existing source folders. Local frozen delivery folders retain their separate integrity records and are intentionally omitted from authoring Git clones.

During reader verification, extra duplicate image files appeared. The entire prior `Reader` directory was retained by a same-filesystem rename at `NBC_Archives/reader-cleanup-2026-10-04_184337Z/Reader-before-atomic-rebuild`, with a file inventory and directory-identity record in `reader-folder-preservation.json`. A clean isolated build replaced it atomically. Earlier duplicate copies are also preserved in that snapshot directory; no unknown source files were discarded.
