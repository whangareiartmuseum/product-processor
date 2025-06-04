# Deployment Guide - Vercel

This guide will help you deploy the Product Processor app to Vercel with Python Serverless Functions support.

## Prerequisites

- Vercel account (free tier works)
- GitHub repository with the Product Processor code
- Environment variables ready

## Important Note on Node.js Version

⚠️ **Critical**: This project requires Node.js 18.x for Python serverless functions to work properly. The `package.json` is configured with `"engines": { "node": "18.x" }` to ensure compatibility. Do not change this to Node.js 20.x or higher as it will cause Python functions to fail.

## Deployment Steps

### 1. Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub repository
4. Select the repository containing the Product Processor code

### 2. Configure Build Settings

Vercel should auto-detect the Next.js framework. Ensure these settings:

- **Framework Preset**: Next.js
- **Root Directory**: `./` (or the path to your product-processor folder)
- **Build Command**: `npm run build` (default)
- **Output Directory**: `.next` (default)
- **Node.js Version**: Will use 18.x from package.json

### 3. Configure Python Support

The Python serverless functions are already set up in the `/api` directory:
- `/api/colors-all.py` - Extract all product colors
- `/api/colors-missing.py` - Process missing colors only  
- `/api/colors-single.py` - Single product processing
- `/api/colors-report.py` - Generate contrast reports
- `/api/recommendations.py` - AI product recommendations
- `/api/metafields-inspect.py` - Inspect metafields

Each Python file follows Vercel's serverless function format with a `handler` class.

### 4. Set Environment Variables

In Vercel's project settings, add these environment variables:

```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=REDACTED_SHOPIFY_TOKEN
OPENAI_API_KEY=REDACTED_OPENAI_KEY_PARTIAL....[your full key]
```

### 5. Python Dependencies

The `requirements.txt` file in the root directory specifies the Python packages:
```
requests
numpy
openai
tqdm
Pillow
```

Vercel will automatically install these dependencies during deployment.

### 6. Deploy

1. Click "Deploy"
2. Wait for the build to complete (usually 2-3 minutes)
3. Your app will be live at `https://[your-project-name].vercel.app`

## How It Works

- **Local Development**: The app uses Node.js to spawn Python processes
- **Production (Vercel)**: The frontend detects Vercel environment and calls Python serverless functions directly
- **Automatic Detection**: The app automatically switches between local and serverless modes

## Troubleshooting

### Python Functions Not Working

1. Ensure Python files are in the root `/api` directory (not nested)
2. Check that each Python file has a `handler` class with `do_POST` method
3. Verify environment variables are set in Vercel dashboard
4. Ensure `requirements.txt` is in the project root (not in `/api`)
5. Confirm Node.js 18.x is being used (check build logs)

### Build Failures

If the build fails with pip errors:
- Ensure you're using Node.js 18.x (specified in package.json)
- Check that `requirements.txt` doesn't have conflicting versions
- Verify all package names are correct

### "Unable to find any supported Python versions" Error

This error occurs when using Node.js 20.x or higher. The fix is already implemented:
- `package.json` specifies `"engines": { "node": "18.x" }`
- Do not override this setting in Vercel project settings

### Module Import Errors

- Ensure `requirements.txt` is in the project root directory
- Check that all required packages are listed
- The Python scripts import from `python_scripts/` directory - ensure this directory structure is maintained

## Testing

After deployment:
1. Visit your Vercel URL
2. Try "Inspect Metafields" first (doesn't modify data)
3. Test other features as needed

## Monitoring

- Check Vercel's Function logs for Python execution details
- Use the browser console for frontend errors
- Vercel provides real-time logs for debugging

## Updating

When you push changes to GitHub:
1. Vercel automatically rebuilds and redeploys
2. Python dependencies are reinstalled from `requirements.txt`
3. Environment variables persist across deployments

## Local Development

For development:

```bash
npm run dev
```

The app automatically detects local environment and runs Python scripts directly.

## Post-Deployment

1. Test all processes on the live URL
2. Monitor logs in Vercel dashboard
3. Set up alerts for errors
4. Consider adding authentication for production use

## Support

For Vercel-specific issues: https://vercel.com/docs
For app-specific issues: Check the logs and error messages 