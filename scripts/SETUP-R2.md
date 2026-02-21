# Image Hosting Migration: Cloudflare R2

## The Problem

All 1,519 gallery images use `cdn.midjourney.com` URLs which now return **403 Forbidden**. Images don't load on the website.

## The Solution: Cloudflare R2

Cloudflare R2 is free cloud storage designed for serving images on websites.

**Free tier includes:**
- 10 GB storage (enough for all images, videos, and music)
- 10 million reads per month (plenty for a portfolio site)
- No bandwidth/download charges ever
- Global CDN (fast loading worldwide)
- No credit card required

## Step-by-Step Setup

### 1. Create a Cloudflare Account

1. Go to [cloudflare.com](https://dash.cloudflare.com/sign-up)
2. Sign up with your email
3. No credit card needed

### 2. Enable R2 Storage

1. In the Cloudflare dashboard, click **R2 Object Storage** in the left sidebar
2. Click **Create bucket**
3. Name it `axylusion-images`
4. Choose **Automatic** for location
5. Click **Create bucket**

### 3. Set Up Public Access

For the images to be viewable on your website, the bucket needs public access:

1. Go to your `axylusion-images` bucket
2. Click **Settings**
3. Under **Public access**, click **Allow Access**
4. You'll get a public URL like: `https://pub-xxxxxxxxxxxx.r2.dev`
5. (Optional) You can later connect a custom domain like `images.axylusion.com`

### 4. Create an API Token

For the upload script to work:

1. Go to **R2 Object Storage** > **Manage R2 API Tokens**
2. Click **Create API token**
3. Give it a name like "Axylusion upload"
4. Permissions: **Object Read & Write**
5. Specify bucket: `axylusion-images`
6. Click **Create API Token**
7. **Save the Access Key ID and Secret Access Key** — you'll need these

### 5. Download Your Images

You need to download your published images from Midjourney:

**Option A: Bulk download from Midjourney Archive**
1. Go to [midjourney.com/archive](https://www.midjourney.com/archive)
2. Filter to show your created images
3. Select all and download

**Option B: Download individually**
1. Run `python scripts/migrate-images.py export-urls`
2. Visit each URL and download the image

The filenames should contain the job ID (UUID), which is how the script matches them to gallery entries.

### 6. Run the Migration

```bash
# Set environment variables
export R2_ACCOUNT_ID="your-cloudflare-account-id"
export R2_ACCESS_KEY_ID="your-r2-access-key"
export R2_SECRET_ACCESS_KEY="your-r2-secret-key"
export R2_BUCKET_NAME="axylusion-images"
export R2_PUBLIC_URL="https://pub-xxxxxxxxxxxx.r2.dev"

# Check how many images need migrating
python scripts/migrate-images.py status

# Scan your downloaded images
python scripts/migrate-images.py scan /path/to/downloaded/images

# Upload and update gallery
python scripts/migrate-images.py upload /path/to/downloaded/images
```

### 7. Verify

After running the upload:
- `data/gallery.json` will be updated with new R2 URLs
- `gallery.js` will be updated with new R2 URLs
- Open `index.html` locally to verify images load
- Commit and push to deploy

## File Sizes

Typical Midjourney image sizes:
- Standard quality: ~1-3 MB per image
- High quality (--quality 4): ~3-8 MB per image
- 1,519 images at ~2 MB average = ~3 GB total

This fits comfortably within R2's 10 GB free tier.

## Alternative: Google Drive (Not Recommended)

Google Drive can host files but:
- Rate-limited for frequent access
- URLs are clunky and can change
- Not designed for serving website images
- 15 GB free but poor performance at scale

Cloudflare R2 is purpose-built for this use case and is the recommended option.
