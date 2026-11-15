<?php
/**
 * Read-only MyAnimeList export parser shared by the achievement import flow.
 *
 * This deliberately returns plain entry data. It never writes to a Graph user
 * collection or calls a MyAnimeList write endpoint.
 */
class MalAchievementImportHelper
{
    public static function parse($raw)
    {
        if (!is_string($raw) || trim($raw) === '') {
            throw new InvalidArgumentException('The MAL export is empty.');
        }

        return ltrim($raw) !== '' && strpos(ltrim($raw), '<') === 0
            ? self::parseXml($raw)
            : self::parseCsv($raw);
    }

    private static function parseXml($raw)
    {
        if (!function_exists('simplexml_load_string')) {
            throw new RuntimeException('XML support is unavailable on this server.');
        }

        $previous = libxml_use_internal_errors(true);
        $xml = simplexml_load_string($raw, 'SimpleXMLElement', LIBXML_NONET | LIBXML_NOCDATA);
        libxml_clear_errors();
        libxml_use_internal_errors($previous);

        if ($xml === false) {
            throw new InvalidArgumentException('The MAL XML export could not be parsed.');
        }

        $rows = [];
        foreach ($xml->anime as $item) {
            $row = self::normalizeRow([
                'mal_id' => (string) ($item->series_animedb_id ?? $item->anime_id ?? ''),
                'title' => (string) ($item->series_title ?? $item->anime_title ?? $item->title ?? ''),
                'score' => (string) ($item->my_score ?? ''),
                'status' => (string) ($item->my_status ?? ''),
                'progress' => (string) ($item->my_watched_episodes ?? ''),
                'rewatches' => (string) ($item->my_times_watched ?? ''),
                'total' => (string) ($item->series_episodes ?? $item->anime_episodes ?? ''),
            ]);
            if ($row !== null) {
                $rows[] = $row;
            }
        }

        if (!$rows) {
            throw new InvalidArgumentException('No anime entries were found in this MAL XML export.');
        }

        return $rows;
    }

    private static function parseCsv($raw)
    {
        $records = [];
        $row = [];
        $field = '';
        $quoted = false;
        $length = strlen($raw);

        for ($i = 0; $i < $length; $i++) {
            $char = $raw[$i];
            if ($char === '"' && $quoted && $i + 1 < $length && $raw[$i + 1] === '"') {
                $field .= '"';
                $i++;
            } elseif ($char === '"') {
                $quoted = !$quoted;
            } elseif ($char === ',' && !$quoted) {
                $row[] = $field;
                $field = '';
            } elseif (($char === "\n" || $char === "\r") && !$quoted) {
                $row[] = $field;
                $field = '';
                if (count(array_filter($row, 'strlen'))) {
                    $records[] = $row;
                }
                $row = [];
                if ($char === "\r" && $i + 1 < $length && $raw[$i + 1] === "\n") {
                    $i++;
                }
            } else {
                $field .= $char;
            }
        }

        $row[] = $field;
        if (count(array_filter($row, 'strlen'))) {
            $records[] = $row;
        }
        if (count($records) < 2) {
            throw new InvalidArgumentException('The MAL CSV export is empty or missing its header.');
        }

        $headers = array_map(function ($value) {
            return strtolower(trim(str_replace("\xEF\xBB\xBF", '', $value)));
        }, array_shift($records));

        $column = function ($names) use ($headers) {
            foreach ($names as $name) {
                $index = array_search($name, $headers, true);
                if ($index !== false) {
                    return $index;
                }
            }
            return null;
        };

        $indices = [
            'mal_id' => $column(['anime_id', 'series_animedb_id']),
            'title' => $column(['anime_title', 'title', 'series_title']),
            'score' => $column(['my_score']),
            'status' => $column(['my_status']),
            'progress' => $column(['my_watched_episodes']),
            'rewatches' => $column(['my_times_watched']),
            'total' => $column(['anime_episodes', 'series_episodes']),
        ];
        if ($indices['title'] === null || $indices['mal_id'] === null) {
            throw new InvalidArgumentException('The MAL CSV must include anime_id and anime_title columns.');
        }

        $rows = [];
        foreach ($records as $record) {
            $values = [];
            foreach ($indices as $key => $index) {
                $values[$key] = $index === null ? '' : ($record[$index] ?? '');
            }
            $normalized = self::normalizeRow($values);
            if ($normalized !== null) {
                $rows[] = $normalized;
            }
        }

        if (!$rows) {
            throw new InvalidArgumentException('No anime entries were found in this MAL CSV export.');
        }

        return $rows;
    }

    private static function normalizeRow(array $values)
    {
        $title = trim((string) ($values['title'] ?? ''));
        $malId = (int) ($values['mal_id'] ?? 0);
        if ($title === '' || $malId <= 0) {
            return null;
        }

        $status = trim((string) ($values['status'] ?? ''));
        $statusMap = [
            '1' => UserListStatus::Completing,
            '2' => UserListStatus::Finished,
            '3' => UserListStatus::OnHold,
            '4' => UserListStatus::Dropped,
            '6' => UserListStatus::Planned,
            'watching' => UserListStatus::Completing,
            'completed' => UserListStatus::Finished,
            'on-hold' => UserListStatus::OnHold,
            'on hold' => UserListStatus::OnHold,
            'dropped' => UserListStatus::Dropped,
            'plan to watch' => UserListStatus::Planned,
            'planned' => UserListStatus::Planned,
        ];

        return [
            'mal_id' => $malId,
            'title' => $title,
            'score' => max(0, min(10, (int) ($values['score'] ?? 0))),
            'status' => $statusMap[strtolower($status)] ?? UserListStatus::Unknown,
            'progress' => max(0, (int) ($values['progress'] ?? 0)),
            'rewatches' => max(0, (int) ($values['rewatches'] ?? 0)),
            'total' => max(0, (int) ($values['total'] ?? 0)),
        ];
    }
}
