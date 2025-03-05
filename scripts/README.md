# Multi-Remote Git Workflow

This directory contains scripts to help manage pushing code to multiple Git remotes, including the clean `frameworkreboot` remote.

## Available Scripts

### `push_to_all_remotes.bat` (Windows)

This script pushes your current branch to all configured remotes. For the `frameworkreboot` remote, it uses a special clean branch approach to avoid pushing sensitive information.

#### Usage:

```bash
# From the repository root
scripts\push_to_all_remotes.bat

# To force push (use with caution)
scripts\push_to_all_remotes.bat --force
```

## How It Works

The script handles different remotes in different ways:

1. For regular remotes (`origin`, `notion-operations`), it pushes your current branch directly.
2. For the `frameworkreboot` remote:
   - It creates/updates a clean branch (`clean-main`) without sensitive information
   - It pushes this clean branch to the `main` branch on the `frameworkreboot` remote
   - This approach ensures no sensitive information is pushed to the public repository

## Workflow Instructions

### Regular Development Workflow

1. Work on your code in the `main` branch (or any feature branch)
2. Commit your changes as usual:
   ```
   git add .
   git commit -m "Your commit message"
   ```
3. When ready to push to all remotes, use:
   ```
   scripts\push_to_all_remotes.bat
   ```
4. The script will:
   - Push directly to regular remotes
   - Create/update a clean branch for the `frameworkreboot` remote
   - Check for sensitive information before pushing to `frameworkreboot`
   - Automatically handle branch switching and return you to your original branch

### Adding New Sensitive Patterns

If you need to add more patterns to check for sensitive information, edit the `SENSITIVE_PATTERNS` list in `scripts/push_to_all_remotes.py`.

### Troubleshooting

- If you encounter issues with the script, make sure Python is installed and in your PATH
- Check that the `.gitignore` file is properly configured to exclude sensitive files
- If you need to force push (e.g., after rebasing), use the `--force` flag
- If the script fails during the clean branch process, you may need to manually return to your original branch with `git checkout main` 