#!/bin/bash

echo "Verificando portas em uso..."

# Verificar portas comuns
echo "Portas 5432, 5433 (PostgreSQL):"
lsof -i :5432 2>/dev/null || echo "5432: livre"
lsof -i :5433 2>/dev/null || echo "5433: livre"

echo "Portas 8000, 8001, 8002 (API):"
lsof -i :8000 2>/dev/null || echo "8000: livre"
lsof -i :8001 2>/dev/null || echo "8001: livre"
lsof -i :8002 2>/dev/null || echo "8002: livre"

echo "Portas 3000, 3001, 3002 (Frontend):"
lsof -i :3000 2>/dev/null || echo "3000: livre"
lsof -i :3001 2>/dev/null || echo "3001: livre"
lsof -i :3002 2>/dev/null || echo "3002: livre"

echo ""
echo "Portas configuradas atualmente:"
echo "PostgreSQL: 5433"
echo "API: 8002"  
echo "Frontend: 3002"

echo ""
echo "Se ainda houver conflitos, você pode modificar docker-compose.yml:"