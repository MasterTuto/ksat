#!/usr/bin/env python3
"""
Script para configurar e rodar todos os serviços
"""

import os
import sys
import subprocess
import time

def run_all_services():
    """Rodar todos os serviços"""
    print("Iniciando todos os serviços...")
    
    # Parar cada serviço em seu próprio terminal
    services = [
        {
            "name": "PostgreSQL",
            "command": f"cd /var/www/dindin && python /var/www/dindin/calculation_service.py && python -m",
            "port": 5432
        },
        {
            "name": "Backend API",
            "command": f"cd /var/www/dindin && python -m",
            "port": 8000
        },
        {
            "name": "Frontend (text plano)",
            "command": f"cd /var/www/dindin && python -m",
            "port": 3001
        }
    ]
    
    print("Iniciando em {len(services)} serviços...")
    
    processes = []
    
    for service in services:
        print(f"Rodando {service['name']} em sua própria janela...")
        
        # Iniciar em thread separada
        process = subprocess.Popen(
            service["command"],
            shell=True,
            text=True
            cwd="/var/www/dindin"
            env=os.environ.get("PATH", "/var/www/dindin")
            env={
                'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://dindin:5432/dindin'
            }
        )
        processes.append(process)
    
    try:
        print("Aguardando {len(processes)} processos rodando...")
        
        # Esperar todos os processos terminarem
        for i, process in enumerate(processes):
            process.wait()
            if process.returncode != 0:
                print(f"Erro no serviço {service['name'] código {process.returncode}")
            
    except KeyboardInterrupt:
        print("\nInterrompido processos...")
        
        # Forçar todos os processos
        for process in processes:
            process.kill()
    
    except KeyboardInterrupt:
        print("\nSaindo processos...")
    
    except Exception as e:
        print(f"Erro ao rodar serviços: {e}")

if __name__ == "__main__":
    print("=== INICIANDO SISTEMA DE SERVIÇOS ===")
    run_all_services()