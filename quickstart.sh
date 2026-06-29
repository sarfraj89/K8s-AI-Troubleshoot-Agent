#!/bin/bash
# Quick start script for AI Kubernetes Agent

set -e

echo "🚀 AI Kubernetes Agent - Quick Start"
echo "===================================="
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found. You can still run the backend, but won't be able to investigate K8s"
fi

echo "✓ Prerequisites OK"
echo ""

# Setup backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python -m venv venv
fi

echo "  Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

echo "  Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "  ⚠️  Create backend/.env with OPENROUTER_API_KEY"
    echo "  Example:"
    echo "    OPENROUTER_API_KEY=sk_live_xxxxx"
    echo "    LLM_MODEL=openai/gpt-4"
fi

cd ..
echo "✓ Backend setup complete"
echo ""

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install -q
fi

if [ ! -f ".env" ]; then
    echo "  Creating .env file..."
    cp .env.example .env
    echo "  ⚠️  Update frontend/.env with InsForge credentials:"
    echo "    VITE_INSFORGE_URL=https://your-app.region.insforge.app"
    echo "    VITE_INSFORGE_ANON_KEY=your-anon-key-here"
fi

cd ..
echo "✓ Frontend setup complete"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "==========="
echo ""
echo "1. Update backend/.env:"
echo "   • Add OPENROUTER_API_KEY from InsForge or OpenRouter.ai"
echo ""
echo "2. Update frontend/.env:"
echo "   • Add VITE_INSFORGE_URL from InsForge project"
echo "   • Add VITE_INSFORGE_ANON_KEY from InsForge project"
echo ""
echo "3. Create InsForge database table 'investigations'"
echo "   • See INTEGRATION.md for SQL schema"
echo ""
echo "4. Start services:"
echo "   Terminal 1 - Backend:"
echo "     cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo ""
echo "   Terminal 2 - Frontend:"
echo "     cd frontend && npm run dev"
echo ""
echo "5. Open browser:"
echo "   http://localhost:3000"
echo ""
echo "📚 For detailed setup, see:"
echo "   • frontend/SETUP.md - Frontend configuration"
echo "   • INTEGRATION.md - Full system integration guide"
echo "   • README.md - Project overview"
