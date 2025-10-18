# Documentation Deployment Guide

Complete guide to building, testing, and deploying your Yuho documentation site to GitHub Pages.

## Prerequisites

1. **Python 3.8+** installed
2. **Git** installed and configured
3. **GitHub repository** set up
4. **MkDocs and dependencies** installed

## Step 1: Install Dependencies

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions

# Or from the project requirements
pip install -r requirements-dev.txt
```

## Step 2: Test Locally

### Start Development Server

```bash
# Navigate to project root
cd /path/to/yuho

# Start the development server
mkdocs serve
```

The site will be available at **http://localhost:8000**

The server includes:
- **Live reload**: Changes update automatically
- **Search functionality**: Test the search
- **Navigation**: Test all links

### Development Server Options

```bash
# Serve on a different port
mkdocs serve -a localhost:8080

# Open browser automatically
mkdocs serve --open

# Only rebuild changed files (faster)
mkdocs serve --dirty

# Clean build (no caching)
mkdocs serve --clean
```

### Stop the Server

Press `Ctrl+C` in the terminal

## Step 3: Build Static Site

### Build the Site

```bash
# Build static HTML files
mkdocs build
```

This creates a `site/` directory with:
- All HTML files
- CSS and JavaScript
- Assets (images, etc.)
- Search index

### Build Options

```bash
# Strict mode (fail on warnings)
mkdocs build --strict

# Clean build (remove previous build)
mkdocs build --clean

# Verbose output
mkdocs build --verbose
```

### Verify Build

```bash
# Check the site directory
ls -la site/

# The site/ directory contains:
# - index.html
# - getting-started/
# - language/
# - cli/
# - assets/
# - search/
# - sitemap.xml
# - etc.
```

## Step 4: Deploy to GitHub Pages

### Method 1: Using MkDocs (Recommended)

**Automatic deployment to gh-pages branch:**

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

This command:
1. Builds the documentation
2. Creates/updates the `gh-pages` branch
3. Pushes to GitHub
4. Your site will be live at: `https://yourusername.github.io/yuho`

**Options:**

```bash
# Deploy with custom message
mkdocs gh-deploy -m "Update documentation"

# Force push (use with caution)
mkdocs gh-deploy --force

# Clean build before deploy
mkdocs gh-deploy --clean
```

### Method 2: Manual GitHub Pages Setup

1. **Build the site:**
   ```bash
   mkdocs build
   ```

2. **Push to gh-pages branch manually:**
   ```bash
   # Create gh-pages branch if it doesn't exist
   git checkout -b gh-pages
   
   # Copy built files
   cp -r site/* .
   
   # Add and commit
   git add .
   git commit -m "Deploy documentation"
   
   # Push to GitHub
   git push origin gh-pages
   
   # Switch back to main
   git checkout main
   ```

### Method 3: Using GitHub Actions (Automated)

The CI/CD pipeline (`.github/workflows/ci.yml`) automatically deploys on push to `main`:

```yaml
# Already configured in the workflow
deploy-docs:
  name: Deploy Documentation
  runs-on: ubuntu-latest
  needs: [test, code-quality, docs]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  steps:
    - name: Deploy to GitHub Pages
      run: mkdocs gh-deploy --force --clean --verbose
```

**To trigger automatic deployment:**

```bash
# Simply push to main branch
git add .
git commit -m "Update documentation"
git push origin main

# GitHub Actions will automatically:
# 1. Run tests
# 2. Build documentation
# 3. Deploy to GitHub Pages
```

## Step 5: Configure GitHub Pages

1. **Go to GitHub Repository Settings:**
   - Navigate to `https://github.com/yourusername/yuho/settings`

2. **Enable GitHub Pages:**
   - Scroll to "Pages" section
   - Source: Select `gh-pages` branch
   - Folder: `/ (root)`
   - Click "Save"

3. **Custom Domain (Optional):**
   - Add your custom domain if you have one
   - Create a CNAME file in your `docs/` directory:
     ```bash
     echo "docs.yourproject.com" > docs/CNAME
     ```

4. **Wait for Deployment:**
   - GitHub Pages typically takes 1-5 minutes to deploy
   - Your site will be available at:
     - `https://yourusername.github.io/yuho`
     - Or your custom domain

## Step 6: Verify Deployment

### Check Deployment Status

1. **GitHub Actions Tab:**
   - Go to `https://github.com/yourusername/yuho/actions`
   - Check the workflow status
   - Green checkmark = successful deployment

2. **GitHub Pages Section:**
   - In repository settings → Pages
   - Shows deployment status and URL

3. **Visit Your Site:**
   - Open `https://yourusername.github.io/yuho`
   - Test navigation
   - Test search
   - Check all pages load correctly

### Common Issues and Fixes

