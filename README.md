# 🎨 Canva-Etsy Automation System

Automate your Canva template listing to Etsy with AI-powered market research, bestseller analysis, and SEO optimization.

## ✨ Features

- **📊 Market Research**: Automatically discover profitable niches and analyze Etsy trends
- **🔥 Bestseller Analysis**: Analyze top-selling templates to extract design insights (colors, layouts, keywords)
- **🎨 Template Management**: Manage Canva template links and metadata
- **📄 PDF Generation**: Automatically generate delivery PDFs with template links and usage instructions
- **🤖 AI-Powered SEO**: Generate optimized titles, descriptions, and tags using local LLM (Ollama) or OpenAI
- **🚀 Auto Upload**: Automatically create Etsy listings with proper formatting and SEO

## 💰 Cost

**MVP**: $13/month (Canva Pro only)
- Ollama (Local LLM): Free
- eRank Free Plan: Free
- Local Development: Free

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Etsy Seller Account
- Etsy Developer API Keys
- Canva Pro Account (for Template Links)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd canva-etsy-automation
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your API keys
   ```

3. **Install Ollama (Local LLM)**:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull Llama 3 model
   ollama pull llama3:8b
   ```

4. **Start the application**:
   ```bash
   docker-compose up -d
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## 📋 Getting Started Guide

See the full guide in the [plan document](/root/.claude/plans/rustling-knitting-garden.md) for:
- Step-by-step Etsy seller account setup
- Etsy Developer API key generation
- First template design tutorial
- System testing guide

## 🏗️ Project Structure

```
canva-etsy-automation/
├── backend/               # FastAPI backend
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── database.py       # SQLAlchemy models
│   ├── models/           # Database models
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   └── templates/        # PDF templates
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── components/   # Reusable components
│   │   └── lib/          # Utilities
│   └── package.json
├── docker-compose.yml    # Docker orchestration
└── .env.example          # Environment template
```

## 🔧 Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📚 API Documentation

Access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗺️ Implementation Roadmap

- [x] **Phase 1**: Project setup (Week 1)
- [ ] **Phase 2**: Market research & bestseller analysis (Week 2-3)
- [ ] **Phase 3**: Template management & PDF generation (Week 4-5)
- [ ] **Phase 4**: SEO optimization & Etsy upload (Week 6-7)
- [ ] **Phase 5**: Integration & workflow automation (Week 8)

## 🎯 Success Metrics

- Market research: 10 niches in 30 minutes
- Template registration: 2 minutes per template
- PDF generation: 30 seconds per template
- SEO generation: 1 minute per template
- Etsy upload: 2 minutes per template
- **Total: 5 minutes per template** (from registration to upload)

## 🛠️ Tech Stack

**Backend**:
- Python 3.11+
- FastAPI
- SQLAlchemy
- Ollama + Llama 3 (Local LLM)
- Pillow + OpenCV (Image analysis)
- ReportLab (PDF generation)

**Frontend**:
- React 18
- Vite
- TailwindCSS
- Zustand (State management)
- Recharts (Data visualization)

**Infrastructure**:
- Docker & Docker Compose
- SQLite (MVP) / PostgreSQL (Production)
- Redis + Celery (Task queue, Phase 5)

## 📖 Documentation

- [Full Implementation Plan](/root/.claude/plans/rustling-knitting-garden.md)
- [API Documentation](http://localhost:8000/docs)
- [Etsy API Docs](https://developers.etsy.com/)
- [Canva Template Links](https://www.canva.com/help/share-template-link/)

## ⚠️ Important Notes

1. **Copyright**: Only sell original designs
2. **Trademarks**: Don't use famous brand names/logos
3. **Etsy Policy**: Review [Etsy seller policies](https://www.etsy.com/legal/sellers/)
4. **Canva License**: Verify Template Link selling is allowed (currently OK)
5. **Taxes**: Report income according to your local laws

## 🤝 Contributing

This is a personal automation project. Feel free to fork and customize for your own use.

## 📄 License

Private project - All rights reserved

## 🆘 Troubleshooting

### Etsy API Connection Failed
- Check API Key/Secret in .env
- Verify Callback URL matches (http://localhost:3000/auth/callback)
- Ensure correct scopes: listings_w, listings_r, shops_r

### Ollama Slow/Errors
- GPU recommended but works on CPU
- Consider OpenAI API as alternative (~$5/month)

### PDF Generation Failed
- Check image file size (<10MB)
- View logs: `docker-compose logs backend`

### Template Link Not Found
- Verify Canva Pro subscription
- Check Share → More → Template Link menu exists

## 📞 Support

For issues with:
- Etsy API: https://www.etsy.com/developers
- Canva: https://www.canva.com/help
- Ollama: https://ollama.com

---

Built with ❤️ by a 10-year veteran designer looking to automate Etsy passive income
