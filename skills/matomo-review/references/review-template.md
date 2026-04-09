# Review Template

Use this structure exactly for the final review output:

```markdown
Findings

Blocking
1. ...
None.

Medium
1. ...
None.

Low / Polish
1. ...
None.

Problem Addressed
<1 short paragraph>

Overall Assessment
Verdict: Yes | No | Partially
Merge readiness: Ready | Not ready
<1 short paragraph covering evidence, strengths, confidence, test coverage, and ambiguity when relevant>

Matomo-Specific Checks
Applied rule sets
- ...
- None.

Applied review dimensions
- ...
- None.

Structural integrity
- Clean.
- Findings listed above.
- Not checked: <reason>

Ran
- ...
- None.

Not run
- <command> — <reason confidence is limited>
- None.

Next Steps
1. ...
```

## Example Output

```markdown
Findings

Blocking
1. Duplicate translation keys were added in `plugins/Example/lang/en.json` around line 42 and only registered in `plugins/Example/Example.php` around line 110, which violates `matomo-i18n-development-rules` and creates dead translator churn.

Medium
None.

Low / Polish
1. `plugins/Example/vue/src/View.vue` around line 88 still uses a legacy helper name that obscures intent, which raises maintainability cost but does not block the branch goal.

Problem Addressed
The branch appears intended to update the Example plugin GDPR copy and associated UI text.

Overall Assessment
Verdict: Partially
Merge readiness: Not ready
The UI copy update is mostly in place, but the branch is not merge-ready because the new translation-key set violates the routed i18n rules. Confidence is moderate: the diff is coherent, but build and UI-test coverage is incomplete because only targeted static inspection was performed.

Matomo-Specific Checks
Applied rule sets
- `matomo-i18n-development-rules` — blocking findings listed above.
- `matomo-vue-development-rules` — reviewed, no findings.
- `matomo-test-runner` — review expectation applied; missing validation noted below.

Applied review dimensions
- `intent`
- `structural integrity`
- `maintainability`
- `test quality`

Structural integrity
- Clean.

Ran
- `git diff --stat origin/5.x-dev...HEAD`
- `git diff origin/5.x-dev...HEAD`
- `git log --oneline origin/5.x-dev..HEAD`
- `rg "ExampleKey|ExampleKeyNew" plugins/Example`

Not run
- `ddev matomo:console vue:build Example` — not run in this environment, so build/lint regressions remain unverified.
- `ddev matomo:console tests:run-ui Example` — not run in this environment, so screenshot and rendered-flow regressions remain unverified.

Next Steps
1. Remove the dead translation keys or reuse the existing keys instead of shipping parallel variants.
2. Run the targeted Example Vue build and UI validation once the environment supports `ddev`.
```
