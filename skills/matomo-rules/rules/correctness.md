---
set: correctness
title: Behavioural correctness
applies: ["**"]
---

# Behavioural correctness

The general rules behind "does the change do what it says, without breaking what worked". Use them
for defects no more specific rule covers; prefer the specific rule when one exists.

### COR-01 · The change does what its intent says, on every path
`release` `major`

The stated purpose is achieved for every argument shape and state the code can meet: multiple
sites, periods and ranges, segments, timezones, empty and null data, permission levels, absent
optional plugins, existing installations. A path where the intent silently does not happen is a
defect.

### COR-02 · No data loss
`release` `blocking`

No path drops, overwrites or deletes stored data, rows, fields or arguments beyond what the
operation was asked to remove — including state destroyed for a third party, or for another site
or user, by an operation someone else triggered (for example a filtered view that is saved back).
Never treat a loss as acceptable because it is intended, documented or observable; an exception is
a per-case decision by the person merging, not the author's or the reviewer's.

### COR-03 · Declared contracts are honoured
`release` `blocking`

A documented parameter, return shape, setting or recovery path works as documented. A downstream
internal exception is not the contract being honoured; neither is a silent fallback to a default.

### COR-04 · Existing behaviour does not regress
`release` `major`

Behaviour that users, API consumers or plugins rely on and that the change does not intend to alter
still works: other callers of changed code, other entry points (UI, API, console, scheduled tasks,
tracker) and other consumers of changed data.
