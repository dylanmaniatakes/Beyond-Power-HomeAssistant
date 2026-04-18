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
3. Keep the manifest URLs pointed at the live GitHub repo:
   - `documentation`: `https://github.com/dylanmaniatakes/Beyond-Power-HomeAssistant#readme`
   - `issue_tracker`: `https://github.com/dylanmaniatakes/Beyond-Power-HomeAssistant/issues`
   - `codeowners`: `@dylanmaniatakes`
4. Use the included GitHub Actions:
   - `.github/workflows/validate.yml` for HACS validation
   - `.github/workflows/hassfest.yml` for Home Assistant validation
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
- Manifest has `documentation`, `issue_tracker`, `codeowners`, and `version`
- Brand assets included
- HACS action passing
- Hassfest passing
- At least one GitHub release
- Repository description, issues, and topics enabled

## GitHub Repo Settings Still Needed

These are checked on GitHub itself and cannot be enforced from the files alone:

- repository description
- issues enabled
- topics added
- at least one GitHub release before default-store submission

## Branding Note

Home Assistant now supports local integration brand assets, and this repository includes them inside the integration. To make HACS/custom-repository presentation more compatible too, this repo also carries matching repository-level `brand/` assets and root `icon.png` / `logo.png` copies. Default-store submission may still require following whatever the current HACS/brands policy is at that time.

## Brand Assets

This integration already includes local brand images for Home Assistant 2026.3+:

- `custom_components/voltra/brand/icon.png`
- `custom_components/voltra/brand/logo.png`
- `custom_components/voltra/brand/dark_icon.png`
- `custom_components/voltra/brand/dark_logo.png`

Repository-level brand copies are also included for HACS/repository presentation:

- `brand/icon.png`
- `brand/logo.png`
- `icon.png`
- `logo.png`
