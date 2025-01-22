import streamlit as st                                          
import pickle                                                  
from barfi import save_schema, barfi_schemas, Block, st_barfi  
from barfi.manage_schema import delete_schema                   
from typing import Dict                                         
import os                                                       
import time                                                     
import ast                                                      
import io                                                      
import shutil                                                  
from datetime import datetime, timedelta                       


def load_schemas(main_file_name: str) -> Dict:
    try: 
        with open(main_file_name, 'rb') as handle_read:
            schemas = pickle.load(handle_read)  # Загружаем данные из файла с помощью pickle
    except FileNotFoundError:
        
        schemas = {}
    return schemas  

def create_backup(main_file_name: str):
    """Создает бэкап основного файла схем в папке backups"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Получаем текущую дату и время для имени файла
    backup_dir = "backups"  # Указываем папку для бэкапов
    os.makedirs(backup_dir, exist_ok=True)  # Создаем папку, если она не существует

    # Формируем имя файла бэкапа с временной меткой
    backup_file_name = os.path.join(backup_dir, f"backup_{timestamp}.barfi")  
    shutil.copy(main_file_name, backup_file_name)  # Копируем основной файл в папку бэкапов

def check_and_create_backup(main_file_name: str):
    """Проверяет, прошло ли 15 минут с последнего бэкапа, и создает новый бэкап при необходимости."""
    # Проверяем, есть ли в состоянии сессии время последнего бэкапа
    if 'last_backup_time' not in st.session_state:
        # Инициализируем время последнего бэкапа на 15 минут назад
        st.session_state.last_backup_time = datetime.now() - timedelta(minutes=15)  

    # Проверяем, прошло ли 15 минут с последнего бэкапа
    if datetime.now() - st.session_state.last_backup_time > timedelta(minutes=15):
        create_backup(main_file_name)  # Создаем новый бэкап
        st.session_state.last_backup_time = datetime.now()  # Обновляем время последнего бэкапа

def create_scheme(name, schema_data):
    """Создает новую схему с указанным именем и данными."""
    existing_schemes = barfi_schemas()  # Получаем существующие схемы
    try:
        schema_data = ast.literal_eval(schema_data)  # Преобразуем строку в словарь
        if not isinstance(schema_data, dict):
            schema_data = ""  # Если не словарь, обнуляем данные
        if name in existing_schemes:
            st.toast("Схема с указанным названием существует", icon='⚠️')  # Уведомляем, если схема уже существует
            time.sleep(1)  # Задержка перед возвратом
            return  # Выходим из функции, если схема уже существует
    except:
        schema_data = ""  # Если произошла ошибка, обнуляем данные

    save_schema(name, schema_data)  # Сохраняем схему
    st.toast(f"Схема '{name}' успешно создана!", icon="✅")  # Уведомление об успешном создании схемы

def delete_scheme(name):
    """Удаляет схему с указанным именем."""
    delete_schema(name)  # Удаляем схему
    st.toast(f"Схема '{name}' успешно удалена!", icon="✅")  # Уведомление об успешном удалении

def get_additional_files(directory):
    """Получает список дополнительных файлов в указанной директории."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.barfi')]  # Возвращаем список файлов с расширением .barfi

def load_additional_schemas(directory: str) -> Dict:
    """Загружает дополнительные схемы из указанной директории."""
    additional_schemas = {}  # Инициализируем пустой словарь для дополнительных схем
    for filename in get_additional_files(directory):  # Проходим по всем дополнительным файлам
        try:
            # Открываем каждый файл и загружаем схемы
            with open(filename, 'rb') as handle_read:
                schema = pickle.load(handle_read)  # Загружаем схемы из файла
                additional_schemas.update(schema)  # Обновляем словарь дополнительными схемами
        except Exception as e:
            st.error(f"Ошибка при загрузке файла {filename}: {e}")  # Уведомляем об ошибке, если не удалось загрузить файл
    return additional_schemas  # Возвращаем загруженные дополнительные схемы

