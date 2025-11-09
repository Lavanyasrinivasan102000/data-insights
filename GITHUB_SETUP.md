# GitHub Setup Guide

This guide will help you add this project to GitHub.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in the details:
   - **Repository name**: `data-insights` (or your preferred name)
   - **Description**: "AI-powered data query system with natural language interface"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

## Step 2: Initialize Git (if not already done)

Open a terminal in the project root directory (`rag/`) and run:

```bash
# Check if git is already initialized
git status

# If not initialized, run:
git init
```

## Step 3: Add All Files

```bash
# Add all files to staging
git add .

# Check what will be committed (optional)
git status
```

**Note**: The `.gitignore` file will automatically exclude:
- `venv/` (Python virtual environment)
- `node_modules/` (Node.js dependencies)
- `.env` files (environment variables with secrets)
- `rag.db` (SQLite database)
- `catalog/` (uploaded files)
- `__pycache__/` (Python cache)
- `__MACOSX/` (macOS metadata)

## Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: AI-powered data query system

- Full-stack application with React frontend and FastAPI backend
- Natural language to SQL query generation using Google Gemini API
- Interactive data tables with pagination and filtering
- Automatic data cataloging and visualization
- Multi-file support with file selection
- Statistical analysis and anomaly detection
- Premium UI with Tailwind CSS"
```

## Step 5: Connect to GitHub Repository

Replace `<your-username>` and `<your-repo-name>` with your actual GitHub username and repository name:

```bash
# Add remote repository
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# Verify remote was added
git remote -v
```

## Step 6: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

If you encounter authentication issues, you may need to:
- Use a Personal Access Token instead of password
- Set up SSH keys
- Use GitHub CLI (`gh auth login`)

## Step 7: Verify on GitHub

1. Go to your repository on GitHub
2. Verify all files are present
3. Check that the README.md displays correctly
4. Verify that sensitive files (`.env`, `venv/`, `node_modules/`) are NOT in the repository

## Step 8: Add Repository Topics (Optional)

On your GitHub repository page:
1. Click the gear icon (⚙️) next to "About"
2. Add topics like:
   - `react`
   - `typescript`
   - `fastapi`
   - `python`
   - `data-analysis`
   - `ai`
   - `natural-language-processing`
   - `data-visualization`

## Step 9: Create .env.example Files (Recommended)

Create example environment files so others know what variables are needed:

**Backend `.env.example`:**
```bash
# Copy this file to .env and fill in your actual values
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./rag.db
CATALOG_DIR=./catalog
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=csv,json
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

**Frontend `.env.example`:**
```bash
# Copy this file to .env and fill in your actual values
REACT_APP_API_URL=http://localhost:8000
```

Then commit these:
```bash
git add backend/.env.example frontend/.env.example
git commit -m "Add .env.example files for configuration reference"
git push
```

## Troubleshooting

### Authentication Issues

If you get authentication errors:
```bash
# Use Personal Access Token
# Generate one at: https://github.com/settings/tokens
# Then use it as password when prompted

# Or use SSH instead:
git remote set-url origin git@github.com:<your-username>/<your-repo-name>.git
```

### Large Files

If you get errors about large files:
```bash
# Check for large files
git ls-files | xargs ls -lh | sort -k5 -hr | head -20

# If you accidentally added large files, remove them:
git rm --cached <large-file>
git commit -m "Remove large files"
```

### Already Have a Repository?

If you already initialized git and want to push to a new GitHub repo:
```bash
# Remove old remote (if exists)
git remote remove origin

# Add new remote
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# Push
git push -u origin main
```

## Next Steps

After pushing to GitHub:

1. **Add a LICENSE file** (if you want to use MIT license):
   ```bash
   # Create LICENSE file with MIT license text
   # Or use GitHub's web interface to add it
   ```

2. **Set up GitHub Actions** (optional):
   - Create `.github/workflows/` directory
   - Add CI/CD workflows for testing and deployment

3. **Add badges to README** (optional):
   - Build status
   - License
   - Version

4. **Create releases** (when ready):
   - Tag versions: `git tag v1.0.0`
   - Push tags: `git push --tags`
   - Create releases on GitHub

## Security Checklist

Before pushing, ensure:
- ✅ No `.env` files are committed (check with `git status`)
- ✅ No API keys or secrets in code
- ✅ No database files (`*.db`, `*.sqlite`) are committed
- ✅ No uploaded files in `catalog/` directory
- ✅ No virtual environments (`venv/`, `node_modules/`) are committed
- ✅ `.gitignore` is properly configured

## Useful Git Commands

```bash
# Check status
git status

# View what will be committed
git diff --staged

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View commit history
git log --oneline

# Create a new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main
```

