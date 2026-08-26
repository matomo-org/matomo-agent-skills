# Surface Obligations

The classes the `Surface Inventory` in `SKILL.md` enumerates, and what each row is asked. Enumeration commands are in `references/review-checks.md`; the binding rules stay in the routed skills, which is why the last column names a skill rather than quoting one.

A row is answered `met` with the code that meets it, `unmet` as a finding, or `unreviewed` with the reason. `met` on a floor-carrying class is a stated negative, so it reaches the step-5 audit through the merge.

## 1. Stored state — owning lens: `contracts & compatibility`

A table or column the change adds or alters, wherever its DDL lives.

1. Does an installation that already recorded this component as installed get the schema? Name the vehicle. Activation-only creation is Severity Floor 4 on that population, and which vehicle is available is a `matomo-migrations-workflow` question, not a free choice.
2. What scopes a read or a write to one site? An `idsite` column, or enforced code on every path that touches the table. A limit that holds only by caller convention is Severity Floor 3.
3. Where the table holds data about a subject, do erasure, retention, and deleted-site cleanup reach it? Name the path each one takes.

## 2. Client-supplied parameter — owning lens: `security & trust`

A request, tracking, header, or cookie value the change newly reads. These rows are the untrusted-input inventory's rows, carrying three questions the inventory did not previously ask.

1. What authorises the write this value reaches, and is that authority as wide as the state it changes? A gate on one parameter does not cover a second parameter that selects which state the first one writes.
2. What happens to a value outside the accepted set — rejected, or accepted as something else? A value folded into a sentinel that means "absent" is Severity Floor 1 when nothing tells the sender, and Severity Floor 2 when a documented contract said it would be honoured.
3. What size bound applies before the value is processed, and which code enforces it? This is the inventory's existing column; `none` is answered with the cost of the added work as a complexity class.

## 3. Public API method — owning lens: `contracts & compatibility`

A method the change adds or alters in `plugins/*/API.php`.

1. Is the documented return shape true for every arm the parameters allow? A multi-site or multi-period argument that returns a `DataTable\Map` where the docblock promises rows is Severity Floor 2, and `matomo-documentation` binds the fix.
2. Are fixed-value parameters validated against the set the docblock declares? `matomo-api-development-rules` binds this.
3. Is there an access check, and does a test fail without it? Coverage is a `matomo-test-runner` question; the check's absence is a security finding.

## 4. Named public artifact — owning lens: `conventions & precedent`

A segment, metric, dimension, event, config or option key, or exported prop the change adds, removes, or renames. Both sides of a rename are rows.

1. For a removed or renamed name, what resolves the old one, and for how long? `matomo-deprecation-rules` binds the transition; a rename with no resolving path is the same removal.
2. For an added name, what does the precedent probe return for its shape and placement?

## What is not a class here

A surface already answered by a mechanical check is not enumerated again: framework sinks are check 8, added `Updates/*.php` against its version marker is check 5, and removed public methods are check 7. The inventory covers what those checks cannot decide — whether the surface they found meets its obligations.
