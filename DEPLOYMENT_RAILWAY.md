# Deploy to Railway (Supports Python + Node.js)

Railway is the easiest platform to deploy your Product Processor with full Python support.

## Quick Deploy Steps

1. **Install Railway CLI** (optional but helpful):
```bash
brew install railway
```

2. **Sign up at [railway.app](https://railway.app)**

3. **Deploy from GitHub**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `simonbowerbank/product-processor`
   - Railway will auto-detect both Node.js and Python

4. **Add Environment Variables**:
   In Railway dashboard, go to Variables and add:
   ```
   SHOPIFY_SHOP_URL=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=shpat_your_access_token
   OPENAI_API_KEY=sk-proj-your_openai_key
   ```

5. **Deploy**:
   - Railway will automatically:
     - Install Node.js dependencies
     - Install Python dependencies
     - Build and start your app
   - You'll get a URL like: `product-processor.up.railway.app`

## Advantages
- ✅ Full Python support
- ✅ Automatic deployments from GitHub
- ✅ Free tier available
- ✅ No configuration needed
- ✅ Supports long-running processes

## Alternative: Deploy with Railway CLI

```bash
# From your project directory
railway login
railway link
railway up

# Add environment variables
railway variables set SHOPIFY_SHOP_URL=your-store.myshopify.com
railway variables set SHOPIFY_ACCESS_TOKEN=shpat_your_access_token
railway variables set OPENAI_API_KEY=sk-proj-your_openai_key

# Deploy
railway up
```

Your app will be live in minutes with full Python support! 