import sys
import os
from datetime import datetime, timedelta

# 1. Ajuste de Path (igual aos outros scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal
from src.models import NewsHistory

def prune_old_records(days_to_keep=60):
    """
    Remove do banco de dados qualquer histórico de notícia
    mais antigo que 'days_to_keep' dias.
    """
    print(f"🧹 Iniciando faxina... (Mantendo apenas últimos {days_to_keep} dias)")
    
    db = SessionLocal()
    
    # Calcula a data de corte (Hoje - 60 dias)
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    try:
        # Filtra e deleta
        # processed_at é o campo DateTime que definimos no models.py
        deleted_count = db.query(NewsHistory).filter(
            NewsHistory.processed_at < cutoff_date
        ).delete()
        
        db.commit()
        print(f"✅ Faxina concluída! {deleted_count} registros antigos foram apagados.")
        
    except Exception as e:
        print(f"❌ Erro ao limpar histórico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Você pode alterar o número de dias aqui ou passar via argumento
    prune_old_records(days_to_keep=60)