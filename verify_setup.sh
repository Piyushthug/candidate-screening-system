#!/bin/bash
# Verification script for Candidate Screening System

echo "=========================================="
echo "Candidate Screening System - Setup Check"
echo "=========================================="
echo ""

# Check Python
echo "1. Python Version:"
python --version
echo ""

# Check venv
echo "2. Virtual Environment:"
if [ -d ".venv" ]; then
    echo "   ✓ .venv directory exists"
else
    echo "   ✗ .venv directory NOT found"
    exit 1
fi
echo ""

# Check key packages
echo "3. Key Dependencies:"
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

packages=("fastapi" "sqlalchemy" "pydantic" "pytest" "google-generativeai" "langchain-google-genai")
for package in "${packages[@]}"; do
    if python -c "import ${package//-/_}" 2>/dev/null; then
        echo "   ✓ $package"
    else
        echo "   ✗ $package NOT installed"
    fi
done
echo ""

# Check .env file
echo "4. Configuration:"
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    if grep -q "GOOGLE_API_KEY" .env; then
        echo "   ✓ GOOGLE_API_KEY configured"
    else
        echo "   ✗ GOOGLE_API_KEY not found in .env"
    fi
else
    echo "   ✗ .env file NOT found"
    exit 1
fi
echo ""

# Check project structure
echo "5. Project Structure:"
directories=("backend" "tests" "eval" ".github/workflows")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir/"
    else
        echo "   ✗ $dir/ NOT found"
    fi
done
echo ""

# Check git
echo "6. Git Repository:"
if [ -d ".git" ]; then
    echo "   ✓ Git repository initialized"
    commit_count=$(git rev-list --count HEAD)
    echo "   ✓ Commits: $commit_count"
else
    echo "   ✗ Git repository NOT initialized"
fi
echo ""

# Run unit tests
echo "7. Running Unit Tests:"
pytest tests/test_tools.py -q --tb=no
test_result=$?

if [ $test_result -eq 0 ]; then
    echo "   ✓ Unit tests PASSED"
else
    echo "   ✗ Unit tests FAILED (exit code: $test_result)"
fi
echo ""

echo "=========================================="
echo "Setup Verification Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Add your Gemini API key to .env"
echo "2. Run: python -m uvicorn backend.main:app --reload"
echo "3. Visit: http://127.0.0.1:8000/docs"
echo ""
