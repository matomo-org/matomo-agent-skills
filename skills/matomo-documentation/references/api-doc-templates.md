# API Doc Templates

Use these templates and examples only when the task needs detailed parameter text or minimal internal-method examples.

## Public API Templates

Use these descriptive templates for public API methods only. The final type and description must match the actual accepted public input in the code.

- Determine the final parameter contract by inspecting the method signature and how the value is normalized or consumed.
- Validate any existing parameter documentation against the code before reusing it.
- Do not trust existing parameter docblocks for the final type. Use native types when present; otherwise derive the contract from code behavior and forwarded helper contracts.
- For public API methods, document request-facing inputs, not broader internal PHP flexibility.
- For public API methods, always include parameter descriptions, even for straightforward parameters.

## `$date`

- For public API methods, document `$date` as `string`.
- Use this when the public method accepts date strings or date ranges via API request input.

```php
@param string $date The date or date range to process.
                    'YYYY-MM-DD', magic keywords (today, yesterday, lastWeek, lastMonth, lastYear),
                    or date range (ie, 'YYYY-MM-DD,YYYY-MM-DD', lastX, previousX).
```

## `$idSite` and `$idSites`

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

- If a public API method forwards `$idSite` unchanged to `Archive::build()`, `Archive::createDataTableFromArchive()`, or another helper that clearly accepts multi-site selectors, document `$idSite` as multi-site. Do not keep or generate `@param int $idSite` just because an older docblock used it.
- Keep the single-site `int` form only when the code clearly narrows the contract to one site before the value is used.

## `$period`

- Use this when `$period` must be one of the standard archive period strings.

```php
@param 'day'|'week'|'month'|'year'|'range' $period The period to process, processes data for the period
                                                   containing the specified date.
```

## `$segment`

- Match the documented type to the actual accepted public input.
- Valid forms are `string|null` or `string|null|false`, depending on the method contract.
- Reuse the standard example and operator description for public API `$segment` docblocks instead of rewriting or tailoring it.

```php
@param string|null $segment Custom segment to filter the report.
                            Example: "referrerName==example.com"
                            Supports AND (;) and OR (,) operators.
```

## Internal Type-Only Guidance

Use this guidance for protected, private, and other non-public methods.

- Add or fix type-only `@param` tags when native parameter types are missing or too broad.
- Add or fix type-only `@return` tags when native return types are missing or too broad.
- If native types fully cover the contract, omit redundant PHPDoc instead of rewriting it.
- Add descriptions only when they provide non-obvious information such as array structure, sentinel values, or special normalization behavior.

### Internal Type Example

```php
@param Date|string $date
```

## Internal Method Examples

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
 * @param int $idSite The numeric ID of the website to query.
 */
public function get($idSite, $period, $date, $segment = false)
{
    return Archive::createDataTableFromArchive('Example_record', $idSite, $period, $date, $segment);
}
```

Good:

```php
/**
 * @param int|string|int[] $idSite Website ID(s) to query.
 *                                 - Single site ID (e.g. 1)
 *                                 - Multiple site IDs (e.g. [1, 4, 5])
 *                                 - Comma-separated list ("1,4,5") or "all"
 */
public function get($idSite, $period, $date, $segment = false)
{
    return Archive::createDataTableFromArchive('Example_record', $idSite, $period, $date, $segment);
}
```

Bad:

```php
/**
 * @param int $limit
 */
public function getList($limit)
{
    return $this->fetchList($limit);
}
```

Good:

```php
/**
 * @param int|string $limit
 */
public function getList($limit)
{
    return $this->fetchList($limit);
}
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

Bad:

```php
/**
 * @return array
 */
private function normalizeConfig(array $config): array
```

Good:

```php
/**
 * @return array{enabled: bool, threshold: int}
 */
private function normalizeConfig(array $config): array
```

Bad:

```php
/**
 * Returns whether the feature is enabled.
 * @return bool
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

Keep a non-public summary only when it adds remarkable information, for example non-obvious normalization behavior, sentinel values, or important side effects not already clear from the signature and tags.
