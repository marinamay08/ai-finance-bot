import json
import logging
from pathlib import Path
from typing import Dict, Optional
from config.categories_map import CATEGORY_MAP

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

# Константы
DICT_PATH = Path("config") / "category_dict.json"
MAX_LEMMA_LENGTH = 50
MAX_CATEGORY_LENGTH = 30
VALID_CATEGORIES = set(CATEGORY_MAP.values())

# Теперь custom_category_map: Dict[str, Dict[str, str]]
custom_category_map: Dict[str, Dict[str, str]] = {}

def ensure_config_directory() -> None:
    """Создает директорию config, если она не существует."""
    try:
        DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Директория {DICT_PATH.parent} создана или уже существует")
    except Exception as e:
        logger.error(f"Ошибка при создании директории {DICT_PATH.parent}: {e}")
        raise

def load_custom_keywords() -> None:
    """Загружает пользовательские соответствия категорий из файла."""
    global custom_category_map
    try:
        if DICT_PATH.exists():
            with open(DICT_PATH, "r", encoding="utf-8") as f:
                custom_category_map = json.load(f)
            logger.info(f"Загружено пользовательских профилей: {len(custom_category_map)}")
        else:
            logger.info("Файл с пользовательскими соответствиями не найден")
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении JSON файла: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке пользовательских соответствий: {e}")
        raise

def save_custom_keywords(lemma: str, category: str, username: str, overwrite: bool = False) -> None:
    """Сохраняет новое соответствие в пользовательский словарь.
    
    Args:
        lemma: Ключевое слово для категории
        category: Название категории
        username: Имя пользователя
        overwrite: Если True, перезаписывает существующее соответствие
    """
    if not isinstance(lemma, str) or not isinstance(category, str) or not isinstance(username, str):
        raise ValueError("lemma, category и username должны быть строками")
    
    if len(lemma) > MAX_LEMMA_LENGTH:
        raise ValueError(f"lemma слишком длинный (максимум {MAX_LEMMA_LENGTH} символов)")
    
    if len(category) > MAX_CATEGORY_LENGTH:
        raise ValueError(f"category слишком длинный (максимум {MAX_CATEGORY_LENGTH} символов)")
    
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Неизвестная категория: {category}")

    ensure_config_directory()
    if username not in custom_category_map:
        custom_category_map[username] = {}
    if lemma in custom_category_map[username] and not overwrite:
        logger.info(f"Соответствие для '{lemma}' у пользователя '{username}' уже существует")
        return
    custom_category_map[username][lemma] = category
    try:
        with open(DICT_PATH, "w", encoding="utf-8") as f:
            json.dump(custom_category_map, f, ensure_ascii=False, indent=2)
        logger.info(f"Добавлено новое соответствие: '{lemma}' -> '{category}' для пользователя '{username}'")
    except Exception as e:
        logger.error(f"Ошибка при сохранении соответствия: {e}")
        raise

def get_combined_category_map(username: str) -> Dict[str, str]:
    """Возвращает объединенный словарь категорий."""
    try:
        all_map = CATEGORY_MAP.copy()
        user_map = custom_category_map.get(username, {})
        all_map.update(user_map)
        
        if not user_map:
            logger.warning(f"Пользовательский словарь категорий пуст для пользователя {username}")
            
        return all_map
    except Exception as e:
        logger.error(f"Ошибка при объединении словарей категорий: {e}")
        raise

def add_category_mapping(comment: str, category: str, username: str, overwrite: bool = False) -> None:
    """Добавляет новое соответствие комментария и категории в пользовательский словарь.
    
    Args:
        comment: Комментарий к расходу
        category: Название категории
        username: Имя пользователя
        overwrite: Если True, перезаписывает существующее соответствие
    """
    try:
        save_custom_keywords(comment, category, username, overwrite)
    except Exception as e:
        logger.error(f"Ошибка при добавлении соответствия категории: {e}")
        raise

# Загружаем пользовательский словарь при запуске
load_custom_keywords()