import tkinter as tk
from tkinter import messagebox, ttk
import json
import urllib.request
import urllib.parse
import urllib.error
import webbrowser

# --- Конфигурация ---
SEARCH_API_URL = "https://api.github.com/search/users"  # Для поиска (требует спец. заголовок)
USER_API_URL = "https://api.github.com/users/"  # Для получения данных пользователя
FAVORITES_FILE = "C:/Users/student/PycharmProjects/favorites.json"


# --- Работа с избранным (JSON) ---
def load_favorites():
    """Загружает список избранных пользователей из файла."""
    try:
        with open(FAVORITES_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_favorites(favorites):
    """Сохраняет список избранных пользователей в файл."""
    with open(FAVORITES_FILE, 'w') as file:
        json.dump(favorites, file, indent=4)


# --- Вспомогательные функции для API ---
def search_github_users(query):
    """Выполняет поиск пользователей. Использует спец. заголовок для API v3."""
    url = SEARCH_API_URL + "?" + urllib.parse.urlencode({'q': query})
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        messagebox.showerror("Ошибка GitHub", f"Код: {e.code}\n{error_data}")
        return None
    except urllib.error.URLError as e:
        messagebox.showerror("Ошибка сети", f"Не удалось подключиться: {e.reason}")
        return None


def get_user_data(user_url):
    """Получает полные данные пользователя. Использует стандартный заголовок."""
    # user_url выглядит как 'https://github.com/username'
    # Нам нужен 'https://api.github.com/users/username'
    username = user_url.split('/')[-1]
    url = USER_API_URL + username

    try:
        # Здесь мы НЕ указываем заголовок Accept, чтобы избежать ошибки 406
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        messagebox.showerror("Ошибка GitHub", f"Код: {e.code}\n{error_data}")
        return None
    except urllib.error.URLError as e:
        messagebox.showerror("Ошибка сети", f"Не удалось получить данные пользователя: {e.reason}")
        return None


# --- Логика приложения ---
def search_users():
    """Выполняет поиск пользователей по запросу из поля ввода."""
    query = entry_search.get().strip()

    # 5. Проверка корректности ввода: поле не должно быть пустым
    if not query:
        messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым!")
        return

    data = search_github_users(query)

    if not data:
        return  # Если была ошибка сети/API, выходим

    # Очистка таблицы перед выводом новых данных
    for item in tree.get_children():
        tree.delete(item)

    if data.get('total_count', 0) == 0:
        tree.insert('', 'end', values=("Ничего не найдено", ""))
        return

    # Загружаем логины избранных для быстрой проверки
    favorites_logins = [user['login'] for user in load_favorites()]

    for user in data['items']:
        login = user['login']
        url = user['html_url']

        is_favorite = login in favorites_logins

        tree.insert('', 'end', values=(login, url),
                    tags=('favorite',) if is_favorite else ())


def toggle_favorite():
    """Добавляет или удаляет выбранного пользователя из избранного."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите пользователя из списка!")
        return

    item_values = tree.item(selected_item, 'values')
    login = item_values[0]

    favorites = load_favorites()

    # Ищем индекс пользователя в списке избранного по логину
    found_index = next((i for i, user in enumerate(favorites) if user['login'] == login), None)

    if found_index is not None:
        # --- УДАЛЕНИЕ ИЗ ИЗБРАННОГО ---
        del favorites[found_index]
        save_favorites(favorites)
        tree.item(selected_item, tags=())  # Снимаем выделение (убираем тег)
        messagebox.showinfo("Успех", f"Пользователь {login} удален из избранного.")
    else:
        # --- ДОБАВЛЕНИЕ В ИЗБРАННОЕ ---
        full_data = get_user_data(item_values[1])

        if not full_data:
            return  # Выходим, если не удалось получить данные

        favorites.append({
            'login': login,
            'html_url': full_data['html_url'],
            'avatar_url': full_data['avatar_url']
        })

        save_favorites(favorites)

        # Обновляем таблицу (выделяем строку)
        tree.item(selected_item, tags=('favorite',))

        messagebox.showinfo("Успех", f"Пользователь {login} добавлен в избранное.")


def open_profile(event):
    """Открывает профиль пользователя в браузере при двойном клике."""
    selected_item = tree.selection()
    if selected_item:
        item_values = tree.item(selected_item, 'values')
        url = item_values[1]
        webbrowser.open(url)


# --- Создание графического интерфейса (GUI) ---
root = tk.Tk()
root.title("GitHub User Finder")
root.geometry("600x400")

style = ttk.Style()
style.configure("Treeview", rowheight=25)
style.configure("favorite.Treeview", foreground="red")

frame_top = tk.Frame(root)
frame_top.pack(pady=10, fill='x')

entry_search = tk.Entry(frame_top, font=('Arial', 12), width=40)
entry_search.pack(side='left', expand=True, fill='x', padx=5)

btn_search = tk.Button(frame_top, text="Поиск", command=search_users)
btn_search.pack(side='left', padx=5)

btn_favorite = tk.Button(frame_top, text="В избранное", command=toggle_favorite)
btn_favorite.pack(side='left', padx=5)

tree = ttk.Treeview(root, columns=("Логин", "Ссылка"), show='headings')
tree.heading("Логин", text="Логин")
tree.heading("Ссылка", text="Ссылка")
tree.column("Ссылка", minwidth=0, width=0, stretch=False)
tree.pack(expand=True, fill='both', padx=10, pady=10)
tree.tag_configure('favorite', foreground='red')
tree.bind("<Double-1>", open_profile)

root.mainloop()