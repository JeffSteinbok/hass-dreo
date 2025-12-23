# Release Process

This document describes how to create a new release using the automated GitHub Actions workflow.

## Overview

The release automation workflow handles the entire release process, including:
- Running tests to ensure code quality
- Bumping the version number
- Creating a Git tag
- Publishing a GitHub release with artifacts

## Prerequisites

1. Ensure all changes for the release are merged into the target branch (e.g., `release/v1.4.0`)
2. Ensure all tests pass locally
3. Have appropriate permissions to trigger workflows and create releases

## Creating a Release

### Step 1: Trigger the Workflow

1. Navigate to the repository on GitHub
2. Go to **Actions** → **Release Automation**
3. Click **Run workflow**
4. Select the branch you want to release from (e.g., `release/v1.4.0`)
5. Enter the version number (e.g., `1.4.0`) - without the 'v' prefix
6. Click **Run workflow**

### Step 2: Monitor the Workflow

The workflow will automatically:

1. **Run Tests**: Execute all tests using Python 3.9 to ensure code quality
2. **Bump Version**: Update the version in `custom_components/dreo/manifest.json` using bump2version
3. **Commit Changes**: Commit the version bump with an automated message
4. **Create Tag**: Tag the commit with the version (e.g., `v1.4.0`)
5. **Build Artifact**: Create a ZIP file of the custom component
6. **Create Release**: Publish a GitHub release with release notes and the artifact

### Step 3: Verify the Release

After the workflow completes:

1. Check the **Releases** page to verify the new release is published
2. Download the artifact to verify it contains the correct files
3. Verify the version in `manifest.json` is updated correctly
4. Check that the tag was created

## Version Bumping

The workflow uses `bump2version` to manage version numbers. The configuration is in `.bumpversion.cfg`.

### Configuration

- **Current version**: Stored in `custom_components/dreo/manifest.json`
- **Version format**: `MAJOR.MINOR.PATCH` (e.g., `1.4.0`)
- **Auto-commit**: Enabled
- **Auto-tag**: Enabled

### How It Works

1. The workflow reads the current version from `manifest.json`
2. If the target version is different, it runs `bump2version` to update the file
3. The change is committed with message: `Bump version: {old} → {new}`
4. A Git tag is created automatically

## Release Artifacts

Each release includes:

- **dreo-v{version}.zip**: A ZIP archive containing the custom component
  - Contains the entire `custom_components/dreo/` directory
  - Can be extracted directly to Home Assistant's `custom_components` directory

## Release Notes

The workflow automatically generates release notes with:

- Version information
- Installation instructions
- Link to the README

You can manually edit the release notes after creation if needed.

## Troubleshooting

### Workflow Fails on Tests

If tests fail, the workflow will stop and the release will not be created. Fix the failing tests and trigger the workflow again.

### Version Already Exists

If the version already exists, the workflow will skip the version bump step but will still create the release and artifacts.

### Permission Issues

Ensure the workflow has `contents: write` permission (already configured) and that your branch protection rules allow the workflow to push commits and tags.

## Manual Release Process

If you need to create a release manually:

```bash
# 1. Update version
bump2version --new-version 1.4.0 patch

# 2. Push changes and tags
git push origin your-branch
git push origin --tags

# 3. Create artifact
cd custom_components
zip -r ../dreo-v1.4.0.zip dreo/

# 4. Create release on GitHub manually
# Upload the ZIP file as an artifact
```

## Additional Notes

- The workflow is configured to run on **any branch** via manual trigger
- Only **manual triggers** are supported (no automatic triggers)
- Python 3.9 is used for consistency with testing requirements
- All tests must pass before a release is created
