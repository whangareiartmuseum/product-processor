# Product Processor for Whangārei Art Museum

A powerful web-based tool for managing Shopify product colors and recommendations for Whangārei Art Museum. Built with Next.js and Python.

## 🚀 Deployment Status

This application uses **Vercel's Python Serverless Functions** (Beta) for processing tasks.

### Features

- **Python Support**: Uses Vercel's Python 3.12 runtime (Beta)
- **Hybrid Architecture**: Next.js frontend with Python backend processing
- **Automatic Deployments**: Push to GitHub to deploy automatically

### Current Deployment

Your app is deployed on Vercel with full Python support for serverless functions.

## Features

### 🎨 Color Processing
- **Extract All Colors**: Process color extraction for all products in your store
- **Extract Missing Only**: Update only products missing color metadata
- **Extract Colors - Single Product**: Extract colors from a specific product by ID or handle
- **Contrast Reports**: Generate detailed color contrast analysis reports

### 🤖 AI-Powered Recommendations
- Generate intelligent product recommendations using OpenAI embeddings
- Automatically excludes out-of-stock products
- Creates meaningful connections between related products
- Uses friendly, accessible language for all recommendations

## 🎨 Features

### 1. Extract Colors - All Products
Processes every product in your store to extract and save color metadata.
- Extracts dominant color from product images
- Generates complementary colors
- Calculates text colors with proper contrast ratios
- **Real-time progress updates** showing:
  - Current product being processed
  - Progress percentage and time estimates
  - Success/failure counts
  - Detailed status messages

### 2. Extract Colors - Missing Only
Updates only products that are missing color metadata.
- Identifies products with incomplete color data
- Processes only what needs updating
- **Live progress tracking** with product counts

## Tech Stack

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: Python scripts for Shopify API integration
- **AI**: OpenAI GPT-4 for product recommendations
- **Deployment**: Optimized for Vercel

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd product-processor
```

2. Install dependencies:
```bash
npm run setup
```

This will install both Node.js and Python dependencies.

3. Configure environment variables:
```bash
cp .env.example .env.local
```

Then edit `.env.local` with your credentials:
- `SHOPIFY_SHOP_URL`: Your Shopify store URL
- `SHOPIFY_ACCESS_TOKEN`: Your Shopify access token
- `OPENAI_API_KEY`: Your OpenAI API key

## Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Deployment on Vercel

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)

2. Import your project to Vercel:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your Git repository

3. Configure environment variables in Vercel:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add the same variables from your `.env.local`

4. Deploy:
   - Vercel will automatically deploy your application
   - You'll get a production URL like `https://your-app.vercel.app`

## API Endpoints

All endpoints accept POST requests:

- `/api/colors/extract-all` - Extract colors for all products
- `/api/colors/extract-missing` - Extract colors for products missing metadata
- `/api/colors/extract-single` - Extract colors for a single product
- `/api/colors/contrast-report` - Generate contrast report
- `/api/recommendations/generate` - Generate product recommendations

## Project Structure

```
product-processor/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   └── page.tsx           # Main UI
├── components/            # React components
├── python_scripts/        # Python processing scripts
├── api_utils/            # API utilities
├── public/               # Static assets
└── requirements.txt      # Python dependencies
```

## Features in Detail

### Color Extraction
The color extraction algorithm:
- Analyzes product images to identify dominant and complementary colors
- Calculates optimal text colors for accessibility
- Stores colors as metafields in Shopify
- Handles transparency and various image formats

### Product Recommendations
The recommendation system:
- Uses OpenAI embeddings for semantic similarity
- Considers product descriptions, tags, and metadata
- Filters out out-of-stock products
- Generates friendly, accessible explanations
- Processes products in batches for efficiency

## Troubleshooting

### Python Dependencies
If you encounter issues with Python packages:
```bash
pip3 install -r requirements.txt --upgrade
```

### API Rate Limits
The application includes built-in delays to respect Shopify and OpenAI rate limits. If you encounter rate limit errors, the process will automatically retry.

### Memory Issues
For large product catalogs, consider:
- Processing in smaller batches
- Running processes during off-peak hours
- Monitoring server resources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues or questions, please open a GitHub issue or contact support.
