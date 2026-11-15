# Change watcher

One time each day, a GitHub Action gets each address in `sources.json` and compares a SHA-256 with `state.json`.
If a hash is different, the Action opens a GitHub issue in this repository.

| File | Content |
|---|---|
| `sources.json` | The watched addresses. Edit this file to add or move an address. |
| `state.json` | The last hash for each address. The Action updates it. |
| `../ledger/watch.py` | The code. Standard library only. |
| `../.github/workflows/watch.yml` | The schedule. |

## Two kinds of address

- **`file`:** a document. The hash is the hash of the bytes.
- **`page`:** a web page that lists documents. The hash is the hash of the list of document links. A new PDF link is a change. A new cookie banner is not.

## What the first hashes are

For 5 documents, `state.json` starts with the SHA-256 from the upstream corpus (Zhu, 2026).
So the first run already compares the live file with the file that the ledger was coded from.
A difference in that first run means that the developer replaced the file after the corpus was collected.

## First result, 15 November 2026

| Address | Result |
|---|---|
| Anthropic RSP v3.4, Google DeepMind FSF v3.1, Meta v2, OpenAI PF v2 | The live file has the same SHA-256 as the corpus file. |
| xAI framework, 30 June 2026 | **Different.** The corpus address gives HTTP 404. The xAI safety page links a file with the same date in its name and a different name suffix. Its SHA-256 is `4be128b1…`. The corpus file is `2c3c6313…`. See [issue 1](https://github.com/mrmarmac/apartresearch-ledger/issues/1). |
| OpenAI Preparedness page | HTTP 403. The site blocks the watcher. |
| Google DeepMind Frontier Safety page | No document links found in the page source. This entry does not detect a change. |

**The xAI files were compared on 15 November 2026. The words are identical** (3,294 words, no difference). The PDF title changed: the corpus file has the title "Privileged/Confidential DRAFT working FRAMEWORK DOC", and the new file has the title "xAI Frontier Artificial Intelligence Framework (June 30, 2026)". The new file is recorded in `data/reuploads.json`.

## Limits

- **The watcher finds that a file is different. It does not find what changed.** A person must look.
- **A re-upload with the same words also changes the hash.** The upstream corpus records 9 such re-uploads.
- **A site can block automated requests.** After 3 failures in sequence, the Action opens an issue "Watcher cannot get".
- **A new version at a new address is found only through a `page` entry.** A direct file address does not change when the developer publishes a new file with a new name.
- GitHub can delay or skip a scheduled run, and stops schedules in a repository with no activity for 60 days.

## Run it yourself

```bash
python run.py watch          # get each address, print the result, update state.json
python tests/test_watch.py   # tests, no network
```
