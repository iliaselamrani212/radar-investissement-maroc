@echo off
echo ============================================================
echo  INSTALLATION — Radar Investissement Maroc
echo ============================================================
echo.

echo [1/4] Installation des dependances Python...
pip install fastapi uvicorn[standard] sqlalchemy pydantic requests beautifulsoup4 lxml python-dotenv tenacity numpy sentence-transformers pdfplumber openpyxl pandas python-docx geopy psycopg

echo.
echo [2/4] Injection des donnees de demonstration...
python seed_data.py

echo.
echo [3/4] Installation des dependances frontend...
cd frontend
rmdir /s /q node_modules 2>nul
del package-lock.json 2>nul
npm install
cd ..

echo.
echo [4/4] Installation terminee !
echo.
echo ============================================================
echo  DEMARRAGE
echo ============================================================
echo.
echo Ouvre 2 terminaux :
echo.
echo Terminal 1 (Backend) :
echo   cd backend
echo   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo Terminal 2 (Frontend) :
echo   cd frontend
echo   npm run dev
echo.
echo Puis ouvre : http://localhost:3000
echo ============================================================
pause
