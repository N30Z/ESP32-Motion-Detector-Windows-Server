# GitHub Path Redirects Guide

**For Repository Maintainers**

After the repository restructure (v2.0.0), many file paths have changed. This document provides guidance for setting up GitHub redirects to prevent broken links.

---

## Why Redirects?

- **External links** in blog posts, tutorials, issues may reference old paths
- **Bookmarks** users have saved will break
- **Search engines** have indexed old paths
- **GitHub issues** may reference old file locations

---

## Old → New Path Mappings

### Critical Redirects (High Traffic)

| Old Path | New Path | Priority |
|----------|----------|----------|
| `server/` | `Server/` | 🔴 HIGH |
| `esp32/` | `ESP32/Client/` | 🔴 HIGH |
| `clients/raspi/` | `Raspberry-Pi/Client/` | 🔴 HIGH |
| `docs/LINUX_SETUP.md` | `Linux/Linux.md` | 🟠 MEDIUM |
| `docs/RASPBERRY_PI.md` | `Raspberry-Pi/Raspberry.md` | 🟠 MEDIUM |

### Documentation Redirects

| Old Path | New Path | Priority |
|----------|----------|----------|
| `server/README.md` | `Server/README.md` | 🟠 MEDIUM |
| `esp32/README.md` | `ESP32/Client/README.md` | 🟠 MEDIUM |
| `clients/raspi/README.md` | `Raspberry-Pi/Client/README.md` | 🟡 LOW |
| `deploy/linux/systemd/motion-detector-server.service` | `Linux/Server/motion-detector-server.service` | 🟡 LOW |

---

## How to Implement Redirects

### Option 1: GitHub Pages Redirects (If Enabled)

Create `_redirects` file in root or `.github/` directory:

```
# ESP32 redirects
/esp32/* /ESP32/Client/:splat 301
/esp32/ /ESP32/ESP32.md 301

# Server redirects
/server/* /Server/:splat 301
/server/ /Server/ 301

# Raspberry Pi Client redirects
/clients/raspi/* /Raspberry-Pi/Client/:splat 301
/clients/raspi/ /Raspberry-Pi/Client/ 301

# Documentation redirects
/docs/LINUX_SETUP.md /Linux/Linux.md 301
/docs/RASPBERRY_PI.md /Raspberry-Pi/Raspberry.md 301
```

### Option 2: Stub Files with Meta Refresh

Create stub HTML files at old paths (only for GitHub Pages):

**Example: `server/index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=../Server/">
    <title>Redirecting...</title>
</head>
<body>
    <p>This page has moved to <a href="../Server/">Server/</a></p>
</body>
</html>
```

### Option 3: README Stub Files (Recommended for GitHub)

Create README stubs at old locations that guide users:

**`server/README.md`:**
```markdown
# ⚠️ MOVED

This directory has been renamed.

**New location:** [../Server/](../Server/)

Please update your bookmarks and links.
```

### Option 4: .github/workflows Redirect Action

Create `.github/workflows/redirects.yml`:

```yaml
name: Handle Redirects
on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  check-old-paths:
    runs-on: ubuntu-latest
    steps:
      - name: Check for old path references
        run: |
          # Script to detect old paths in issues/PRs and comment with new paths
          echo "Checking for old path references..."
```

---

## Implementation Steps

### Step 1: Create Stub Files (Immediate)

```bash
# Create stub READMEs for old paths
mkdir -p server esp32 clients/raspi deploy

# server/README.md
echo "# ⚠️ MOVED → [../Server/](../Server/)" > server/README.md

# esp32/README.md
echo "# ⚠️ MOVED → [../ESP32/Client/](../ESP32/Client/)" > esp32/README.md

# clients/raspi/README.md
mkdir -p clients/raspi
echo "# ⚠️ MOVED → [../../Raspberry-Pi/Client/](../../Raspberry-Pi/Client/)" > clients/raspi/README.md
```

### Step 2: Update Issue Templates

Add to `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
## File Paths

⚠️ **Note:** Repository structure was updated in v2.0.0

If referencing files, use new paths:
- `Server/` (not `server/`)
- `ESP32/Client/` (not `esp32/`)
- `Raspberry-Pi/Client/` (not `clients/raspi/`)

See [CHANGELOG.md](../CHANGELOG.md) for details.
```

### Step 3: Pin Issue with Migration Guide

Create a pinned issue:

**Title:** "📌 Repository Restructured - Path Migration Guide"

**Content:**
```markdown
The repository structure was updated in v2.0.0 (2025-12-22).

## Old → New Paths

- `server/` → `Server/`
- `esp32/` → `ESP32/Client/`
- `clients/raspi/` → `Raspberry-Pi/Client/`
- `docs/LINUX_SETUP.md` → `Linux/Linux.md`
- `docs/RASPBERRY_PI.md` → `Raspberry-Pi/Raspberry.md`

## For Users

See [CHANGELOG.md](CHANGELOG.md) for migration instructions.

## For Contributors

Update all references to use new paths.
```

### Step 4: Update README (Already Done)

✅ README.md already updated with new structure diagram

---

## Testing Redirects

### Manual Tests

1. **GitHub Web Interface:**
   - Navigate to old path (e.g., `/blob/main/server/README.md`)
   - Verify stub file shows redirect message
   - Click link to new location
   - Verify new location loads

2. **Clone & Check:**
   ```bash
   git clone <repo-url>
   cd ESP32-Motion-Detector-Windows-Server

   # Check stubs exist
   cat server/README.md
   cat esp32/README.md
   cat clients/raspi/README.md
   ```

3. **Search Engine Test:**
   - Google: `site:github.com/N30Z/ESP32-Motion-Detector "server/README"`
   - Verify stub files show in results
   - Verify they redirect to new locations

---

## Monitoring Broken Links

### GitHub Insights

Check GitHub Insights → Traffic → Referrals for:
- 404 errors from old paths
- External sites linking to old paths

### Tools

- **GitHub Link Checker Action:** Automatically scan for broken links
- **Google Search Console:** Monitor 404s from search engines

---

## Recommended Implementation Priority

### Phase 1: Immediate (Done)
- ✅ Deprecation notices in old docs (`docs/LINUX_SETUP.md`, `docs/RASPBERRY_PI.md`)
- ✅ CHANGELOG.md with migration guide
- ✅ README.md updated

### Phase 2: Next Commit (This PR)
- [ ] Create stub README files at old directory paths
- [ ] Update issue templates
- [ ] Create pinned issue

### Phase 3: Future
- [ ] Monitor 404 errors
- [ ] Set up automated link checking
- [ ] Eventually remove stubs (after 6-12 months)

---

## Alternative: Do Nothing

**Considerations:**

**Pros:**
- Simpler
- Git history preserves file moves
- GitHub shows "renamed" in commit view

**Cons:**
- External links break immediately
- User confusion
- SEO impact

**Recommendation:** Implement at least stub README files (low effort, high value).

---

## Reference

- [GitHub Pages Redirects](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain-and-the-www-subdomain-variant)
- [HTTP 301 Permanent Redirect](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/301)
- [Google Webmaster Guidelines](https://developers.google.com/search/docs/advanced/crawling/301-redirects)

---

**Last Updated:** 2025-12-22
**Related:** CHANGELOG.md, AUDIT_REPORT.md
