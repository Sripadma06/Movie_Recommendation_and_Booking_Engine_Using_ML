#!/bin/bash

# Movie Booking System - Quick Setup Script
# Run this to set up everything automatically

echo "🎬 CineMatch - Automated Setup Script"
echo "======================================"

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Found $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install streamlit==1.31.0
pip install pandas==2.1.4
pip install numpy==1.26.3
pip install scikit-learn==1.4.0
pip install requests==2.31.0
pip install python-dotenv==1.0.0

echo "✅ All dependencies installed!"

# Create .env file
echo ""
echo "🔑 Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOF
# TMDB API Configuration
TMDB_API_KEY=your_tmdb_api_key_here

# Email Configuration (Optional)
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here
EOF
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your TMDB API key!"
else
    echo "⚠️  .env file already exists, skipping..."
fi

# Create .gitignore
echo ""
echo "📝 Creating .gitignore..."
cat > .gitignore << EOF
venv/
__pycache__/
*.pyc
.env
bookings.db
.DS_Store
*.sqlite
*.log
EOF

echo "✅ Created .gitignore"

# Create README
echo ""
echo "📄 Creating README..."
cat > README.md << EOF
# 🎬 CineMatch - Movie Recommendation & Booking System

AI-powered movie discovery and booking platform built with Python, Streamlit, and Machine Learning.

## Features

- 🎯 **Smart Recommendations**: Content-based filtering using TF-IDF and cosine similarity
- 🎟️ **Easy Booking**: Select theaters, showtimes, and seats
- 📧 **Email Confirmations**: Automatic booking confirmations via email
- 🗄️ **Booking History**: Track all your past bookings
- 🎨 **Beautiful UI**: Modern, responsive Streamlit interface
- 🔄 **Real-time Data**: Integration with TMDB API for movie information

## Quick Start

\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Add your TMDB API key to .env file
echo "TMDB_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
\`\`\`

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python, SQLite
- **ML**: Scikit-learn (TF-IDF, Cosine Similarity)
- **APIs**: TMDB, Gmail SMTP
- **Deployment**: Streamlit Cloud / Render

## Project Structure

\`\`\`
movie-booking-system/
├── app.py              # Main Streamlit application
├── email_sender.py     # Email utility functions
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── bookings.db        # SQLite database (auto-created)
\`\`\`

## Setup Guide

### 1. Get TMDB API Key
1. Sign up at https://www.themoviedb.org/
2. Go to Settings → API
3. Request API Key (Developer option)
4. Add to .env file

### 2. Configure Email (Optional)
1. Enable Gmail App Password
2. Add credentials to .env

### 3. Run Locally
\`\`\`bash
streamlit run app.py
\`\`\`

## Deployment

### Streamlit Cloud (Free)
1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect repository
4. Add secrets (TMDB_API_KEY)
5. Deploy!

### Render (Alternative)
1. Connect GitHub
2. Set build command: \`pip install -r requirements.txt\`
3. Set start command: \`streamlit run app.py --server.port=\$PORT\`
4. Add environment variables
5. Deploy!

## Features Explained

### Recommendation Engine
Uses content-based filtering:
- Analyzes movie genres and descriptions
- Converts to TF-IDF vectors
- Calculates cosine similarity
- Returns top-N similar movies

### Booking System
- Select movie, theater, showtime
- Interactive seat selection
- SQLite database for persistence
- Email confirmations

## Extending the Project

### Add More Features
- User authentication
- Payment gateway integration
- Movie trailers
- Rating & reviews
- QR code tickets
- Admin dashboard

### Improve ML Model
- Collaborative filtering
- Hybrid recommendations
- Deep learning models
- Real-time personalization

## License

MIT License - feel free to use for your projects!

## Contributing

Pull requests welcome! For major changes, please open an issue first.

## Author

Built as a learning project for full-stack ML applications.
EOF

echo "✅ Created README.md"

# Test imports
echo ""
echo "🧪 Testing Python imports..."
python3 << EOF
try:
    import streamlit
    import pandas
    import numpy
    import sklearn
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

# Final instructions
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit .env file and add your TMDB API key"
echo "   Get it from: https://www.themoviedb.org/settings/api"
echo ""
echo "2. Run the app:"
echo "   streamlit run app.py"
echo ""
echo "3. Open browser at: http://localhost:8501"
echo ""
echo "📚 Need help? Check README.md for full documentation"
echo ""
echo "🚀 Happy coding!"