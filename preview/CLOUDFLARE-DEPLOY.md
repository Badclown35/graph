# Deploy the Graph achievement preview to Cloudflare Pages

This is a static UI preview, not the live PHP application. The MAL file parser runs locally in the browser and does not upload the export.

## One-time Cloudflare setup

1. Sign in to the Cloudflare dashboard and open **Workers & Pages**.
2. Choose **Create application** → **Pages** → **Connect to Git**.
3. Authorize Cloudflare to access GitHub, then select `Badclown35/graph`.
4. Select the branch `feature/achievement-dashboard-v1`.
5. Set the build settings:
   - Framework preset: **None**
   - Build command: `bash scripts/build-cloudflare-preview.sh`
   - Build output directory: `dist`
   - Root directory: leave blank (repository root)
6. Deploy.

The build copies the preview page and the repository's original achievement badge images into the static output. Subsequent commits to the feature branch automatically redeploy. Do not select `main`.

## What this preview does and does not do

- Responsive dashboard layout with search and achievement filters.
- Original Graph badge artwork.
- Local XML/CSV file-format parsing and entry counting.
- No upload, account login, MAL API write, or persistent storage.
- Sample achievement cards only: the PHP achievement evaluator and Graph database are not connected, so this is not yet a verified personal achievement result.

## Manual build

Run `bash scripts/build-cloudflare-preview.sh` from the repository root. The deployable static site is written to `dist/`.
