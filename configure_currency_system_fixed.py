import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import (
    User,
    Market,
    MetricValue,
    MarketValue,
    GlobalCurrencyValue,
    DataPoint,
)
from app.services.calculation_service import CalculationService
from uuid import uuid4
import random
from datetime import datetime


def update_user_balances():
    """Atualiza saldos dos usuários quando a população muda"""
    db = SessionLocal()

    try:
        # Contar usuários atuais
        users = db.query(User).all()
        current_population = len(users)

        if current_population == 0:
            print("Nenhum usuário encontrado. Usando população padrão de 1_000")
            current_population = 1

        print(f"População atual: {current_population}")

        # Calcular nova distribuição (novamente 1_000 para cada usuário existente + 1_000)
        new_total_balance = current_population * 1000.0

        # Atualizar saldos
        for user in users:
            user.currency_balance = new_total_balance
            user.updated_at = datetime.utcnow()
            print(f"Usuário {user.username}: {user.currency_balance:.2f} unidades")

        db.commit()
        print(
            f"Distribuição atualizada: {len(users)} usuários, {new_total_balance:.2f} unidades totais"
        )

    except Exception as e:
        print(f"Erro ao atualizar saldos: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def calculate_global_values():
    """Calcula o valor global da moeda baseado nos mercados"""
    db = SessionLocal()

    try:
        # Buscar todos os valores dos mercados
        markets = db.query(Market).filter(Market.is_active == True).all()
        market_values = []

        for market in markets:
            market_val = (
                db.query(MarketValue).filter(MarketValue.market_id == market.id).first()
            )
            if market_val:
                market_values.append(market_val.value)

        if not market_values:
            print("Nenhum valor de mercado encontrado")
            return 0.0

        # Calcular valor global (média dos mercados)
        if market_values:
            global_value = sum(mv.value for mv in market_values) / len(market_values)

            # Criar registro do valor global
            global_currency_val = GlobalCurrencyValue(value=global_value)
            db.add(global_currency_val)
            db.commit()

            print(f"Valor global calculado: {global_value:.8f}")
            return global_value

        return 0.0

    except Exception as e:
        print(f"Erro ao calcular valor global: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        return 0.0
    finally:
        db.close()


def update_population_based_on_market_data():
    """
    Atualiza população com base nos dados dos mercados
    """
    db = SessionLocal()

    try:
        # Calcular população baseada nos dados
        markets = db.query(Market).filter(Market.is_active == True).all()
        total_population = 0

        for market in markets:
            # Contar data points confiáveis deste mercado
            data_points = (
                db.query(DataPoint)
                .join(Metric)
                .filter(Metric.market_id == market.id)
                .filter(DataPoint.is_reliable == True)
                .all()
            )

            if data_points:
                # Usar o primeiro data point como proxy da população
                estimated_people_per_market = (
                    int(1000.0 / float(data_points[0].value))
                    if data_points and float(data_points[0].value) > 0
                    else 1000
                )
                total_population += estimated_people_per_market

        print(f"População estimada com base nos dados: {total_population}")

        # Atualizar população dos usuários
        users = db.query(User).all()
        new_population = max(total_population, len(users))

        for user in users:
            user.currency_balance = new_population * 1000.0
            user.updated_at = datetime.utcnow()

        db.commit()
        print(f"População ajustada para {new_population} usuários")

    except Exception as e:
        print(f"Erro ao atualizar população: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def generate_marketcap_analysis():
    """Analisa o marketcap entre mercados"""
    db = SessionLocal()

    try:
        markets = db.query(Market).filter(Market.is_active == True).all()

        if len(markets) < 2:
            print("É necessário pelo menos 2 mercados para análise de marketcap")
            return

        print("=== ANÁLISE DE MARKETCAP ===")

        market_values = []
        total_values = []

        for market in markets:
            market_val = (
                db.query(MarketValue).filter(MarketValue.market_id == market.id).first()
            )
            if market_val:
                market_values.append(market_val.value)
                print(f"Mercado: {market.name} - Valor: {market_val.value:.8f}")

        if not market_values:
            return

        # Calcular marketcap
        total_value = sum(market_values)
        print(f"Total Market Cap: {total_value:.8f}")

        # Análise comparativa
        if len(markets) >= 2:
            avg_value = total_value / len(markets)
            print(f"Valor médio por mercado: {avg_value:.8f}")

            # Verificar se algum mercado se destaca
            max_market = max(market_values)
            min_market = min(market_values)
            max_value = float(max_market.value)

            print(
                f"Mercado com maior valor: {markets[market_values.index(max_market)]}"
            )
            print(
                f"Mercado com menor valor: {markets[market_values.index(min_market)]}"
            )
            print(f"Diferença: {(max_value - min_value):.8f}")

    except Exception as e:
        print(f"Erro na análise de marketcap: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def main():
    """Função principal"""
    print("=== CONFIGURANDO SISTEMA DE MOEDA E POPULAÇÃO DINÂMICA ===")

    # Configurar sistema de moeda
    update_user_balances()

    # Atualizar população com base nos dados dos mercados
    update_population_based_on_market_data()

    # Calcular valores atuais
    global_value = calculate_global_values()

    # Análise de marketcap
    generate_marketcap_analysis()

    print("\n=== SISTEMA CONFIGURADO ===")
    print(f"Valor global atual: {global_value:.8f}")
    print(f"População atual: {len(SessionLocal().query(User).all())}")
    print(
        f"Moeda em circulação: {SessionLocal().query(User).first().currency_balance:.2f}"
    )

    print("\nJobs dumb continuam atualizando valores...")
    print("Use: docker-compose exec api python run_dumb_jobs.py")
    print("Pressione Ctrl+C para parar")


if __name__ == "__main__":
    main()
