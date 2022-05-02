import requests
import os
from datetime import datetime


def data_checkout(user):
    """Ф-ия для проверки данных по основным полям json-файла,
    необходимых для составления отчета, аргумент: словарь по юзеру.

    Поля: id, username, name, email, company. (id и username - ключевые, без них точно отчет составить нельзя,
    остальные поля в списке, потому что без них хоть и можно составить отчет, но он будет неполноценным).

    Ищем соответствия в ключах текущего json-файла юзера (словаре), перебираем checkout_list.
    """
    checkout_list = ['id', 'username', 'name', 'email', 'company']
    for key_name in checkout_list:
        if key_name not in list(user.keys()):
            print(f'Невозможно сгенерировать отчет, отсутствует поле {key_name} пользователя')
            return True


def files_rename(all_users, path):
    """Ф-ия для переименовывания старых отчетов,
    если они существуют, аргументы: список словарей юзеров, путь директории.

    files_in_tasks содержит список название файлов в директории tasks.
    files_to_make_names содержит названия файлов, которые будут созданы.

    Если файл существует в директории,
    то он будет переименован по формату: old_Username_year-month-dayThours:minutes.txt
    Время берется системное, когда файл был создан.
    """
    files_in_tasks = os.listdir(path)
    files_to_make_names = [current_user["username"] + ".txt" for current_user in all_users]
    for file_name in files_to_make_names:
        if file_name in files_in_tasks:
            old_name = os.path.join(path, file_name)
            file_time_creation_unix = os.path.getctime(path + f'/{file_name}')
            file_time_creation = datetime.fromtimestamp(file_time_creation_unix).isoformat("T", "minutes")
            new_name = os.path.join(path, f"old_{file_name.partition('.txt')[0]}_{file_time_creation}.txt")
            os.rename(old_name, new_name)


def get_task_title(tasks):
    """Ф-ия получения названия файлов, аргумент - список названий задач юзера.
    Сначала проверяется, есть ли вообще у пользователя задачи, так как аргумент ф-ии - список названий тасков, то
    проверяется кол-во элементов этого списка, если он пустой, значит, задач нет.

    Если задачи имеются, тогда генерируется список (result) задач с проверкой на длину до 48 символов,
    затем преобразуется в строку со всеми задачами (one_string_result).
    """
    if len(tasks) == 0:
        print('У пользователя нет задач')
        return ''
    else:
        result = [task['title'] if len(task['title']) <= 48 else task['title'][:48] + '...' for task in tasks]
        one_string_result = '\n'.join(result)
        return one_string_result


def generate_reports(all_users, all_todos):
    """Ф-ия для создания отчетов, аргументы: список словарей юзеров и список словарей тасков.

    В цикле выбирается словарь из списка, сначала проверяется, что все необходимые поля у словаря имеются вызовом
    ф-ии data_checkout, в случае, если данных не хватает, цикл переходит на следующего юзера.

    completed_tasks - список выполненных тасков юзером.
    not_completed_tasks - список невыполненных тасков юзером.

    Во внутреннем цикле перебираем задачи, ищем соответствие по ключу (id (из юзеров) = userId (из задач)).
    По полю completed решаем в какой список добавить название таска.

    Текст отчета формируется с помощью форматируемой мульти-лайн строки.

    exception общий на системные ошибки.
    """
    for current_user in all_users:
        if data_checkout(current_user):
            continue
        else:
            try:
                with open(f'tasks/{current_user["username"] + ".txt"}', 'w') as report:
                    completed_tasks = []
                    not_completed_tasks = []
                    for current_todo in all_todos:
                        if 'userId' in current_todo and current_user['id'] == current_todo['userId']:
                            if current_todo['completed']:
                                completed_tasks.append(current_todo)
                            elif not current_todo['completed']:
                                not_completed_tasks.append(current_todo)

                    text = f"""Отчет для {current_user["company"]["name"]}.
{current_user["name"]} <{current_user["email"]}> {datetime.now().strftime("%d.%m.%Y %H:%M")}
Всего задач: {len(completed_tasks) + len(not_completed_tasks)}

Завершенные задачи({len(completed_tasks)}):
{get_task_title(completed_tasks)}

Оставшиеся задачи({len(not_completed_tasks)}):
{get_task_title(not_completed_tasks)}"""

                    report.write(text)

            except OSError as error:
                print(f"{type(error)}: {error}")


def tasks_checkout_and_create(script_path, users, todos):
    """Ф-ия проверки наличия директории tasks/ее создание,
    аргументы: путь к скрипту, список словарей пользователей, список словарей задач.

    Если директория не существует, тогда она создается, затем вызывается ф-ия generate_reports.
    Если директория существует, тогда сначала ф-ия переименовывания файлов, а затем создания новых отчетов.
    """
    if not os.path.exists(script_path):
        os.mkdir(script_path)
        generate_reports(users, todos)
    else:
        files_rename(users, script_path)
        generate_reports(users, todos)


if __name__ == '__main__':

    get_script_path = os.path.abspath('script.py').partition('script.py')[0] + 'tasks'

    for i in range(10):
        try:
            get_users = requests.get('https://json.medrating.org/users').json()
            get_todos = requests.get('https://json.medrating.org/todos').json()
            tasks_checkout_and_create(get_script_path, get_users, get_todos)
        except requests.exceptions.Timeout as e:
            print(e)
        except requests.exceptions.ConnectionError as e:
            print(e)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        else:
            break
