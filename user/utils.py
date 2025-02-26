import pdfplumber
import re
from .models import Question, Choice

def import_pdf_to_models(file_path, language='uz'):
    print(f"Запуск функции import_pdf_to_models с file_path: {file_path}, language: {language}")

    # Открытие и чтение PDF
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text(layout=True) or ""
                print(f"Страница {page_num}: {page_text[:200]}...")
                text += page_text + "\n"
            print(f"Полный текст из PDF:\n{text[:500]}...")
    except Exception as e:
        print(f"Ошибка при чтении PDF: {e}")
        return

    lines = text.split('\n')
    current_question = None
    options = {'a': '', 'b': '', 'c': '', 'd': ''}  # Храним текст вариантов A, B, C, D (или А, В, С, Д)
    correct_option = 'a'  # По умолчанию считаем, что правильный ответ — A
    in_question = False
    in_choices = False

    # Маппинг букв (латинских и кириллических) на ключи словаря options
    letter_mapping = {
        'A': 'a', 'А': 'a',
        'B': 'b', 'В': 'b',
        'C': 'c', 'С': 'c',
        'D': 'd', 'Д': 'd',
    }

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            print(f"Пропущена пустая строка {i}")
            continue

        # Нормализация текста (учитываем ошибки OCR)
        line = re.sub(r'[^\w\sА-Яа-яЁё0-9(),.\-*]', '', line)  # Удаляем странные символы
        line = line.replace('божхона', 'божхона').replace('божжона', 'божхона')
        line = line.replace('иахс', 'шахс').replace('кйрсатиш', 'кўрсатиш')
        line = line.replace('мальлумот', 'малумот').replace('та', ' та')
        line = line.replace('хукукуни', 'ҳуқуқни').replace('хамкорлик', 'ҳамкорлик')
        line = line.replace('хорижий', 'хорижий').replace('худудидан', 'ҳудудидан')
        line = line.replace('тулдирилилиди', 'тулдирилмайди').replace('test', '')
        line = line.replace('k', 'Б').replace('c', 'С')
        line = ' '.join(line.split())  # Нормализуем пробелы

        # Начало нового вопроса
        question_match = re.match(r'^\d+\)\s*', line)
        if question_match:
            if current_question and any(v.strip() for v in options.values()):  # Сохраняем только если есть непустые варианты
                print(f"Сохранение вопроса: {current_question}")
                save_question(current_question, options, correct_option, language)
            question_text = line[question_match.end():].strip() + " турган хавобни топинг?"
            options = {'a': '', 'b': '', 'c': '', 'd': ''}
            correct_option = 'a'
            current_question = question_text
            in_question = True
            in_choices = False
            print(f"Обнаружен вопрос в строке {i}: {line}")
            print(f"Новый вопрос: {question_text}"[:100])
            continue

        # Обработка вариантов ответа (более гибкое регулярное выражение)
        choice_match = re.match(r'^\s*(\*?)\s*([A-DА-Д])\s*\)\s*(.*)', line, re.IGNORECASE)
        if choice_match and current_question:
            asterisk = choice_match.group(1)
            option_letter = choice_match.group(2).upper()
            is_correct = bool(asterisk)
            option_text = choice_match.group(3).strip()

            # Если текст варианта пустой, ищем его в следующих строках
            if not option_text:
                next_line_index = i
                while next_line_index < len(lines) - 1:
                    next_line_index += 1
                    next_line = lines[next_line_index].strip()
                    if next_line:
                        if not re.match(r'^\s*(\*?)\s*([A-DА-Д])\s*\)\s*', next_line, re.IGNORECASE):
                            option_text = next_line
                            break
                        else:
                            break  # Если следующая строка — новый вариант, прерываем

            if not option_text:
                print(f"Пустой текст варианта в строке {i}, пропущен: {line}")
                continue

            mapped_letter = letter_mapping.get(option_letter)
            if mapped_letter:
                options[mapped_letter] = option_text
                if is_correct:
                    correct_option = mapped_letter
                print(f"Вариант {option_letter}: {option_text} (Правильный: {is_correct})")
                print(f"Добавлено в options[{mapped_letter}] = {option_text}")
            else:
                print(f"Неизвестная буква в строке {i}: {line}")
            in_choices = True
            continue

        # Добавление текста к вопросу или последнему варианту
        if current_question and not question_match:
            if in_question and not any(options.values()):
                current_question += " " + line
                print(f"Добавление текста к вопросу в строке {i}: {line}")
            elif in_choices and any(options.values()):
                last_option = max((k for k, v in options.items() if v), key=lambda x: ord(x))
                options[last_option] += " " + line
                print(f"Добавление текста к варианту {last_option} в строке {i}: {line}")
            else:
                print(f"Не распознанная строка {i}: {line}")

    # Сохранение последнего вопроса
    if current_question and any(v.strip() for v in options.values()):
        print(f"Сохранение последнего вопроса: {current_question}")
        save_question(current_question, options, correct_option, language)

    print(f"Обработка завершена. Импортировано вопросов: {Question.objects.count()}")

def save_question(question_text, options, correct_option, language):
    question = Question.objects.create(
        text=question_text,
        language=language
    )
    print(f"Создан вопрос: {question_text}"[:100])
    Choice.objects.create(
        question=question,
        a=options['a'],
        b=options['b'],
        c=options['c'],
        d=options['d'],
        is_correct=correct_option
    )
    print(f"Создан набор вариантов для вопроса {question.id}: A={options['a']}, B={options['b']}, C={options['c']}, D={options['d']}, Correct={correct_option}")