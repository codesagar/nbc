# Read, share, and edit Neet & Buddy

## Just read

Double-click `index.html` at the top of the project, or open [Reader/index.html](../Reader/index.html) in any modern browser. No Markdown app, Python, account, server, or internet connection is needed. The complete `Reader` folder must stay together. Search, story groups, previous/next links, adjustable text, night mode and optional alternate tellings are included. Read marks and the last reading position are saved only in that browser when local storage is available; reading and navigation work without it or without JavaScript.

The reader omits production and archival notes. Narrative epilogues and emotional endings stay intact. The three complete alternate tellings have their own optional pages. Two abbreviated-version descriptions remain in the editorial source rather than interrupting the reading experience. The order comes from [the sole story shelf](../Stories/README.md).

## Share with a reader

Send the ready-made reader ZIP, or zip the entire `Reader` folder. After extracting it, open `index.html`. It contains all reading pages and optimized illustrations, with no external fonts, services or image requests. The full-resolution originals remain in the working library.

For a new verified ZIP, use a new destination/version:

```sh
python3 Studio/build_reader.py --check --zip /path/to/Neet-and-Buddy-reader-v002.zip
```

## Edit or make new stories together

Share or clone the working repository, including `Stories`, `Characters`, `Assets`, `Productions`, `Studio`, and `Reader`. A clone can read the existing `Reader/index.html` immediately. The Git ignore rules omit the frozen delivery duplication and large archival packages; keep those separately for historical recovery. The production images make the authoring repository larger than the lightweight reader.

- **Words and picture placement:** edit the corresponding file in `Stories/`. Keep the archival sections at the end; the reader build separates them automatically.
- **Artwork:** retain the original in its episode folder under `Productions/`, and use a relative image link in the story. The build makes browser copies without altering the originals.
- **New story:** follow [Writing](Writing.md) and [Production](Production.md), add its source file and one entry to [Stories/README.md](../Stories/README.md), then rebuild. The reader derives its catalog from that shelf; there is no second list to maintain.
- **Reader design:** edit `Studio/reader/reader.css`, `reader.js`, or `Studio/build_reader.py`. Treat `Reader/` as generated output. The builder refuses to overwrite manual changes there.

Once per editing machine, install Python 3.10 or newer and create the build environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r Studio/reader/requirements.txt
```

On Windows, activate with `.venv\Scripts\activate` instead. For later edits, activate the environment and run:

```sh
python Studio/build_reader.py
```

Open the reader and check the affected pages. Commit both the source edits and rebuilt `Reader/` so the next clone is ready to read. The build records source and derivative hashes in `Studio/reader-build.json`; it does not grant story approval or update creative reviews. Follow [Maintenance](Maintenance.md) for preservation, inspection and local accounting.

## Publish on GitHub Pages

The prepared workflow publishes only `Reader/`. The Markdown, original photos, prompts and production history are not part of the Pages website; their visibility follows the repository's own visibility setting.

1. Push the working repository to your chosen GitHub repository, including the `.github` folder.
2. In that repository, open **Settings → Pages → Build and deployment → Source**, and choose **GitHub Actions**.
3. Open **Actions → Publish reader → Run workflow**. The workflow rebuilds the reader from the current source, checks its links and uploads just that folder.
4. When deployment completes, GitHub displays the website URL. Run the workflow again whenever you want to publish updated stories.

Nothing is published merely by editing or rebuilding locally. This workflow is deliberately run by hand. No remote repository was created or connected as part of the reader cleanup, and publication status remains `not_published`.

GitHub instructions: [configure a Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site), [official Pages deployment action](https://github.com/actions/deploy-pages).

## Earlier delivery and recovery

The local frozen delivery at `Productions/Library-Refinement/delivery-v001/` remains unchanged as a reviewed source/export snapshot. It intentionally contains production history and is no longer the everyday reading entry point. [Recovery](Recovery.md) describes the separate original archives. A Git clone can edit and build current stories without those external archives; retrieving historical originals requires the preserved archive set.
