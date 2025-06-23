import re
from decimal import Decimal
from pymorphy3 import MorphAnalyzer
from typing import Tuple, Optional
from .categories import get_combined_category_map

morph = MorphAnalyzer()

def parse_message(text: str, username: str) -> Tuple[Optional[Decimal], Optional[str], Optional[str]]:
    """
    Парсит сообщение и возвращает сумму, комментарий и категорию.
    
    Args:
        text: Текст сообщения в формате "сумма комментарий"
        username: Имя пользователя
        Примеры:
        - "200 кофе"
        - "200.50 кофе"
        - "200,50 кофе"
        - "200кофе" (без пробела)
        
    Returns:
        Tuple[Optional[Decimal], Optional[str], Optional[str]]: (сумма, комментарий, категория)
        Если формат не распознан, возвращает (None, None, None)
    """
    # Удаляем лишние пробелы и приводим к нижнему регистру
    text = ' '.join(text.strip().lower().split())
    
    # Поддерживаем разные форматы чисел: целые и десятичные (через точку или запятую)
    # Также поддерживаем формат без пробела между суммой и комментарием
    match = re.match(r"(\d+(?:[.,]\d+)?)[\s]*(.+)", text)
    if not match:
        return None, None, None
        
    try:
        # Заменяем запятую на точку для корректного парсинга десятичного числа
        amount_str = match.group(1).replace(',', '.')
        amount = Decimal(amount_str)
        
        # Проверяем, что сумма положительная
        if amount <= 0:
            return None, None, None
            
        comment = match.group(2).strip()
        
        # Проверяем длину комментария
        if len(comment) > 100:  # Максимальная длина комментария
            return None, None, None
            
        category = match_category(comment, username)
        return amount, comment, category
        
    except (ValueError, TypeError, ArithmeticError):
        return None, None, None

def match_category(comment: str, username: str) -> Optional[str]:
    """
    Находит категорию для комментария.
    Сначала ищет полное совпадение, затем каждое слово в нормальной форме.
    
    Args:
        comment: Комментарий к расходу
        username: Имя пользователя
        
    Returns:
        Optional[str]: Найденная категория или None
    """
    category_map = get_combined_category_map(username)
    
    # Проверяем полное совпадение комментария
    if comment in category_map:
        return category_map[comment]
    
    # Проверяем каждое слово в нормальной форме
    words = comment.split()
    for word in words:
        try:
            lemma = morph.parse(word)[0].normal_form
            if lemma in category_map:
                return category_map[lemma]
        except (IndexError, AttributeError):
            # Пропускаем слова, которые не удалось проанализировать
            continue
    
    return None