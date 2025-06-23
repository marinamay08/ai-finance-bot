import csv
import logging
from .spreadsheet import save_to_google_sheets
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple, Optional
from .parser import parse_message
from .categories import add_category_mapping

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessResult(NamedTuple):
    """Результат обработки сообщения."""
    amount: Optional[Decimal]
    category: Optional[str]
    error_message: Optional[str]

def ensure_data_directory() -> Path:
    """
    Создает директорию data и файл expenses.csv если они не существуют.
    
    Returns:
        Path: Путь к файлу expenses.csv
        
    Raises:
        OSError: Если не удалось создать директорию или файл
    """
    try:
        data_dir = Path('data')
        if not data_dir.exists():
            data_dir.mkdir()
            logger.info(f"Created directory: {data_dir}")
            
        csv_path = data_dir / 'expenses.csv'
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['datetime', 'amount', 'category', 'comment', 'username'])
            logger.info(f"Created file: {csv_path}")
            
        return csv_path
    except OSError as e:
        logger.error(f"Failed to create data directory or file: {e}")
        raise

def save_expense(amount: Decimal, category: str, comment: str, username: str) -> None:
    """
    Сохраняет расход в CSV файл.
    
    Args:
        amount: Сумма расхода
        category: Категория расхода
        comment: Комментарий к расходу
        username: Имя пользователя
        
    Raises:
        ValueError: Если входные данные невалидны
        OSError: Если не удалось сохранить данные
    """
    # Валидация входных данных
    if not isinstance(amount, Decimal) or amount <= 0:
        raise ValueError("Amount must be a positive Decimal")
    if not category or not isinstance(category, str):
        raise ValueError("Category must be a non-empty string")
    if not comment or not isinstance(comment, str):
        raise ValueError("Comment must be a non-empty string")
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")
        
    try:
        csv_path = ensure_data_directory()
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), amount, category, comment, username])
        logger.info(f"Saved expense: {amount} {category} for {username}")

        # Пробуем дублировать в Google Таблицу
        try:
            save_to_google_sheets(amount, category, comment, username)
            logger.info(f"Also saved to Google Sheets: {amount} {category} for {username}")
        except Exception as e:
            logger.warning(f"Could not save to Google Sheets: {e}")
    except OSError as e:
        logger.error(f"Failed to save expense: {e}")
        raise

def process_message(text: str, username: str) -> ProcessResult:
    """
    Обрабатывает сообщение пользователя.
    
    Args:
        text: Текст сообщения
        username: Имя пользователя
        
    Returns:
        ProcessResult: Результат обработки сообщения, содержащий:
            - amount: Сумма расхода или None
            - category: Категория расхода или None
            - error_message: Сообщение об ошибке или None
    """
    try:
        # Валидация входных данных
        if not text or not isinstance(text, str):
            return ProcessResult(None, None, "Текст сообщения не может быть пустым")
        if not username or not isinstance(username, str):
            return ProcessResult(None, None, "Имя пользователя не может быть пустым")
            
        amount, comment, category = parse_message(text, username)
        if not amount or not comment:
            return ProcessResult(None, None, "Не удалось распознать сообщение. Введите сумму и комментарий, например: 200 кофе.")

        if category:
            # Если категория найдена, сохраняем расход
            save_expense(amount, category, comment, username)
            logger.info(f"Successfully processed expense: {amount} {category} for {username}")
            return ProcessResult(amount, category, None)
        else:
            # Если категория не найдена, возвращаем сумму и комментарий для выбора категории
            logger.info(f"Category not found for comment: {comment}, amount: {amount}")
            return ProcessResult(amount, None, comment)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return ProcessResult(None, None, f"Произошла ошибка при обработке сообщения: {str(e)}")