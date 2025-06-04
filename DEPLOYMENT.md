# Deployment Guide for Product Processor

## Prerequisites

1. **GitHub Account**: Create a repository for your code
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
3. **Python Dependencies**: Ensure all scripts work locally first

## Step 1: Prepare for Deployment

1. Test locally:
```bash
npm run dev
```

2. Ensure all Python scripts use environment variables (already done)

3. Test a few processes to ensure they work

## Step 2: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Product Processor web app"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## Step 3: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and click "New Project"
2. Import your GitHub repository
3. Configure the project:
   - Framework Preset: Next.js
   - Root Directory: `./` (or `product-processor` if in a subdirectory)
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)

## Step 4: Set Environment Variables

In Vercel Project Settings > Environment Variables, add:

```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=REDACTED_SHOPIFY_TOKEN
OPENAI_API_KEY=REDACTED_OPENAI_KEY
```

## Step 5: Deploy

Click "Deploy" and Vercel will:
1. Install dependencies
2. Build the Next.js app
3. Deploy to their edge network
4. Provide you with a URL

## Important Notes

### Python Runtime
Vercel provides Python runtime in their serverless functions. However, for complex Python scripts:
- Consider breaking long-running processes into smaller chunks
- Use background jobs for processes that take > 5 minutes
- Monitor function logs in Vercel dashboard

### API Limits
- Vercel functions have a 5-minute timeout on Pro plans
- Consider implementing progress tracking for long processes
- Use proper error handling and retry logic

### Security
- Never commit `.env.local` to Git
- Rotate API keys regularly
- Use Vercel's environment variable encryption

## Post-Deployment

1. Test all processes on the live URL
2. Monitor logs in Vercel dashboard
3. Set up alerts for errors
4. Consider adding authentication for production use

## Troubleshooting

### Python Dependencies Not Found
- Vercel automatically installs from requirements.txt
- Ensure all dependencies are listed
- Check function logs for specific errors

### Timeout Errors
- Break long processes into batches
- Implement progress saving
- Consider using Vercel's Edge Functions for lighter tasks

### Memory Issues
- Vercel functions have memory limits
- Optimize Python scripts for memory usage
- Process data in chunks

## Support

For Vercel-specific issues: https://vercel.com/docs
For app-specific issues: Check the logs and error messages 