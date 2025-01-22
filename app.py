import streamlit as st
import json
import pickle
from barfi import st_barfi, barfi_schemas, Block


# Существующий функционал
def load_schemas():
    try:
        with open('schemas.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}


def save_schemas(schemas):
    with open('schemas.pkl', 'wb') as f:
        pickle.dump(schemas, f)


def save_schema(name, schema):
    schemas = load_schemas()
    schemas[name] = schema
    save_schemas(schemas)


def delete_schema(name):
    schemas = load_schemas()
    if name in schemas:
        del schemas[name]
        save_schemas(schemas)
        return True
    else:
        return False


def merge_schemas(files):
    merged_schemas = load_schemas()
    merged_schema = {}

    for file in files:
        try:
            if file.name.endswith('.barfi'):
                new_schemas = json.loads(file.getvalue().decode('utf-8'))
            elif file.name.endswith('.pkl'):
                new_schemas = pickle.loads(file.getvalue())
            else:
                st.error(f"Некорректный формат файла: {file.name}")
                continue

            # Объединение всех схем в одну объединенную схему
            for name, schema in new_schemas.items():
                if name in merged_schema:
                    new_name = f"{name}_merged"
                    st.warning(f"Конфликт для {name}. Переименовано в {new_name}")
                    merged_schema[new_name] = schema
                else:
                    merged_schema[name] = schema

        except json.JSONDecodeError as je:
            st.error(f"Ошибка при загрузке JSON файла {file.name}: {je}")
        except pickle.UnpicklingError as pe:
            st.error(f"Ошибка при загрузке pickle файла {file.name}: {pe}")
        except Exception as e:
            st.error(f"Ошибка при загрузке файла {file.name}: {e}")

    # Сохранение объединенной схемы под именем merged_schema
    merged_schemas["merged_schema"] = merged_schema
    save_schemas(merged_schemas)
    return merged_schemas


def export_schema_json(schema, filename):
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=4)


def import_schema_json(file):
    try:
        return json.load(file)
    except json.JSONDecodeError:
        st.error("Некорректный JSON формат")
        return None