def synchronize_schemas(main_file_name: str, additional_directory: str) -> None:
    """Синхронизирует схемы из основной и дополнительной директории."""
    main_schemas = load_schemas(main_file_name)  # Загружаем основные схемы
    additional_schemas = load_additional_schemas(additional_directory)  # Загружаем дополнительные схемы

    # Флаг для отслеживания изменений
    changes_made = False

    # Проходим по всем дополнительным схемам
    for name, additional_schema in additional_schemas.items():
        if name in main_schemas:
            # Если схема уже существует, проверяем, отличаются ли они
            if main_schemas[name] == additional_schema:
                continue  # Если они одинаковые, пропускаем
            else:
                # Если они отличаются, создаем новое имя для копии
                new_name = f"{name}_copy"
                while new_name in main_schemas:
                    new_name += "_copy"  # Увеличиваем имя, пока не найдем уникальное
                main_schemas[new_name] = additional_schema  # Сохраняем дополнительную схему как новую
                changes_made = True  # Устанавливаем флаг изменений
        else:
            main_schemas[name] = additional_schema  # Если схемы нет, добавляем ее
            changes_made = True  # Устанавливаем флаг изменений

    # Сохраняем обновленные схемы в основной файл
    with open(main_file_name, 'wb') as handle_write:
        pickle.dump(main_schemas, handle_write)  # Сохраняем все схемы в файл

    # Уведомляем пользователя о завершении синхронизации
    if changes_made:
        st.toast("Синхронизация схем завершена!", icon="✅")  # Уведомление о завершении синхронизации
    else:
        st.toast("Нет изменений для синхронизации.", icon="⚠️")  # Уведомление, если изменений не было

def import_schema(file, main_file_name: str):
    """Импортирует схему из загруженного файла в основной файл."""
    try:
        # Загружаем схемы из загруженного файла
        imported_schemas = pickle.load(file)
        
        # Загружаем существующие схемы из основного файла
        main_schemas = load_schemas(main_file_name)

        # Получаем список названий схем для выбора
        schema_names = list(imported_schemas.keys())
        
        # Выбор схемы для импорта
        selected_schema = st.selectbox("Выберите схему для импорта", schema_names)

        if st.button("Импортировать"):
            if selected_schema in main_schemas:
                st.warning(f"Схема '{selected_schema}' уже существует.")  # Уведомляем, если схема уже существует
            else:
                main_schemas[selected_schema] = imported_schemas[selected_schema]  # Импортируем схему
                st.toast(f"Схема '{selected_schema}' успешно импортирована!")  # Уведомляем об успешном импорте

                # Сохраняем обновленные схемы в основной файл
                with open(main_file_name, 'wb') as handle_write:
                    pickle.dump(main_schemas, handle_write)  # Сохраняем изменения в файл

    except Exception as e:
        st.error(f"Ошибка при импорте схемы: {e}")  # Уведомляем об ошибке

def export_schema(main_file_name: str):
    """Экспортирует выбранную схему в отдельный файл."""
    main_schemas = load_schemas(main_file_name)  # Загружаем основные схемы
    
    if main_schemas:
        schema_names = list(main_schemas.keys())  # Получаем список названий схем
        
        # Выбор схемы для экспорта
        selected_schema = st.selectbox("Выберите схему для экспорта", schema_names)

        if st.button("Подготовить к экспорту"):
            schema_to_export = {selected_schema: main_schemas[selected_schema]}  # Создаем словарь с выбранной схемой
            
            # Используем имя выбранной схемы как имя файла
            export_file_name = selected_schema

            # Создаем байтовый поток для сохранения схемы
            buffer = io.BytesIO()
            pickle.dump(schema_to_export, buffer)  # Сохраняем схему в байтовый поток
            buffer.seek(0)  # Сбросить указатель на начало потока

            # Кнопка для скачивания файла
            st.download_button(
                label="Скачать схему",
                data=buffer,
                file_name=f"{export_file_name}.barfi",  # Имя файла для скачивания
                mime="application/octet-stream"  # MIME-тип для скачивания
            )
    else:
        st.warning("Нет доступных схем для экспорта.")  # Уведомляем, если нет схем для экспорта

