# Testing Unreleased Fixes

This guide explains how to install and test unreleased fixes from specific branches or pull requests before they are officially released.

## Why Test Pre-Release Code?

When a bug fix or new feature is developed, it goes through these stages:
1. **Pull Request (PR)** - Code is submitted for review
2. **Merged to main** - Code passes review and is merged
3. **Release** - A new version is published to HACS

Testing pre-release code helps:
- Verify fixes work on your specific device
- Catch issues before they affect all users
- Speed up the release process

## Prerequisites

- Home Assistant with HACS installed
- Basic familiarity with HACS custom repository features

## Method 1: Install from a Branch (Recommended)

Use this when a maintainer asks you to test code from `main` or a specific branch.

### Steps

1. **Remove the existing installation** (if installed via HACS)
   - Go to **HACS → Integrations**
   - Find **Dreo Smart Device Integration**
   - Click the three dots menu → **Remove**
   - Restart Home Assistant

2. **Add as a custom repository**
   - Go to **HACS → Integrations**
   - Click the three dots menu (top right) → **Custom repositories**
   - Enter:
     - **Repository:** `JeffSteinbok/hass-dreo`
     - **Category:** `Integration`
   - Click **Add**

3. **Install from the branch**
   - Find **Dreo Smart Device Integration** in HACS
   - Click on it to open details
   - Click the three dots menu → **Redownload**
   - Check **Show beta versions** if testing a beta
   - Or select a specific version/branch from the dropdown
   - Click **Download**

4. **Restart Home Assistant**
   - Go to **Settings → System → Restart**

5. **Test and report back**
   - Test the specific functionality that was fixed
   - Report results on the GitHub issue or PR

## Method 2: Install from a Pull Request

Use this when testing code from an open PR that hasn't been merged yet.

### Steps

1. **Find the PR branch name**
   - Go to the PR on GitHub (e.g., `https://github.com/JeffSteinbok/hass-dreo/pull/123`)
   - Note the branch name shown at the top (e.g., `username:fix-feature-branch`)

2. **Download the PR code manually**
   
   **Option A: Using HACS (if the branch is in the main repo)**
   - Follow Method 1, but select the PR branch in step 3
   
   **Option B: Manual download**
   - Go to the PR on GitHub
   - Click **Code → Download ZIP**
   - Extract to your Home Assistant `config/custom_components/` directory
   - Ensure the folder is named `dreo`

3. **Restart Home Assistant**

## Method 3: Direct File Copy (Advanced)

For quick testing without HACS:

```bash
# SSH into your Home Assistant instance
cd /config/custom_components/

# Remove existing installation
rm -rf dreo

# Clone the specific branch
git clone -b main --single-branch https://github.com/JeffSteinbok/hass-dreo.git temp
mv temp/custom_components/dreo ./dreo
rm -rf temp

# Restart Home Assistant
```

## Reverting to Stable Release

To go back to the stable HACS release:

1. Remove the custom repository entry in HACS
2. Remove the integration files:
   - Go to **HACS → Integrations → Dreo** → Remove
3. Re-add from the default HACS store:
   - Search for "Dreo" in HACS Integrations
   - Install the stable version
4. Restart Home Assistant

## Providing Feedback

When reporting test results:

1. **Include your version info**
   - Home Assistant version
   - The branch/commit you tested
   - Your device model

2. **Describe what you tested**
   - Specific features or bug fixes
   - Steps you took

3. **Share results**
   - Did it work? Partially? Not at all?
   - Include relevant logs if there are issues

4. **Enable debug logging** if needed:
   ```yaml
   # In configuration.yaml
   logger:
     default: info
     logs:
       custom_components.dreo: debug
   ```

## Troubleshooting

### Integration doesn't load after update
- Check Home Assistant logs for errors
- Ensure the folder structure is correct: `config/custom_components/dreo/`
- Verify `manifest.json` exists in the dreo folder

### HACS shows wrong version
- Clear browser cache
- Try removing and re-adding the custom repository

### Device not responding after update
- Reload the integration: **Settings → Devices & Services → Dreo → Reload**
- Check if your device credentials are still valid

## Questions?

If you have issues with testing pre-release code, comment on the relevant GitHub issue or open a new one with the `question` label.
