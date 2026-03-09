---
name: matomo-documentation
description: Create and update Matomo code documentation.
---

# Matomo Documentation

## Overview

Use this skill for Matomo PHP documentation tasks. 

## Trigger Conditions

Use this skill when the task involves one or more of:

1. Writing or fixing PHPDoc for .php files.
2. Correcting `@param`, `@return`, or `@throws` tags.
3. Improving PHPDoc type precision, including array shapes.
4. Adding a new public method that needs documentation

## Method Docblock Rules

Every public method must have PHPDoc immediately above it.

1. Summary line (two sentences max).
   - Keep existing summary if it already exists, don't re-write summaries. 
     - This is a hard rule that should not be ignored based on inference
2. `@param` tags.
   - Keep parameter order identical to method signature.
   - Use accurate and specific types.
   - Use specific array shapes when applicable.
   - Add examples only when confidently derived from code behavior.
   - If a parameter has a default of false, document this as null
     - e.g. ```foo($bar = false) -> @param string|null $bar```
     - This is a hard rule that should not be ignored based on inference. The only time it can be ignored, is if the param is a boolean (accepts true & false).
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

## API File-Specific Rules
When working with API.php files, extra rules apply:
1. File summary
   - Include a summary of the class at the top of the file.
       - First line should be API for plugin {pluginName}
       - Then a summary that details what the methods in the API class do
       - Include a getInstance @method tag ```@method static \Piwik\Plugins\Events\API getInstance()```

      Example:
     ```
     /**
      * API for plugin RollUpReporting.
      *
      * Exposes endpoints to create, update, and list roll-up sites, including their
      * source site mappings, timezone, and currency.
      *
      * @method static \Piwik\Plugins\RollUpReporting\API getInstance()
      */
     ```



## Default Parameter Responses

Use these as mandatory defaults for matching parameters.

- Determine these parameters by inspecting code usage. If needed, traverse call stack until you reach where the variable is last used.
  - If you can't determine the matching parameter, list it in the reply of this prompt.

### \$date

- Use this when `$date` accepts only string dates/ranges
- Common usages (not limited to):
  - ```\Piwik\Archive::createDataTableFromArchive```
```php
@param string $date The date or date range to process.
                    'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                    or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

- Use this when `$date` accepts either a string or `\Piwik\Date`
- Common usages (not limited to):
  - ```\Piwik\Archive::build```
```php
@param Date|string $date The date or date range to process.
                         'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                         or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

### \$idSite and \$idSites

- ```$idSite``` and ```$idSites``` are effectively the same parameter, and should follow the same rules.
- Use this when a single numeric site ID is accepted
```php
@param int $idSite The numeric ID of the website to query.
```

- Use this when single, multiple, comma-separated, or `all` site selectors are accepted
- Common usages (not limited to):
  - ```\Piwik\Archive::createDataTableFromArchive```
```php
@param int|string|int[] $idSite Website ID(s) to query.
                         - Single site ID (e.g. 1)
                         - Multiple site IDs (e.g. [1, 4, 5])
                         - Comma-separated list ("1,4,5") or "all"
```

- Use when method uses selectors as a string or an array of strings
- Common usages (not limited to):
  - ```\Piwik\Site::getIdSitesFromIdSitesString```
```php
@param string|array $idSite Website ID(s) to query.
                            Accepts comma-separated IDs, "all", numeric IDs as strings, or ["all"].
```

### \$period

- Use this when `$period` is required and must be one of the standard period strings:
- Common usages (not limited to):
    - ```\Piwik\Archive::build```
```php
@param 'day'|'week'|'month'|'year'|'range' $period The period to process, processes data for the period
                                                   containing the specified date.
```

### \$segment

- Use this for `$segment` parameters:
- Common usages (not limited to):
  - ```\Piwik\Archive::build```
```php
@param string|null $segment Custom segment to filter the report.
                            Example: "referrerName==example.com"
                            Supports AND (;) and OR (,) operators.
```