# Основное приложение Streamlit
def main():
    st.title("Редактор Barfi-схем")

    # Sidebar для навигации
    menu = st.sidebar.radio("Меню", [
        "Создание схемы",
        "Список схем",
        "Просмотр схемы",
        "Удаление схемы",
        "Слияние схем",
        "Импорт/Экспорт JSON"
    ])

    if menu == "Создание схемы":
        st.header("Создание схемы")

        # Создание блоков схемы
        feed = Block(name='Feed')
        feed.add_output()

        def feed_func(self):
            self.set_interface(name='Output 1', value=4)

        feed.add_compute(feed_func)

        splitter = Block(name='Splitter')
        splitter.add_input()
        splitter.add_output()
        splitter.add_output()

        def splitter_func(self):
            in_1 = self.get_interface(name='Input 1')
            value = (in_1 / 2)
            self.set_interface(name='Output 1', value=value)
            self.set_interface(name='Output 2', value=value)

        splitter.add_compute(splitter_func)

        mixer = Block(name='Mixer')
        mixer.add_input()
        mixer.add_input()
        mixer.add_output()

        def mixer_func(self):
            in_1 = self.get_interface(name='Input 1')
            in_2 = self.get_interface(name='Input 2')
            value = (in_1 + in_2)
            self.set_interface(name='Output 1', value=value)

        mixer.add_compute(mixer_func)

        result = Block(name='Result')
        result.add_input()

        def result_func(self):
            in_1 = self.get_interface(name='Input 1')

        result.add_compute(result_func)

        # Создание и работа с схемой Barfi
        load_schema = st.selectbox('Выберите сохраненную схему:', barfi_schemas())
        compute_engine = st.checkbox('Активировать вычислительный движок Barfi', value=False)
        barfi_result = st_barfi(base_blocks=[feed, result, mixer, splitter], compute_engine=compute_engine,
                                load_schema=load_schema)

    elif menu == "Список схем":
        st.header("Список схем")
        schemas = load_schemas()
        for name in schemas.keys():
            st.write(name)

    elif menu == "Просмотр схемы":
        st.header("Просмотр схемы")
        schemas = load_schemas()
        schema_name = st.selectbox("Выберите схему", list(schemas.keys()))
        if schema_name:
            schema_data = schemas[schema_name]
            st.json(schema_data)  # Вывод данных в формате JSON

    elif menu == "Удаление схемы":
        st.header("Удаление схемы")
        schema_name = st.text_input("Название схемы для удаления")
        if st.button("Удалить"):
            if delete_schema(schema_name):
                st.success(f"Схема '{schema_name}' удалена.")
            else:
                st.error("Схема не найдена.")

    elif menu == "Слияние схем":
        st.header("Слияние схем")
        uploaded_files = st.file_uploader(
            "Выберите .barfi файлы",
            type=['barfi', 'pkl'],
            accept_multiple_files=True
        )
        if st.button("Объединить схемы"):
            if uploaded_files:
                merged_schemas = merge_schemas(uploaded_files)
                st.success("Схемы объединены")
            else:
                st.error("Не выбраны файлы для слияния")

    elif menu == "Импорт/Экспорт JSON":
        # Если пользователь выбрал пункт меню "Импорт/Экспорт JSON"
         st.header("Импорт/Экспорт JSON")
         # Отображаем заголовок для этого раздела
         action = st.radio("Выберите действие", ["Импорт", "Экспорт"])
         # Создаем radio button для выбора действия: "Импорт" или "Экспорт"

         if action == "Импорт":
             # Если выбрано действие "Импорт"
             uploaded_file = st.file_uploader("Загрузите файл JSON", type="json")
             # Создаем загрузчик файлов, принимающий только JSON-файлы
             if uploaded_file:
                # Если файл был загружен
                imported_schema = import_schema_json(uploaded_file)
                # Вызываем функцию import_schema_json для обработки загруженного файла
                if imported_schema:
                    # Если импорт схемы прошел успешно
                    schema_name = st.text_input("Введите имя для сохранения импортированной схемы")
                    # Создаем текстовое поле для ввода имени схемы
                    if schema_name:
                        # Если имя схемы введено
                        save_schema(schema_name, imported_schema)
                        # Вызываем функцию save_schema для сохранения импортированной схемы
                        st.success(f"Схема '{schema_name}' успешно импортирована и сохранена")
                        # Отображаем сообщение об успешном импорте и сохранении схемы
                    else:
                        st.error("Не указано имя для сохранения схемы.")
                        # Отображаем ошибку, если не введено имя схемы
                else:
                      st.error("Ошибка при импорте JSON")
                      # Отображаем ошибку, если импорт JSON не удался
         elif action == "Экспорт":
            # Если выбрано действие "Экспорт"
            schemas = load_schemas()
            # Загружаем все сохраненные схемы
            if schemas:
                # Если есть сохраненные схемы
                selected_schema_name = st.selectbox("Выберите схему для экспорта", list(schemas.keys()))
                # Создаем выпадающий список для выбора схемы для экспорта
                if selected_schema_name:
                    # Если выбрана схема
                    selected_schema = schemas[selected_schema_name]
                    # Получаем выбранную схему из словаря схем
                    if isinstance(selected_schema, str):
                        # Если схема - строка (JSON), парсим ее в словарь
                        selected_schema = json.loads(selected_schema)

                    filename = st.text_input("Введите имя файла для экспорта", value=f"{selected_schema_name}.json")
                    # Создаем текстовое поле для ввода имени файла экспорта, по умолчанию ставим имя схемы + .json
                    if st.button("Экспортировать"):
                       # Если нажата кнопка "Экспортировать"
                       if filename:
                            # Если имя файла введено
                             export_schema_json(selected_schema, filename)
                             # Вызываем функцию export_schema_json для экспорта схемы в JSON-файл
                             st.success(f"Схема экспортирована в '{filename}'")
                             # Отображаем сообщение об успешном экспорте
                       else:
                           st.error("Имя файла для экспорта не указано")
                           # Отображаем ошибку, если имя файла не введено
            else:
                st.write("Нет сохраненных схем для экспорта.")
                # Отображаем сообщение, если нет сохраненных схем


if __name__ == "__main__":
    main()
