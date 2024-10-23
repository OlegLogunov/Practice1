import os
import sqlite3
import csv


class PriceAnalyzer:
    def __init__(self, db_name='prices.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price REAL,
                    weight REAL,
                    file TEXT
                )
            ''')

    def load_prices(self, folder):
        for filename in os.listdir(folder):
            if 'price' in filename and filename.endswith('.csv'):
                file_path = os.path.join(folder, filename)

                print(file_path)

                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    headers = next(reader)

                    name_col = next((i for i, h in enumerate(headers) if
                                     h.lower() in ['название', 'продукт', 'товар', 'наименование']), None)
                    price_col = next((i for i, h in enumerate(headers) if h.lower() in ['цена', 'розница']), None)
                    weight_col = next((i for i, h in enumerate(headers) if h.lower() in ['фасовка', 'масса', 'вес']),
                                      None)

                    if name_col is not None and price_col is not None and weight_col is not None:
                        for row in reader:
                            name = row[name_col]
                            price = float(row[price_col])
                            weight = float(row[weight_col])
                            with self.conn:
                                self.conn.execute(
                                    'INSERT INTO products (name, price, weight, file) VALUES (?, ?, ?, ?)',
                                    (name, price, weight, filename))

    def find_text(self, search_text):
        cursor = self.conn.cursor()
        search_text_lower = search_text.lower()  # Приводим введенный текст к нижнему регистру
        cursor.execute('''
            SELECT id, name, price, weight, file FROM products WHERE LOWER(name) LIKE LOWER(?) ORDER BY price / weight
        ''', ('%' + search_text_lower + '%',))
        return cursor.fetchall()

    def export_to_html(self, output_file='prices.html'):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY price / weight')
        rows = cursor.fetchall()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<html><head><meta charset="UTF-8"><title>Анализ прайс-листов</title></head><body>')
            f.write('<h1>Анализ прайс-листов</h1>')
            f.write('<tr><th>№</th><th>Наименование</th><th>Цена</th><th>Вес</th><th>Файл</th><th>Цена за кг</th></tr>')
            for row in rows:
                f.write(
                    f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[2] / row[3]:.2f}</td></tr>')
            f.write('</table></body></html>')

    def close(self):
        self.conn.close()


def main():
    analyzer = PriceAnalyzer()
    folder_path = input("Введите путь к папке с прайс-листами: ")
    analyzer.load_prices(folder_path)

    while True:
        search_text = input("Введите текст для поиска (или 'exit' для выхода): ")
        if search_text.lower() == 'exit':
            print("Работа завершена.")
            break

        results = analyzer.find_text(search_text)


        if results:
            print(f"{'№':<5} {'Наименование':<30} {'Цена':<10} {'Вес':<10} {'Файл':<20} {'Цена за кг':<10}")

            index = 1  # Начинаем с 1, чтобы номера начинались с 1
            for id_, name, price, weight, file in results:
                price_per_kg = price / weight if weight > 0 else 0  # Проверка на деление на ноль

                print(f"{index:<5} {name:<30} {price:<10} {weight:<10} {file:<20} {price_per_kg:.2f}")
                index += 1  # Увеличиваем индекс для следующей строки
        else:
            print("Товары не найдены.")

    analyzer.export_to_html()
    analyzer.close()

if __name__ == '__main__':
    main()
