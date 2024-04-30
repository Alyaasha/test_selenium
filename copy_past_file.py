#СКРИПТ ДЛЯ ВСТАВКИ ТЕКСТА В ФАЙЛ
# вставить текст в файлы с расширениями .xml, .pdf, .docx, .txt, .ppt, .csv c разным кол-во слов 10**3, 10*9, 10*27, 10*81
from docx import Document

# Параметры скрипта
text_file_path = 'C:/Users/Алёнка/Documents/test/URL/URL.txt'
output_docx = 'C:/Users/Алёнка/Documents/test/URL/output_500.docx'
n = 1000 # количество раз вставки текста

# Открытие файла с текст
with open(text_file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Создание нового документа Word
doc = Document()

# Вставка текста n раз
for _ in range(n):
    doc.add_paragraph(text)

# Сохранение документа
doc.save(output_docx)

print(f"Документ '{output_docx}' успешно создан с вставленным текстом.")

