# Deployment Guide for Product Processor

## Vercel Deployment (Recommended)

Vercel supports Python through Serverless Functions (Beta) with Python 3.12.

### Prerequisites

1. **GitHub Account**: Your code should be in the repository
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
3. **Environment Variables Ready**: Have your API keys ready

### Step 1: Connect GitHub to Vercel

Since you've already deployed to Vercel, you need to connect GitHub for automatic deployments:

1. Go to your [Vercel Dashboard](https://vercel.com/whangarei-art-museum/product-processor/settings/git)
2. Click "Connect Git Repository"
3. Select GitHub and authorize Vercel
4. Choose `simonbowerbank/product-processor`
5. Click "Connect"

### Step 2: Verify Environment Variables

In Vercel Project Settings > Environment Variables, ensure you have:

```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=REDACTED_SHOPIFY_TOKEN
OPENAI_API_KEY=REDACTED_OPENAI_KEY
```

### Step 3: Deploy

Once GitHub is connected, every push will automatically deploy. To manually redeploy:

```bash
vercel --prod
```

### How It Works

- **Frontend**: Next.js runs on Vercel's Edge Network
- **Python Processing**: Python scripts run as Serverless Functions
- **API Routes**: Next.js routes call Python functions when on Vercel

### Architecture

```
/app/api/            → Next.js API routes
/api/python/         → Python Serverless Functions
/python_scripts/     → Shared Python processing logic
```

### Limitations

- Python functions have a 5-minute timeout (Pro plan extends this)
- Memory limit is 3GB for serverless functions
- Cold starts may add 1-2 seconds on first request

### Monitoring

Check function logs in Vercel Dashboard:
- Go to Functions tab
- Click on any function to see logs
- Monitor for errors or timeouts

## Local Development

For development:

```bash
npm run dev
```

The app automatically detects local environment and runs Python scripts directly.

## Troubleshooting

### Python Dependencies Not Installing
- Ensure `Pipfile` specifies Python 3.12
- Check `requirements.txt` in `/api/python/`

### Function Timeouts
- Break long processes into smaller chunks
- Consider upgrading to Vercel Pro for longer timeouts

### Import Errors
- Verify paths in Python functions
- Check that all dependencies are in requirements.txt

## Post-Deployment

1. Test all processes on the live URL
2. Monitor logs in Vercel dashboard
3. Set up alerts for errors
4. Consider adding authentication for production use

## Support

For Vercel-specific issues: https://vercel.com/docs
For app-specific issues: Check the logs and error messages 