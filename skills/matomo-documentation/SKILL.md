---
name: matomo-documentation
description: "Create and update Matomo PHPDoc: derives contracts from code, adds descriptive docs for public API methods and posted events, and keeps internal docs minimal unless native types are missing or too broad."
---

# Matomo Documentation

## Overview

Use this skill for Matomo PHPDoc tasks, especially when updating public API method docblocks in Matomo PHP code.
Use `matomo-api-development-rules` for defining the API contract itself; this skill owns how that contract is documented.
Use `matomo-deprecation-rules` for deprecation lifecycle policy rather than treating docblocks as the source of deprecation timing rules.

## Gotchas

1. Trust code over existing docblocks; stale PHPDoc is common and should be treated as a claim to verify.
2. `@ignore` changes the documentation mode for public API methods: keep those under the internal minimal rules instead of the public descriptive rules.
3. Public API docs should describe the real request-facing contract, especially when parameters are forwarded unchanged to helpers like `Archive::build()`.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Writing or fixing PHPDoc for .php files.
2. Correcting `@param` or `@return` tags in Matomo PHPDoc.
3. Adding or updating docblocks for public API methods.
4. Normalizing Matomo API docblocks to match public request-facing inputs.

## Method Docblock Rules

Public API methods must have PHPDoc immediately above them. Protected and private methods do not need descriptive docblocks by default, but minimal type-only PHPDoc should be added when native types are missing or too broad.

1. Scope.
   - Apply the hard requirement only to externally callable public methods in `plugins/*/API.php`.
   - Public methods outside plugin API classes follow the general rules below, not the stricter public API rules.
   - If a public method in `plugins/*/API.php` has `@ignore`, treat it like a non-public/internal method for documentation purposes.
   - Do not add docblocks to protected or private methods unless the task explicitly asks for internal documentation.
   - Do not add docblocks to constructors or internal helpers by default.
   - Incorrect existing docblocks must always be fixed, including on internal, protected, and private methods.
   - For internal or non-public methods, if native types fully cover the contract, prefer removing a stale or redundant docblock over rewriting it into another redundant docblock.
2. Validate existing docblocks.
   - Treat existing docblocks as claims to verify, not as a source of truth.
   - Trust code over docblocks when they disagree.
   - Native PHP parameter and return type hints are authoritative.
   - Never reuse an existing PHPDoc type just because it is already present. Derive the documented contract from the actual code.
   - If native types, defaults, or actual behavior conflict with existing documentation, update the documentation to match the code.
   - If no native type exists, derive the documented contract from how the value is validated, normalized, forwarded, or returned.
   - If a method forwards a parameter unchanged to a helper or downstream API with a clear accepted contract, document the forwarded parameter to match that real contract unless the method narrows it first.
   - Check summaries, parameter types, parameter descriptions, and return docs against the actual code behavior before reusing them.
   - Preserve metadata and visibility tags such as `@ignore`, `@internal`, `@unsanitized`, `@deprecated`, and `@hide`.
   - `@ignore` is not just preserved metadata. It changes how a method should be documented: ignored public methods use the internal minimal rules instead of the public descriptive rules.
   - Update or remove outdated, incorrect, or misleading documentation instead of preserving it.
   - This validation-and-fix rule applies to all existing docblocks, not only public API methods.
3. Scalar type aliases.
   - In updated docblocks, normalize scalar aliases to canonical PHPDoc forms: `bool`, `int`, `string`, `float`, `array`, `callable`, `mixed`, `null`.
   - Replace long-form aliases such as `boolean` and `integer` when touching a docblock.
4. Summary line (two sentences max).
   - For public API methods, keep an existing summary unless it is missing, incorrect, or too vague to be useful.
   - For public API methods, new summaries should be short and behavior-focused.
   - For internal or non-public methods, do not add or keep a summary line by default.
   - For internal or non-public methods, remove stale, trivial, or obvious summaries.
   - Only keep or add a non-public summary when it conveys remarkable information not already obvious from the method name, signature, or minimal tags.