def duplicate_schema(main_file_name: str):
    """Дублирует выбранную схему с новым именем."""
    main_schemas = load_schemas(main_file_name)  # Загружаем основные схемы
    
    if main_schemas:
        schema_names = list(main_schemas.keys())  # Получаем список названий схем
        
        # Выбор схемы для дублирования
        selected_schema = st.selectbox("Выберите схему для дублирования", schema_names)

        # Поле для ввода нового имени для дубликата
        new_schema_name = st.text_input("Введите новое имя для дубликата", value=f"{selected_schema}_copy")

        if st.button("Дублировать"):
            if new_schema_name in main_schemas:
                st.warning(f"Схема с именем '{new_schema_name}' уже существует. Выберите другое имя.")  # Уведомляем, если имя уже занято
            else:
                main_schemas[new_schema_name] = main_schemas[selected_schema]  # Создаем дубликат схемы
                st.toast(f"Схема '{selected_schema}' успешно дублирована как '{new_schema_name}'!")  # Уведомляем об успешном дублировании

                # Сохраняем обновленные схемы в основной файл
                with open(main_file_name, 'wb') as handle_write:
                    pickle.dump(main_schemas, handle_write)  # Сохраняем изменения в файл
    else:
        st.warning("Нет доступных схем для дублирования.")  # Уведомляем, если нет схем для дублирования


def make_base_blocks():
    """Создает базовые блоки для схемы."""
    feed = Block(name='Feed')  # Создаем блок "Feed"
    feed.add_output()  # Добавляем выход к блоку
    def feed_func(self):
        self.set_interface(name='Выход 1', value=4)  # Устанавливаем значение выхода
    feed.add_compute(feed_func)  # Добавляем функцию вычисления к блоку

    splitter = Block(name='Splitter')  # Создаем блок "Splitter"
    splitter.add_input()  # Добавляем вход к блоку
    splitter.add_output()  # Добавляем выход к блоку
    splitter.add_output()  # Добавляем еще один выход к блоку
    def splitter_func(self):
        in_1 = self.get_interface(name='Вход 1')  # Получаем значение входа
        value = in_1 / 2  # Делим значение входа на 2
        self.set_interface(name='Выход 1', value=value)  # Устанавливаем значение первого выхода
        self.set_interface(name='Выход 2', value=value)  # Устанавливаем значение второго выхода
    splitter.add_compute(splitter_func)  # Добавляем функцию вычисления к блоку

    mixer = Block(name='Mixer')  # Создаем блок "Mixer"
    mixer.add_input()  # Добавляем вход к блоку
    mixer.add_input()  # Добавляем еще один вход к блоку
    mixer.add_output()  # Добавляем выход к блоку
    def mixer_func(self):
        in_1 = self.get_interface(name='Вход 1')  # Получаем значение первого входа
        in_2 = self.get_interface(name='Вход 2')  # Получаем значение второго входа
        value = in_1 + in_2  # Складываем значения входов
        self.set_interface(name='Выход 1', value=value)  # Устанавливаем значение выхода
    mixer.add_compute(mixer_func)  # Добавляем функцию вычисления к блоку

    result = Block(name='Result')  # Создаем блок "Result"
    result.add_input()  # Добавляем вход к блоку
    def result_func(self):
        in_1 = self.get_interface(name='Вход 1')  # Получаем значение входа
    result.add_compute(result_func)  # Добавляем функцию вычисления к блоку
    
    return [feed, splitter, mixer, result]  # Возвращаем список созданных блоков

