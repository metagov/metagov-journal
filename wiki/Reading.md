# Reading the Journal

The journal publishes structured specifications of *living institutions* — organizations that demonstrate active participation, capacity for adaptation, and observable patterns of collective behavior.

## Where to find institutions

- **This wiki** is the navigable entry point. The [Home](Home) page lists every institution, person, and organization currently in the catalog. Click any **Institution** page for the full specification rendered as an article. **Person** and **Organization** pages list everyone they're affiliated with — useful for tracing who-does-what across institutions.

- **The repository** holds the source of truth at [github.com/metagov/metagov-journal](https://github.com/metagov/metagov-journal). Each institution lives at `submissions/{slug}/` with three artifacts:
  - `input.md` — the author's prose answering the catechism
  - `instance.ttl` — the canonical RDF graph (Turtle) — the structured truth
  - `compiled.md` — the published article view, regenerated from `instance.ttl` by CI

- **For programmatic access**, the RDF in `instance.ttl` plus `shared/people.ttl` and `shared/organizations.ttl` can be queried with SPARQL or any RDF tool. The schema lives at `ontology/mgj.ttl`.

## What to read first

- The [catechism](https://github.com/metagov/metagov-journal/blob/main/catechism.md) — the nine questions every submission answers. Reading it makes every submission much easier to navigate.
- The [self-referential submission](Institution-metagov-journal) — the journal documents itself as the inaugural specification, demonstrating the pattern.
