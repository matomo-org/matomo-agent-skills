---
name: matomo-documentation
description: Create and update Matomo PHPDoc, especially for public API methods.
---

# Matomo Documentation

## Overview

Use this skill for Matomo PHPDoc tasks, especially when updating public API method docblocks in Matomo PHP code.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Writing or fixing PHPDoc for .php files.
2. Correcting `@param` or `@return` tags in Matomo PHPDoc.
3. Adding or updating docblocks for public API methods.
4. Normalizing Matomo API docblocks to match public request-facing inputs.

## Method Docblock Rules

Public API methods must have PHPDoc immediately above them. Protected and private methods do not need PHPDoc by default.

1. Scope.
   - Apply the hard requirement only to externally callable public methods in `plugins/*/API.php`.
   - Public methods outside plugin API classes follow the general rules below, not the stricter public API rules.
   - Do not add docblocks to protected or private methods unless the task explicitly asks for internal documentation.
   - Do not add docblocks to constructors or internal helpers by default.
   - Incorrect existing docblocks must always be fixed, including on internal, protected, and private methods.
2. Validate existing docblocks.
   - Treat existing docblocks as claims to verify, not as a source of truth.
   - Trust code over docblocks when they disagree.
   - If native types, defaults, or actual behavior conflict with existing documentation, update the documentation to match the code.
   - Check summaries, parameter types, parameter descriptions, and return docs against the actual code behavior before reusing them.
   - Update or remove outdated, incorrect, or misleading documentation instead of preserving it.
   - This validation-and-fix rule applies to all existing docblocks, not only public API methods.
3. Scalar type aliases.
   - In updated docblocks, normalize scalar aliases to canonical PHPDoc forms: `bool`, `int`, `string`, `float`, `array`, `callable`, `mixed`, `null`.
   - Replace long-form aliases such as `boolean` and `integer` when touching a docblock.
4. Summary line (two sentences max).
   - Keep an existing summary unless it is missing, incorrect, or too vague to be useful.
   - New summaries should be short and behavior-focused.
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
   - Use a specific return type when the return contract is not already obvious from the signature.
   - Every public API method must have an `@return` tag.
   - Every public API `@return` tag must include descriptive text.
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

## API File-Specific Rules
When working with plugin API classes in `plugins/*/API.php`, extra rules apply:
1. File summary
   - Keep an existing class summary unless it is missing or misleading.
   - If a class summary is missing, add a short summary that describes what the API exposes.
   - Do not force one exact opening phrase across all existing API classes.
2. Public methods
   - Every externally callable public API method must have a descriptive docblock.
   - Every public API parameter must have a `@param` tag with a description.
   - Every public API method must have an `@return` tag with descriptive text.
   - Prioritize endpoint behavior, accepted request parameters, and return semantics.
3. Non-public methods
   - Protected and private methods do not need docblocks by default.

For non-plugin `API.php` files, apply only the general PHPDoc rules above.



## Common Parameter Templates

Use these as common templates. The final type and description must match the actual accepted public input in the code.

- Determine the final parameter contract by inspecting the method signature and how the value is normalized or consumed.
- Validate any existing parameter documentation against the code before reusing it.
- Use these descriptive templates for public API methods only.
- For public API methods, document request-facing inputs, not broader internal PHP flexibility.
- For public API methods, always include parameter descriptions, even for straightforward parameters.
- For non-public methods, add or fix type-only tags when native types are missing or too broad.
- For non-public methods, add parameter descriptions only when they add useful information.

### \$date

- For public API methods, document `$date` as `string`.
- Use this when the public method accepts date strings or date ranges via API request input.
```php
@param string $date The date or date range to process.
                    'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                    or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

- For internal or non-public methods that are explicitly being documented, use the real implementation type if it truly accepts both strings and `Date`.
```php
@param Date|string $date
```

### \$idSite and \$idSites

- Use this when a single numeric site ID is accepted.
```php
@param int $idSite The numeric ID of the website to query.
```

- Use this when the parameter accepts a single site, multiple sites, comma-separated selectors, or `all`.
```php
@param int|string|int[] $idSite Website ID(s) to query.
                         - Single site ID (e.g. 1)
                         - Multiple site IDs (e.g. [1, 4, 5])
                         - Comma-separated list ("1,4,5") or "all"
```

- Use this when the method explicitly accepts selector strings or an array of strings.
```php
@param string|array $idSite Website ID(s) to query.
                            Accepts comma-separated IDs, "all", numeric IDs as strings, or ["all"].
```

### \$period

- Use this when `$period` must be one of the standard archive period strings.
```php
@param 'day'|'week'|'month'|'year'|'range' $period The period to process, processes data for the period
                                                   containing the specified date.
```

### \$segment

- Match the documented type to the actual accepted public input.
- Valid forms are `string|null` or `string|null|false`, depending on the method contract.
- Reuse the standard example and operator description for public API `$segment` docblocks instead of rewriting or tailoring it.
```php
@param string|null $segment Custom segment to filter the report.
                            Example: "referrerName==example.com"
                            Supports AND (;) and OR (,) operators.
```

## Internal Method Examples

Use these examples to keep internal/protected/private fixes minimal.

Bad:
```php
/**
 * @param integer $idGoal The goal id
 */
protected function loadGoal($idGoal)
```

Good:
```php
/**
 * @param int $idGoal
 */
protected function loadGoal($idGoal)
```

Bad:
```php
/**
 * @return bool Returns whether the value is true or false.
 */
private function isEnabled()
```

Good:
```php
/**
 * @return bool
 */
private function isEnabled()
```

Bad:
```php
private function loadGoal($idGoal)
```

Good:
```php
/**
 * @param int $idGoal
 */
private function loadGoal($idGoal)
```

Bad:
```php
private function isEnabled()
```

Good:
```php
/**
 * @return bool
 */
private function isEnabled()
```

Bad:
```php
/**
 * @param int $idGoal
 * @return bool
 */
private function hasGoal(int $idGoal): bool
```

Good:
```php
private function hasGoal(int $idGoal): bool
```

Bad:
```php
/**
 * @param int $idSite
 * @param array $config
 * @return void
 */
private function saveConfig(int $idSite, array $config): void
```

Good:
```php
/**
 * @param array<string, mixed> $config
 */
private function saveConfig(int $idSite, array $config): void
```

Keep a non-public description only when it adds non-obvious information, for example array structure, sentinel values, or special normalization behavior.
