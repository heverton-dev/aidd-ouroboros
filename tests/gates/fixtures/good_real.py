import logging
import os

logger = logging.getLogger(__name__)

def process_file_data(file_path: str) -> int:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")
    
    total = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            total += len(line.strip())
            
    logger.info("Total de caracteres: %d", total)
    return total
