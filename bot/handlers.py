import csv
from datetime import datetime
from parser import parse_user_input
from categories import get_category, add_category_mapping

def process_message(text: str, username: str):
    amount, comment = parse_user_input(text)
    if not amount or not comment:
        return None, None, "Не удалось распознать сообщение. Введите сумму и комментарий, например: 200 кофе."

    category = get_category(comment)
    if category:
        # Сохраняем в CSV
        with open('data/expenses.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), amount, category, comment, username])
        return amount, category, None
    else:
        return amount, None, comment  # нужно будет уточнить у пользователя