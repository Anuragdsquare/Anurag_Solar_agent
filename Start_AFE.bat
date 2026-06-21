@echo off
title Anurag Forecast Engine Initialization
echo ===================================================
echo Anurag Forecast Engine - Local Environment Setup
echo ===================================================
echo Installing necessary AI and Web components...
pip install streamlit pandas numpy scikit-learn requests plotly openpyxl
echo.
echo Launching the Dashboard...
streamlit run app.py
pause