**Issue: 404 Page Not Found**
```bash
# Fix: Ensure gh-pages branch exists and has content
git checkout gh-pages
git pull origin gh-pages
ls  # Should see index.html and other files

# Redeploy
git checkout main
mkdocs gh-deploy --clean
```

**Issue: Site Not Updating**
```bash
# Fix: Force clean deployment
mkdocs gh-deploy --force --clean

# Or clear browser cache
# Ctrl+Shift+R (hard refresh)
```

**Issue: Build Errors**
```bash
# Fix: Build with verbose and strict mode to see errors
mkdocs build --strict --verbose

# Check mkdocs.yml for syntax errors
# Check all .md files for broken links
```

**Issue: Missing Assets**
```bash
# Fix: Ensure assets are in correct location
# Check that asset paths in markdown are correct
# Example: ../asset/logo/yuho_mascot.png
```

## Step 7: Update Documentation

### Regular Updates

```bash
# 1. Edit documentation files in docs/
vim docs/getting-started/installation.md

# 2. Test locally
mkdocs serve

# 3. Commit changes
git add docs/
git commit -m "Update installation guide"

# 4. Push to GitHub
git push origin main

# 5. Automatic deployment (if GitHub Actions configured)
# OR manual deployment:
mkdocs gh-deploy
```

### Adding New Pages

1. **Create new markdown file:**
   ```bash
   # Example: Add a new tutorial
   touch docs/tutorials/advanced-patterns.md
   ```

2. **Add content to the file:**
   ```markdown
   # Advanced Patterns
   
   Tutorial content here...
   ```

3. **Update mkdocs.yml navigation:**
   ```yaml
   nav:
     - Tutorials:
         - Advanced Patterns: tutorials/advanced-patterns.md
   ```

4. **Test and deploy:**
   ```bash
   mkdocs serve  # Test
   mkdocs gh-deploy  # Deploy
   ```

## Using Docker for Documentation

### Serve Documentation with Docker

```bash
# Using docker-compose
docker-compose up yuho-docs

# Visit http://localhost:8000
```

### Build in Docker

```bash
# Build using Docker
docker run --rm -v $(pwd):/app -w /app squidfunk/mkdocs-material build

# Deploy using Docker
docker run --rm -v $(pwd):/app -w /app squidfunk/mkdocs-material gh-deploy
```

## Documentation File Structure

```
docs/
├── index.md                     # Homepage
├── getting-started/             # Getting started guides
│   ├── installation.md
│   ├── quickstart.md
│   └── first-program.md
├── language/                    # Language reference
│   ├── overview.md
│   ├── syntax.md
│   └── types.md
├── cli/                         # CLI documentation
│   └── commands.md
├── development/                 # Developer docs
│   ├── architecture.md
│   └── contributing.md
├── stylesheets/                 # Custom CSS
│   └── extra.css
└── javascripts/                 # Custom JS
    └── extra.js
```

## Maintenance Tasks

### Weekly

- Check for broken links
- Update changelog
- Review and merge documentation PRs

### Monthly

- Update dependencies
- Check for MkDocs updates
- Review analytics (if enabled)

### As Needed

- Add new pages for new features
- Update examples
- Fix reported issues

## Advanced Configuration

### Custom Domain

1. **Add CNAME file:**
   ```bash
   echo "docs.yourproject.com" > docs/CNAME
   ```

2. **Configure DNS:**
   - Add CNAME record pointing to `yourusername.github.io`

3. **Update mkdocs.yml:**
   ```yaml
   site_url: https://docs.yourproject.com
   ```

### Analytics

Add to `mkdocs.yml`:
```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

### Versioning

Use `mike` for versioned documentation:
```bash
pip install mike

# Deploy version
mike deploy --push --update-aliases 3.0 latest

# Set default version
mike set-default --push latest
```

## Quick Reference

```bash
# Install
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions

# Develop
mkdocs serve

# Build
mkdocs build

# Deploy
mkdocs gh-deploy

# Deploy with commit message
mkdocs gh-deploy -m "Update docs"

# Clean deploy
mkdocs gh-deploy --clean --force
```

## Troubleshooting

### Check MkDocs Version
```bash
mkdocs --version
```

### Validate Configuration
```bash
mkdocs build --strict
```

### View Detailed Errors
```bash
mkdocs build --verbose
```

### Clear Cache
```bash
rm -rf site/
mkdocs build --clean
```

## Resources

- **MkDocs Documentation**: https://www.mkdocs.org
- **Material Theme**: https://squidfunk.github.io/mkdocs-material
- **GitHub Pages**: https://pages.github.com
- **Your Site**: https://yourusername.github.io/yuho

---

## Your Site URL

Once deployed, your documentation will be available at:

**https://gongahkia.github.io/yuho**

(Replace `gongahkia` with your GitHub username if different)

