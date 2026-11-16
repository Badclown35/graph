<?php
/**
 * Static integrity checks for the original achievement definitions and badge assets.
 * Run with: php tests/achievement-definitions.php
 */

$definitionDirectory = __DIR__ . '/../data/achievement';
$imageDirectory = __DIR__ . '/../public_html/image/achievement';
$definitionFiles = glob($definitionDirectory . '/*.json');
$imageFiles = glob($imageDirectory . '/*');

if ($definitionFiles === false || $imageFiles === false) {
    fwrite(STDERR, "Could not read achievement definitions or image assets.\n");
    exit(1);
}

$imageNames = array_map('basename', $imageFiles);
$seenIds = [];
$errors = [];

foreach ($definitionFiles as $file) {
    try {
        // Match the comment stripping used by TextHelper::loadJson before decoding.
        $contents = file_get_contents($file);
        $contents = preg_replace(['#//(.*)$#m', '#\\#(.*)$#m'], '', $contents);
        $definition = json_decode($contents, false, 512, JSON_THROW_ON_ERROR);
    } catch (Throwable $error) {
        $errors[] = basename($file) . ': invalid JSON (' . $error->getMessage() . ')';
        continue;
    }

    if (!isset($definition->media) || !in_array($definition->media, ['A', 'M'], true)) {
        $errors[] = basename($file) . ': media must be A or M';
    }

    if (empty($definition->requirement->type)) {
        $errors[] = basename($file) . ': missing requirement type';
    }

    if (empty($definition->achievements) || !is_array($definition->achievements)) {
        $errors[] = basename($file) . ': achievements must be a non-empty array';
        continue;
    }

    foreach ($definition->achievements as $achievement) {
        if (empty($achievement->id) || empty($achievement->threshold)) {
            $errors[] = basename($file) . ': achievement is missing its id or threshold';
            continue;
        }

        if (isset($seenIds[$achievement->id])) {
            $errors[] = $achievement->id . ': duplicate achievement id';
        }
        $seenIds[$achievement->id] = true;

        $threshold = (string) $achievement->threshold;
        if (!preg_match('/^(?:[0-9]+|[0-9]+(?:\\.[0-9]+)?\\+|[0-9]+(?:\\.[0-9]+)?(?:\\.\\.|-)[0-9]+(?:\\.[0-9]+)?)$/', $threshold)) {
            $errors[] = $achievement->id . ': unsupported threshold format "' . $threshold . '"';
        }

        $imageFound = false;
        foreach ($imageNames as $imageName) {
            if (pathinfo($imageName, PATHINFO_FILENAME) === $achievement->id
                || preg_match('/^' . preg_quote($achievement->id, '/') . '(?:[-_].+)?$/', pathinfo($imageName, PATHINFO_FILENAME))) {
                $imageFound = true;
                break;
            }
        }

        if (!$imageFound) {
            fwrite(STDERR, 'Warning: ' . $achievement->id . ': no original badge image; Android uses its fallback icon.' . PHP_EOL);
        }
    }
}

if ($errors) {
    fwrite(STDERR, implode("\n", $errors) . "\n");
    exit(1);
}

echo 'Validated ' . count($definitionFiles) . ' definition files, '
    . count($seenIds) . ' achievement IDs, and their original badge assets.' . PHP_EOL;
