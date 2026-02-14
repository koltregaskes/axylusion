# Admin Access - How to Login

## What is Decap CMS?

**Decap CMS** (formerly Netlify CMS) is a content management system that lets you edit website content through a web interface instead of editing files directly.

## Current Status: Not Yet Configured

⚠️ **The admin page is not currently functional** because it requires either:

1. **Netlify hosting** with Netlify Identity configured, OR
2. **GitHub OAuth** authentication setup

## How to Edit Content (For Now)

Since the CMS isn't configured yet, edit content directly:

### Option 1: Edit on GitHub
1. Go to https://github.com/koltregaskes/axylusion
2. Navigate to `data/gallery.json`
3. Click the pencil icon (✏️) to edit
4. Make your changes
5. Click "Commit changes"

### Option 2: Edit Locally
1. Clone the repo: `git clone git@github.com:koltregaskes/axylusion.git`
2. Edit `data/gallery.json` in your text editor
3. Commit and push:
   ```bash
   git add data/gallery.json
   git commit -m "Update gallery"
   git push
   ```

## Future: Enabling the Admin Panel

To make the `/admin` page work, choose one of these options:

### Option A: Move to Netlify (Recommended)
1. Import GitHub repo to Netlify
2. Enable Netlify Identity in site settings
3. Invite yourself as a user
4. Login at axylusion.com/admin

### Option B: GitHub OAuth (More Complex)
1. Create GitHub OAuth app
2. Configure backend in `admin/config.yml`
3. Set up authentication proxy

## Questions?

For now, stick with direct file editing on GitHub or locally. It's simpler and more reliable.

---

*Last updated: 2026-02-14*
