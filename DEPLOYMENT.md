# Deployment Guide

This guide provides step-by-step instructions for deploying the Fact-Checking Web App to various platforms.

## Streamlit Cloud (Recommended - Easiest)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your repository
   - Set main file path to `app.py`
   - Click "Advanced settings"
   - Add secrets:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `TAVILY_API_KEY`: Your Tavily API key
   - Click "Deploy"

3. **Your app will be live at**: `https://<your-app-name>.streamlit.app`

## Render

### Steps

1. **Create a new Web Service**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the service**
   - Name: `fact-checking-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

3. **Add Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TAVILY_API_KEY`: Your Tavily API key

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

## Vercel

### Steps

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Create vercel.json**
   ```json
   {
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```

3. **Deploy**
   ```bash
   vercel
   ```

4. **Add Environment Variables**
   - In Vercel dashboard, go to Settings → Environment Variables
   - Add `OPENAI_API_KEY` and `TAVILY_API_KEY`

## Heroku

### Steps

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **Create Procfile**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Create runtime.txt**
   ```
   python-3.11.0
   ```

4. **Deploy**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set TAVILY_API_KEY=your_key
   git push heroku main
   ```

## Important Notes

- **API Keys**: Never commit API keys to GitHub. Always use environment variables or secrets management.
- **Free Tier Limits**: Be aware of API rate limits and costs for OpenAI and Tavily on free tiers.
- **Testing**: Test your deployment with a sample PDF before sharing the URL.
- **Monitoring**: Monitor API usage to avoid unexpected charges.

## Troubleshooting

### Common Issues

1. **App not loading**
   - Check that environment variables are set correctly
   - Verify the main file path is correct (`app.py`)
   - Check build logs for errors

2. **API errors**
   - Verify API keys are correct
   - Check API quota/limits
   - Ensure API keys have proper permissions

3. **PDF upload issues**
   - Check file size limits (usually 200MB max)
   - Verify PDF is not corrupted
   - Ensure PDF contains extractable text (not just images)

