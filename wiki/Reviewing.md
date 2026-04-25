# Participating in Review

Anyone can review an open submission. Review happens entirely on GitHub via the standard pull-request flow.

## Find an open submission

Open the [pull requests page](https://github.com/metagov/metagov-journal/pulls). Submissions in review are PRs whose head branch starts with `submit/`. Each PR's "Files changed" tab shows the new submission directory: `submissions/{slug}/input.md`, `instance.ttl`, and `compiled.md`.

## How to review

1. **Read `compiled.md` first** — it's the article view the journal will publish. If it reads coherently and the institution is recognizable as *living*, the substance is probably sound.
2. **Cross-check `input.md`** — the author's source prose. The compiled view is generated from the structured RDF, but `input.md` carries the voice and reflexivity (especially Q6).
3. **Skim `instance.ttl`** — the RDF Turtle is the canonical structure. You don't have to grok it line-by-line; spot-check that the entities (stakeholders, references, etc.) match what the prose claims.
4. **Apply the criteria** in [criteria.md](https://github.com/metagov/metagov-journal/blob/main/criteria.md). For a structured framework (severity per question, common pitfalls), see [evaluation.md](https://github.com/metagov/metagov-journal/blob/main/evaluation.md).
5. **Comment** using GitHub's inline review or the "Review changes" feature. Suggest specific revisions; quote the catechism when relevant.

Editors decide when a submission is ready to merge. Multiple rounds of revision are normal and expected.

## What you don't have to do

You don't need to run the CLI to review — `validate.yml` already SHACL-validates every PR and the staleness check confirms `compiled.md` matches `instance.ttl`. Your job is editorial judgment, not mechanical verification.
