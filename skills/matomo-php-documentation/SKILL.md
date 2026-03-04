---
name: matomo-php-documentation
description: Create and update Matomo PHP documentation codeblocks.
---

# Matomo PHP Documentation

## Overview

Use this skill when creating or updating PHP method docblocks for Matomo public APIs.

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Writing or fixing PHPDoc above public API methods.
2. Correcting `@param`, `@return`, or `@throws` tags.
3. Improving PHPDoc type precision, including array shapes.

## Method Docblock Rules

Every public API method must have PHPDoc immediately above it.

1. Summary line (two sentences max).
   - Keep existing summary if it already describes the method.
2. `@param` tags.
   - Keep parameter order identical to method signature.
   - Use accurate and specific types.
   - Use specific array shapes when applicable.
   - Add examples only when confidently derived from code behavior.
3. `@return` tag.
    - Use specific return type.
    - Use array shapes when applicable.
    - Include a short description.
    - Never add examples.
4. `@throws` tag only when explicitly thrown.

## Docblock Formatting

1. Wrapped lines must align with the description column.
2. For `@param`, `@return`, and `@throws`, do not vertically align all tags to a shared column.
3. Use normal single-space formatting on the first line of each tag.
4. Align only continuation (wrapped) lines under the description text.

## Default Parameter Responses

Use these as mandatory defaults for matching parameters. Choose the exact block using the explicit conditions below, and keep lines verbatim.

- Determine these parameters by inspecting code usage. If needed, traverse call stack until you reach where the variable is last used.
  - If you can't determine the matching parameter, list it in the response.

### \$date

- Use this when `$date` accepts only string dates/ranges:
- Common usages (not limited to):
  - ```\Piwik\Archive::createDataTableFromArchive```
```php
@param string $date The date or date range to process.
                    'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                    or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

- Use this when `$date` accepts either a string or `\Piwik\Date`:
- Common usages (not limited to):
  - ```\Piwik\Archive::build```
```php
@param Date|string $date The date or date range to process.
                         'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                         or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

### \$idSite and \$idSites

- ```$idSite``` and ```$idSites``` are effectively the same parameter, and should follow the same rules.

- Use this when a single numeric site ID is accepted:
```php
@param int $idSite The numeric ID of the website to query.
```

- Use this when single, multiple, comma-separated, or `all` site selectors are accepted:
- Common usages (not limited to):
  - ```\Piwik\Archive::createDataTableFromArchive```
```php
@param int|string|int[] $idSite Website ID(s) to query.
                         - Single site ID (e.g. 1)
                         - Multiple site IDs (e.g. [1, 4, 5])
                         - Comma-separated list ("1,4,5") or "all"
```


- Use when method uses selectors as a string
- Common usages (not limited to):
  - ```\Piwik\Site::getIdSitesFromIdSitesString```
```php
@param string|array $idSite Website ID(s) to query.
                            Accepts comma-separated IDs, "all", numeric IDs as strings, or ["all"].
```

[//]: # (### idSubtable)

[//]: # ()
[//]: # (- Use this when subtable selector accepts numeric IDs, `all`, or root:)

[//]: # (```php)

[//]: # (@param int|string|false $idSubtable Subtable ID to load, 'all' to load all subtables, or false for root.)

[//]: # (```)

### \$period

- Use this when `$period` is required and must be one of the standard period strings:
```php
@param 'day'|'week'|'month'|'year'|'range' $period The period to process, processes data for the period
                                                   containing the specified date.
```

- Use this when `$period` can be inferred and `false` is accepted:
```php
@param string|false $period Period to use: 'day', 'week', 'month', 'year', or 'range' (or false to infer).
```

### \$segment

- Use this when `$segment` is optional and can be false:
```php
@param string|false $segment (Optional) Custom segment to filter the report.
                             Example: "referrerName==twitter.com"
                             Supports AND (;) and OR (,) operators.
```
