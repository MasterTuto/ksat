#!/usr/bin/env python3
"""
Jobs dumb para atualizar valores dos data points com base na latência
Cada job atualiza valores de forma proporcional ao tempo de latência
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.database import DataPoint
import time
import random
from datetime import datetime


def update_data_points_by_latency():
    """
    Atualiza valores de data points com base na latência
    Quanto maior a latência, mais o valor aumenta com o tempo
    """
    db = SessionLocal()

    try:
        while True:
            # Buscar todos os data points
            data_points = db.query(DataPoint).all()

            if not data_points:
                print("Nenhum data point encontrado. Aguardando...")
                time.sleep(10)
                continue

            print(f"Atualizando {len(data_points)} data points...")

            # Atualizar cada data point
            for dp in data_points:
                if dp.latency and dp.latency > 0:
                    # Calcular fator de atualização baseado na latência
                    # Latência em segundos, converter para minutos
                    time_factor = dp.latency / 60.0
                    update_amount = (time_factor * 0.001) + random.uniform(
                        -0.0005, 0.0005
                    )

                    # Atualizar valor
                    old_value = float(dp.value)
                    new_value = old_value + update_amount

                    dp.value = new_value
                    dp.updated_at = datetime.utcnow()

                    print(
                        f"  DataPoint {dp.id}: {old_value:.8f} -> {new_value:.8f} (latency: {dp.latency}s)"
                    )

            # Commit das alterações
            db.commit()
            print(f"Atualização concluída em {datetime.utcnow()}")
            print("Próxima atualização em 60 segundos...")

            time.sleep(60)  # Esperar 1 minuto antes da próxima atualização

    except KeyboardInterrupt:
        print("\nJob interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no job: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Iniciando job de atualização de data points por latência...")
    print("Pressione Ctrl+C para interromper")
    update_data_points_by_latency()
