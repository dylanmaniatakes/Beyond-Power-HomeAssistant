# Publishing Beyond Power Voltra

Creator note: Technogizguy / Dylan Maniatakes.

## Share It Right Now

Because this repository is already the dedicated Home Assistant package, the easiest ways to share it today are:

1. Zip this repository and send it directly.
2. Push this repository to a public GitHub repo.

For HACS and store-style sharing, option 2 is the one you want.

## Recommended Path

1. Create a new public GitHub repository, for example `beyond-power-voltra-home-assistant`.
2. Push the contents of this repository to that repo root.
3. Add your real GitHub links to `custom_components/voltra/manifest.json`:
   - `documentation`
   - `issue_tracker`
   - `codeowners` using a real GitHub username, not a display name
4. Add GitHub Actions for HACS validation and Hassfest.
5. Create a real GitHub release, not just a tag.
6. Share it first as a HACS custom repository.
7. Once it is stable, submit it to the HACS default store.

## HACS Custom Repository

After the dedicated repo is public, a user can add it in HACS:

1. Open HACS.
2. Open the top-right menu.
3. Choose `Custom repositories`.
4. Paste the GitHub repo URL.
5. Select type `Integration`.

## Store Readiness Checklist

- Public GitHub repo
- One integration in `custom_components/voltra`
- `hacs.json` at repo root
- Brand assets included
- HACS action passing
- Hassfest passing
- At least one GitHub release
- Repository description, issues, and topics enabled

## Brand Assets

This integration already includes local brand images for Home Assistant 2026.3+:

- `custom_components/voltra/brand/icon.png`
- `custom_components/voltra/brand/logo.png`
- `custom_components/voltra/brand/dark_icon.png`
- `custom_components/voltra/brand/dark_logo.png`