5. `@param` tags.
   - Keep parameter order identical to method signature.
   - Use types that describe the public API contract for public API methods.
   - For public API methods, document every parameter and include a description for each one.
   - For public API methods, prefer request-facing types over internal helper flexibility.
   - Public API parameter descriptions should be concise and accurate, even when the parameter is straightforward.
   - Add Matomo-specific constraints and examples when they are confidently derived from code behavior.
   - For internal or non-public methods that are documented as part of a specific task, use the real implementation type when needed.
   - For internal or non-public methods, add or fix minimal `@param` tags when native type hints are missing or too broad.
   - For internal or non-public methods, do not add parameter descriptions just because the docblock is being updated.
   - For internal or non-public methods, simplify or remove stale or trivial parameter prose instead of rewriting it into fuller prose.
   - For internal or non-public methods, add or keep parameter descriptions only when they provide information that is not obvious from the signature.
   - Use array shapes and `@phpstan-param` only when the array structure is stable, important to callers, and can be derived confidently from code.
   - Add examples only when confidently derived from code behavior.
6. `@return` tag.
   - For public API methods, every method must have an `@return` tag.
   - For public API methods, every non-`void` `@return` tag must include descriptive text.
   - Never add descriptive text to `@return void`.
   - For public API methods, use a specific return type that reflects the public contract.
   - For internal or non-public methods, add or fix minimal `@return` tags when native return types are missing or too broad.
   - For internal or non-public methods, do not add return descriptions just because the docblock is being updated.
   - For internal or non-public methods, simplify or remove stale or trivial return prose instead of rewriting it into fuller prose.
   - For internal or non-public methods, add or keep a return description only when it provides information that is not obvious from the signature.
   - Use array shapes and `@phpstan-return` only when the structure is stable and worth documenting.
   - Include a short description when it adds useful meaning.
   - Never add examples.
7. `@throws`.
   - Do not add `@throws` tags.
   - Remove existing `@throws` tags when updating a method docblock.

## Docblock Formatting

1. Wrapped lines must align with the description column.
2. For `@param` and `@return`, do not vertically align all tags to a shared column.
3. Use normal single-space formatting on the first line of each tag.
4. Align only continuation (wrapped) lines under the description text.
5. Avoid mass-reformatting unrelated existing docblocks.

## Event Documentation Rules

Events posted via `Piwik::postEvent()` are included in generated developer documentation unless they are marked internal.

1. Every new `Piwik::postEvent('EventName', ...)` should have a PHPDoc block above the call that describes what the event does, the parameters it passes, and a short usage example.
2. If an event parameter is passed by reference, document that explicitly.
3. Events intended only for core/internal use should include `@internal`.
4. When changing parameters or behavior of an existing posted event, update the event PHPDoc in the same change.
5. If an event is being deprecated, use `matomo-deprecation-rules` for the lifecycle and transition policy, and use this skill only for documenting that policy correctly.

## API File-Specific Rules
When working with plugin API classes in `plugins/*/API.php`, extra rules apply:
1. File summary
   - Keep an existing class summary unless it is missing or misleading.
   - If a class summary is missing, add a short summary that describes what the API exposes.
   - Do not force one exact opening phrase across all existing API classes.
2. Public methods
   - Every externally callable public API method must have a descriptive docblock.
   - Every public API parameter must have a `@param` tag with a description.
   - Every public API method must have an `@return` tag.
   - Public API `@return` tags must include descriptive text unless the return type is `void`.
   - Prioritize endpoint behavior, accepted request parameters, and return semantics.
   - If a public API method has `@ignore`, do not apply these descriptive public-method rules. Apply the internal minimal rules instead.
3. Non-public methods
   - Protected and private methods do not need docblocks by default.

For non-plugin `API.php` files, apply only the general PHPDoc rules above.

## Reference Templates

Read `references/api-doc-templates.md` when:

1. documenting common public API parameters such as `$idSite`, `$date`, `$period`, or `$segment`
2. deciding whether an API method should document single-site or multi-site `$idSite`
3. updating internal type-only PHPDoc and you want a minimal before/after example
