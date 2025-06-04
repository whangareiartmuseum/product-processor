# Setting Up Environment Variables in Vercel

## Required Environment Variables

The Product Processor app requires these environment variables to be set in Vercel:

1. **SHOPIFY_SHOP_URL** - Your Shopify store domain (e.g., `your-store.myshopify.com`)
2. **SHOPIFY_ACCESS_TOKEN** - Your Shopify Admin API access token (starts with `shpat_`)
3. **OPENAI_API_KEY** - Your OpenAI API key for AI recommendations (starts with `sk-`)

## How to Add Environment Variables in Vercel

### Option 1: Through Vercel Dashboard (Recommended)

1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on your `product-processor` project
3. Navigate to the **Settings** tab
4. Click on **Environment Variables** in the left sidebar
5. Add each variable:
   - **Key**: `SHOPIFY_SHOP_URL`
   - **Value**: `your-store.myshopify.com` (or your store URL)
   - **Environment**: Select all (Production, Preview, Development)
   - Click **Save**
6. Repeat for the other variables:
   - **SHOPIFY_ACCESS_TOKEN**: `REDACTED_SHOPIFY_TOKEN`
   - **OPENAI_API_KEY**: Your OpenAI API key
7. After adding all variables, go to the **Deployments** tab
8. Click the three dots menu on the latest deployment and select **Redeploy**

### Option 2: Using Vercel CLI

If you have the Vercel CLI installed:

```bash
# Add each environment variable
vercel env add SHOPIFY_SHOP_URL
vercel env add SHOPIFY_ACCESS_TOKEN
vercel env add OPENAI_API_KEY

# The CLI will prompt you for the values and which environments to add them to
```

### Option 3: During Deployment

You can also add environment variables when importing the project:

1. When importing from GitHub, Vercel will detect that environment variables are needed
2. You'll see a section to add environment variables before deployment
3. Add all three variables with their values

## Important Security Notes

1. **Never commit these values to your repository**
2. The app no longer has any hardcoded credentials - all sensitive data must come from environment variables
3. Make sure to use the correct values for your production store
4. Keep your access tokens secure and rotate them periodically

## Verifying Environment Variables

After setting up and redeploying:

1. Go to your deployed app
2. Try running any of the features (color extraction, recommendations, etc.)
3. If you see errors about missing environment variables, double-check:
   - The variable names are exactly as shown above (case-sensitive)
   - There are no extra spaces in the values
   - You've redeployed after adding the variables

## Local Development

For local development, create a `.env.local` file in the project root:

```env
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=REDACTED_SHOPIFY_TOKEN
OPENAI_API_KEY=your-openai-api-key
```

This file is already in `.gitignore` and won't be committed to the repository. 