def main(): 
    st.title("Редактор Barfi-схем")  # Заголовок приложения

    # Проверка состояния сессии для автоматической консолидации
    if 'synchronized' not in st.session_state:
        main_file = 'schemas.barfi'  # Основной файл
        additional_directory = 'files'  # Директория с дополнительными файлами
        synchronize_schemas(main_file, additional_directory)  # Синхронизируем схемы
        st.session_state.synchronized = True  # Устанавливаем флаг, что синхронизация выполнена
    # Проверка и создание бэкапа каждые 15 минут
    check_and_create_backup('schemas.barfi')

    # Создаем боковое меню для навигации
    menu = st.sidebar.radio("Меню", [ 
        "Создание схемы",  
        "Список схем",  
        "Редактор схем",
        "Удаление схемы", 
        "Синхронизация схем",
        "Импорт схемы", 
        "Экспорт схемы",
        "Дублировать схему"
    ]) 

    if menu == "Создание схемы": 
        st.header("Создание схемы")  # Заголовок для создания схемы
        name = st.text_input("Название схемы")  # Поле для ввода названия схемы
        schema_data = st.text_area("Данные схемы")  # Поле для ввода данных схемы
        st.button("Сохранить", on_click=create_scheme, args=(name, schema_data, ))  # Кнопка для сохранения схемы
        st.subheader("Пример данных схемы")  # Подзаголовок для примера
        st.code(
            '''
            {
            'nodes': [
                {
                'type': 'Feed', 
                'id': 'node_17341976050490', 
                'name': 'Feed-1', 
                'options': [], 
                'state': {}, 
                'interfaces': [[
                    'Output 1', 
                    {
                    'id': 'ni_17341976050491', 
                    'value': None
                    }
                ]], 
                'position': {
                    'x': 41.089179548156956, 
                    'y': 233.22473246135553
                }, 
                'width': 200, 
                'twoColumn': False, 
                'customClasses': ''
                }, 
                {
                'type': 'Result', 
                'id': 'node_17341976077762', 
                'name': 'Result-1', 
                'options': [], 
                'state': {}, 
                'interfaces': [[
                    'Input 1', 
                    {
                    'id': 'ni_17341976077773', 
                    'value': None
                    }
                ]], 
                'position': {
                    'x': 385.67895362663495, 
                    'y': 233.22473246135553
                }, 
                'width': 200, 
                'twoColumn': False, 
                'customClasses': ''
                }], 
                'connections': [
                {
                    'id': '17341976120417', 
                    'from': 'ni_17341976050491', 
                    'to': 'ni_17341976077773'
                }
                ], 
                'panning': {
                    'x': 8.137931034482762, 
                    'y': 4.349583828775266
                }, 
                'scaling': 0.9344444444444444
            }''', 'javascript')  # Пример данных схемы в формате JavaScript

    elif menu == "Удаление схемы": 
        st.header("Удаление схемы")  # Заголовок для удаления схемы 
        if len(barfi_schemas()) == 0:
            st.toast("Схемы не найдены", icon='⚠️')  # Уведомляем, если схемы не найдены
        else:
            option = st.selectbox(
                "Выберите схему",
                tuple(barfi_schemas()),  # Список доступных схем
                index=None,
            )
            if option:
                st.button("Удалить", on_click=delete_scheme, args=(option,))  # Кнопка для удаления схемы
  
    elif menu == "Список схем":
        st.header("Список схем")  # Заголовок для списка схем
        schemas = barfi_schemas()  # Получаем список схем
        if not schemas:
            st.write("Схемы не найдены.")  # Уведомляем, если схемы не найдены
        else:
            for item in schemas:
                st.write(item)  # Выводим каждую схему 
  
    elif menu == "Редактор схем":
        load_schema = st.selectbox('Выберите схему для просмотра:', barfi_schemas())  # Выбор схемы для редактирования
        barfi_result = st_barfi(base_blocks=make_base_blocks(), load_schema=load_schema, compute_engine=False)  # Отображаем схему

        if barfi_result:
            st.write(barfi_result)  # Выводим результат работы схемы

    elif menu == "Синхронизация схем":
        st.header("Синхронизация схем")  # Заголовок для синхронизации схем
        main_file = 'schemas.barfi'  # Основной файл
        additional_directory = 'files'  # Директория с дополнительными файлами

        if st.button("Синхронизировать"):
            synchronize_schemas(main_file, additional_directory)  # Синхронизируем схемы


    elif menu == "Импорт схемы":
        st.header("Импорт схемы")  # Заголовок для импорта схемы
        uploaded_file = st.file_uploader("Выберите файл .barfi", type=["barfi"])  # Загрузка файла
        if uploaded_file is not None:
            import_schema(uploaded_file, 'schemas.barfi')  # Импортируем схему из загруженного файла

    elif menu == "Экспорт схемы":
        st.header("Экспорт схемы")  # Заголовок для экспорта схемы
        export_schema('schemas.barfi')  # Экспортируем схему в файл

    elif menu == "Дублировать схему":
        st.header("Дублировать схему")  # Заголовок для дублирования схемы
        duplicate_schema('schemas.barfi')  # Дублируем схему

# Запуск основной функции
if __name__ == "__main__":
    main()
