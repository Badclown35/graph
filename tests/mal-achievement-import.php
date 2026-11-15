<?php
require_once __DIR__ . '/../src/Enums/Enum.php';
require_once __DIR__ . '/../src/Enums/UserListStatus.php';
require_once __DIR__ . '/../src/Helpers/MalAchievementImportHelper.php';

function expectSame($expected, $actual, $message)
{
    if ($expected !== $actual) {
        fwrite(STDERR, $message . "\nExpected: " . var_export($expected, true) . "\nActual: " . var_export($actual, true) . "\n");
        exit(1);
    }
}

$xml = '<?xml version="1.0"?><myanimelist><anime><series_animedb_id>123</series_animedb_id><series_title>Example Season 2</series_title><my_score>9</my_score><my_status>2</my_status><my_watched_episodes>12</my_watched_episodes><my_times_watched>2</my_times_watched><series_episodes>12</series_episodes></anime><anime><series_animedb_id>456</series_animedb_id><series_title>Another Show</series_title><my_score>0</my_score><my_status>4</my_status><my_watched_episodes>3</my_watched_episodes><series_episodes>24</series_episodes></anime></myanimelist>';
$rows = MalAchievementImportHelper::parse($xml);
expectSame(2, count($rows), 'XML parser must preserve separate MAL entries.');
expectSame(123, $rows[0]['mal_id'], 'XML MAL ID must be retained.');
expectSame('F', $rows[0]['status'], 'Completed status must map to Graph finished status.');
expectSame('D', $rows[1]['status'], 'Dropped status must map to Graph dropped status.');
expectSame(2, $rows[0]['rewatches'], 'XML rewatch count must be retained.');

$csv = "anime_id,anime_title,my_score,my_status,my_watched_episodes,my_times_watched,anime_episodes\n123,\"Example, Season 2\",8,1,5,3,12\n456,Another Show,0,6,0,0,24\n";
$csvRows = MalAchievementImportHelper::parse($csv);
expectSame(2, count($csvRows), 'CSV parser must read all rows.');
expectSame('Example, Season 2', $csvRows[0]['title'], 'CSV parser must preserve quoted commas.');
expectSame('C', $csvRows[0]['status'], 'Watching status must map to Graph completing status.');
expectSame('P', $csvRows[1]['status'], 'Plan-to-watch status must map to Graph planned status.');
expectSame(3, $csvRows[0]['rewatches'], 'CSV rewatch count must be retained.');

$malformedCsvRejected = false;
try {
    MalAchievementImportHelper::parse("anime_id,anime_title\n123,\"Broken title\n");
} catch (InvalidArgumentException $error) {
    $malformedCsvRejected = true;
}
expectSame(true, $malformedCsvRejected, 'CSV parser must reject unfinished quoted fields.');

$duplicateCsvRejected = false;
try {
    MalAchievementImportHelper::parse("anime_id,anime_title\n123,First\n123,Duplicate\n");
} catch (InvalidArgumentException $error) {
    $duplicateCsvRejected = true;
}
expectSame(true, $duplicateCsvRejected, 'Importer must reject duplicate MAL IDs rather than double-counting entries.');

echo "MAL achievement import parser checks passed.\n";
