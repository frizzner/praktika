# Prystupa Anton ipz23 
#Variant 22
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════╗
║        ТРЕКЕР ПРОЄКТІВ  (Python)         ║
╚══════════════════════════════════════════╝
"""

from datetime import date, datetime
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Optional


# ─────────────────────────────────────────
#  Перерахування статусів
# ─────────────────────────────────────────

class ProjectStatus(Enum):
    ACTIVE    = "Активний"
    ON_HOLD   = "На паузі"
    COMPLETED = "Завершено"
    CANCELLED = "Скасовано"

class TaskStatus(Enum):
    TODO        = "Очікує"
    IN_PROGRESS = "В процесі"
    DONE        = "Виконано"


# ─────────────────────────────────────────
#  Моделі даних
# ─────────────────────────────────────────

@dataclass
class Task:
    id:       int
    title:    str
    status:   TaskStatus
    deadline: date

    def is_overdue(self) -> bool:
        return self.status != TaskStatus.DONE and self.deadline < date.today()

    def status_icon(self) -> str:
        icons = {
            TaskStatus.TODO:        "○",
            TaskStatus.IN_PROGRESS: "◑",
            TaskStatus.DONE:        "●",
        }
        return icons[self.status]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.name,
            "deadline": self.deadline.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(
            id=data["id"],
            title=data["title"],
            status=TaskStatus[data["status"]],
            deadline=parse_date(data["deadline"]) or date.today(),
        )


@dataclass
class Project:
    id:          int
    name:        str
    description: str
    status:      ProjectStatus
    deadline:    date
    tasks:       list = field(default_factory=list)
    _next_task_id: int = field(default=1, repr=False)

    def is_overdue(self) -> bool:
        return (
            self.status not in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED)
            and self.deadline < date.today()
        )

    def overdue_tasks(self) -> list:
        return [t for t in self.tasks if t.is_overdue()]

    def stats(self) -> dict:
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t.status == TaskStatus.DONE)
        return {"total": total, "done": done,
                "pct": int(done / total * 100) if total else 0}

    def next_task_id(self) -> int:
        tid = self._next_task_id
        self._next_task_id += 1
        return tid

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.name,
            "deadline": self.deadline.isoformat(),
            "tasks": [t.to_dict() for t in self.tasks],
            "_next_task_id": self._next_task_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "Project":
        p = Project(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=ProjectStatus[data["status"]],
            deadline=parse_date(data["deadline"]) or date.today(),
        )
        p.tasks = [Task.from_dict(td) for td in data.get("tasks", [])]
        p._next_task_id = data.get(
            "_next_task_id",
            max((t.id for t in p.tasks), default=0) + 1,
        )
        return p


# ─────────────────────────────────────────
#  Допоміжні функції виводу
# ─────────────────────────────────────────

LINE  = "─" * 62
DLINE = "═" * 62

def hr(char="─", n=62):
    print(char * n)

def parse_date(s: str) -> Optional[date]:
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None

def fmt_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")

def days_left(d: date) -> str:
    delta = (d - date.today()).days
    if delta < 0:
        return f"⚠ прострочено на {-delta} дн."
    if delta == 0:
        return "⚡ сьогодні!"
    return f"залишилось {delta} дн."

def progress_bar(pct: int, width: int = 20) -> str:
    filled = int(width * pct / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}] {pct}%"


# ─────────────────────────────────────────
#  Введення з валідацією
# ─────────────────────────────────────────

def input_str(prompt: str, allow_empty: bool = False) -> str:
    while True:
        val = input(f"  {prompt}").strip()
        if val or allow_empty:
            return val
        print("  Поле не може бути порожнім.")

def input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    while True:
        try:
            val = int(input(f"  {prompt}"))
            if (min_val is None or val >= min_val) and (max_val is None or val <= max_val):
                return val
            print(f"  Введіть число від {min_val} до {max_val}.")
        except ValueError:
            print("  Введіть ціле число.")

def input_date(prompt: str) -> date:
    while True:
        s = input(f"  {prompt} (ДД.ММ.РРРР): ").strip()
        d = parse_date(s)
        if d:
            return d
        print("  Невірний формат. Приклад: 31.12.2026")

def input_choice(prompt: str, options: dict):
    print(f"  {prompt}")
    for k, v in options.items():
        label = v.value if hasattr(v, "value") else v
        print(f"    {k}. {label}")
    keys = list(options.keys())
    while True:
        choice = input_int(f"Вибір ({keys[0]}–{keys[-1]}): ", min_val=keys[0], max_val=keys[-1])
        if choice in options:
            return options[choice]
        print("  Невірний вибір. Спробуйте ще раз.")

def confirm(prompt: str) -> bool:
    while True:
        ans = input(f"  {prompt} (y/n): ").strip().lower()
        if ans in ("д", "y", "yes", "так", "1"):
            return True
        if ans in ("н", "n", "no", "ні", "0"):
            return False
        print("  Будь ласка, введіть 'y' або 'n'.")


# ─────────────────────────────────────────
#  Клас трекера
# ─────────────────────────────────────────

class ProjectTracker:
    DATA_FILE = Path(__file__).with_suffix(".json")

    def __init__(self):
        self.projects: list[Project] = []
        self._next_project_id = 1
        self.load_data()

    def save_data(self) -> None:
        data = {
            "next_project_id": self._next_project_id,
            "projects": [p.to_dict() for p in self.projects],
        }
        try:
            with open(self.DATA_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except OSError as err:
            print(f"  Не вдалося зберегти дані: {err}")

    def load_data(self) -> None:
        if not self.DATA_FILE.exists():
            return
        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._next_project_id = data.get("next_project_id", 1)
            self.projects = [Project.from_dict(pd) for pd in data.get("projects", [])]
            if self.projects:
                highest = max(p.id for p in self.projects)
                self._next_project_id = max(self._next_project_id, highest + 1)
            else:
                self._next_project_id = 1
        except (OSError, json.JSONDecodeError, KeyError) as err:
            print(f"  Помилка при завантаженні даних: {err}")
            print("  Дані ігноруються, можна продовжити роботу з порожньою базою.")

    # ── пошук ────────────────────────────

    def _find_project(self, pid: int) -> Optional[Project]:
        return next((p for p in self.projects if p.id == pid), None)

    def _find_task(self, project: Project, tid: int) -> Optional[Task]:
        return next((t for t in project.tasks if t.id == tid), None)

    def _pick_project(self) -> Optional[Project]:
        pid = input_int("ID проєкту: ")
        p = self._find_project(pid)
        if not p:
            print("  Проєкт не знайдено.")
        return p

    def _pick_task(self, project: Project) -> Optional[Task]:
        tid = input_int("ID задачі: ")
        t = self._find_task(project, tid)
        if not t:
            print("  Задачу не знайдено.")
        return t

    # ══════════════════════════════════════
    #  ПРОЄКТИ
    # ══════════════════════════════════════

    def list_projects(self):
        if not self.projects:
            print("  Проєктів немає.")
            return
        hr("═")
        print(f"  ПРОЄКТИ  (сьогодні: {fmt_date(date.today())})")
        hr("═")
        print(f"  {'#':<4} {'Назва':<22} {'Статус':<12} {'Дедлайн':<12} {'Задачі':<8} Прогрес")
        hr()
        for p in self.projects:
            stats = p.stats()
            flag  = " ⚠" if p.is_overdue() else ""
            bar   = progress_bar(stats["pct"], 10)
            print(f"  {p.id:<4} {p.name[:21]:<22} {p.status.value:<12} "
                  f"{fmt_date(p.deadline):<12} "
                  f"{stats['done']}/{stats['total']:<5} {bar}{flag}")
        hr()

    def view_project(self):
        p = self._pick_project()
        if not p: return

        hr("═")
        flag = "  ⚠ ПРОСТРОЧЕНО" if p.is_overdue() else ""
        print(f"  Проєкт #{p.id}: {p.name}{flag}")
        print(f"  Статус  : {p.status.value}")
        print(f"  Дедлайн : {fmt_date(p.deadline)}  ({days_left(p.deadline)})")
        if p.description:
            print(f"  Опис    : {p.description}")
        stats = p.stats()
        print(f"  Прогрес : {progress_bar(stats['pct'])}  "
              f"({stats['done']}/{stats['total']} задач)")
        hr("═")

        if not p.tasks:
            print("  Задач немає.")
        else:
            print(f"  {'#':<4} {'Назва':<28} {'Статус':<12} {'Дедлайн':<12} Стан")
            hr()
            for t in p.tasks:
                flag = "  ⚠ прострочено" if t.is_overdue() else ""
                print(f"  {t.status_icon()} {t.id:<3} {t.title[:27]:<28} "
                      f"{t.status.value:<12} {fmt_date(t.deadline):<12}{flag}")
        hr()

    def add_project(self):
        hr()
        print("  НОВИЙ ПРОЄКТ")
        hr()
        name = input_str("Назва: ")
        desc = input_str("Опис (необов.): ", allow_empty=True)
        status = input_choice("Статус:", {
            1: ProjectStatus.ACTIVE,
            2: ProjectStatus.ON_HOLD,
            3: ProjectStatus.COMPLETED,
            4: ProjectStatus.CANCELLED,
        })
        deadline = input_date("Дедлайн")

        p = Project(
            id=self._next_project_id,
            name=name,
            description=desc,
            status=status,
            deadline=deadline,
        )
        self._next_project_id += 1
        self.projects.append(p)
        self.save_data()
        print(f"  ✓ Проєкт #{p.id} «{p.name}» створено.")

    def edit_project(self):
        p = self._pick_project()
        if not p: return

        print(f"  Редагування проєкту #{p.id} «{p.name}»")
        print("  (Enter — не змінювати)")

        name = input(f"  Назва [{p.name}]: ").strip()
        if name: p.name = name

        desc = input(f"  Опис [{p.description}]: ").strip()
        if desc: p.description = desc

        if confirm("Змінити статус?"):
            p.status = input_choice("Новий статус:", {
                1: ProjectStatus.ACTIVE,
                2: ProjectStatus.ON_HOLD,
                3: ProjectStatus.COMPLETED,
                4: ProjectStatus.CANCELLED,
            })
        if confirm("Змінити дедлайн?"):
            p.deadline = input_date("Новий дедлайн")

        self.save_data()
        print("  ✓ Проєкт оновлено.")

    def delete_project(self):
        p = self._pick_project()
        if not p: return
        if confirm(f"Видалити проєкт «{p.name}» та всі його задачі?"):
            self.projects.remove(p)
            if not self.projects:
                self._next_project_id = 1
            self.save_data()
            print("  ✓ Проєкт видалено.")

    def delete_all_projects(self):
        if not self.projects:
            print("  Проєктів немає.")
            return
        if confirm("Видалити всі проєкти та їх задачі?"):
            self.projects.clear()
            self._next_project_id = 1
            self.save_data()
            print("  ✓ Усі проєкти видалено.")

    # ══════════════════════════════════════
    #  ЗАДАЧІ
    # ══════════════════════════════════════

    def add_task(self):
        p = self._pick_project()
        if not p: return

        hr()
        print(f"  НОВА ЗАДАЧА  →  Проєкт «{p.name}»")
        hr()
        title = input_str("Назва задачі: ")
        status = input_choice("Статус:", {
            1: TaskStatus.TODO,
            2: TaskStatus.IN_PROGRESS,
            3: TaskStatus.DONE,
        })
        deadline = input_date("Дедлайн")

        t = Task(id=p.next_task_id(), title=title, status=status, deadline=deadline)
        p.tasks.append(t)
        self.save_data()
        print(f"  ✓ Задачу #{t.id} «{t.title}» додано.")

    def edit_task(self):
        p = self._pick_project()
        if not p: return
        t = self._pick_task(p)
        if not t: return

        print(f"  Редагування задачі #{t.id} «{t.title}»  (Enter — не змінювати)")
        title = input(f"  Назва [{t.title}]: ").strip()
        if title: t.title = title

        if confirm("Змінити статус?"):
            t.status = input_choice("Новий статус:", {
                1: TaskStatus.TODO,
                2: TaskStatus.IN_PROGRESS,
                3: TaskStatus.DONE,
            })
        if confirm("Змінити дедлайн?"):
            t.deadline = input_date("Новий дедлайн")

        self.save_data()
        print("  ✓ Задачу оновлено.")

    def delete_task(self):
        p = self._pick_project()
        if not p: return
        t = self._pick_task(p)
        if not t: return

        if confirm(f"Видалити задачу «{t.title}»?"):
            p.tasks.remove(t)
            self.save_data()
            print("  ✓ Задачу видалено.")

    # ══════════════════════════════════════
    #  ЗВІТИ
    # ══════════════════════════════════════

    def show_overdue(self):
        hr("═")
        print(f"  ⚠  ПРОСТРОЧЕНІ ЕЛЕМЕНТИ  (сьогодні: {fmt_date(date.today())})")
        hr("═")

        found = False
        for p in self.projects:
            block_printed = False

            def print_project_block():
                nonlocal block_printed
                if not block_printed:
                    flag = "  ← сам проєкт прострочено" if p.is_overdue() else ""
                    print(f"\n  Проєкт #{p.id} «{p.name}»{flag}")
                    block_printed = True

            if p.is_overdue():
                print_project_block()
                print(f"    дедлайн {fmt_date(p.deadline)} | {p.status.value} | "
                      f"{days_left(p.deadline)}")
                found = True

            for t in p.overdue_tasks():
                print_project_block()
                print(f"    ⚠ Задача #{t.id} «{t.title}»  — "
                      f"дедлайн {fmt_date(t.deadline)} | {t.status.value} | "
                      f"{days_left(t.deadline)}")
                found = True

        if not found:
            print("\n  Прострочених елементів немає. Все вчасно!")
        print()
        hr("═")

    def show_summary(self):
        hr("═")
        print("  ЗВЕДЕННЯ")
        hr("═")
        total_p = len(self.projects)
        active_p = sum(1 for p in self.projects if p.status == ProjectStatus.ACTIVE)
        overdue_p = sum(1 for p in self.projects if p.is_overdue())
        total_t = sum(len(p.tasks) for p in self.projects)
        done_t   = sum(sum(1 for t in p.tasks if t.status == TaskStatus.DONE) for p in self.projects)
        overdue_t = sum(len(p.overdue_tasks()) for p in self.projects)

        print(f"  Проєктів всього  : {total_p}")
        print(f"  Активних         : {active_p}")
        print(f"  Прострочених     : {overdue_p}")
        print(f"  Задач всього     : {total_t}")
        print(f"  Виконано         : {done_t}")
        print(f"  Прострочених     : {overdue_t}")
        hr("═")

    # ══════════════════════════════════════
    #  ДЕМО-ДАНІ
    # ══════════════════════════════════════

    def load_demo(self):
        # Проєкт 1 — активний, все добре
        p1 = Project(id=self._next_project_id, name="Корпоративний сайт",
                     description="Редизайн + нові розділи",
                     status=ProjectStatus.ACTIVE, deadline=date(2026, 12, 31))
        self._next_project_id += 1
        p1.tasks = [
            Task(p1.next_task_id(), "Макет головної", TaskStatus.DONE,        date(2026, 3, 1)),
            Task(p1.next_task_id(), "Верстка HTML/CSS", TaskStatus.IN_PROGRESS, date(2026, 8, 30)),
            Task(p1.next_task_id(), "SEO-оптимізація",  TaskStatus.TODO,        date(2026, 11, 30)),
        ]

        # Проєкт 2 — прострочений, є прострочена задача
        p2 = Project(id=self._next_project_id, name="Мобільний застосунок",
                     description="iOS/Android для клієнтів",
                     status=ProjectStatus.ON_HOLD, deadline=date(2026, 1, 1))
        self._next_project_id += 1
        p2.tasks = [
            Task(p2.next_task_id(), "Технічне завдання", TaskStatus.DONE,        date(2025, 11, 1)),
            Task(p2.next_task_id(), "Розробка API",      TaskStatus.IN_PROGRESS, date(2025, 12, 1)),
            Task(p2.next_task_id(), "Тестування",        TaskStatus.TODO,        date(2026, 9, 15)),
        ]

        # Проєкт 3 — завершений
        p3 = Project(id=self._next_project_id, name="Звіт Q1 2025",
                     description="Квартальна звітність",
                     status=ProjectStatus.COMPLETED, deadline=date(2025, 3, 31))
        self._next_project_id += 1
        p3.tasks = [
            Task(p3.next_task_id(), "Збір даних",     TaskStatus.DONE, date(2025, 3, 20)),
            Task(p3.next_task_id(), "Написання звіту", TaskStatus.DONE, date(2025, 3, 28)),
        ]

        self.projects.extend([p1, p2, p3])
        self.save_data()
        print("  ✓ Завантажено 3 демо-проєкти.")

    # ══════════════════════════════════════
    #  ГОЛОВНЕ МЕНЮ
    # ══════════════════════════════════════

    def run(self):
        print()
        width = 62
        inner = width - 2
        title = "ТРЕКЕР ПРОЄКТІВ  (Python)"
        print("╔" + "═" * inner + "╗")
        print("║" + title.center(inner) + "║")
        print("╚" + "═" * inner + "╝")

        MENU = {
            "── Проєкти ──────────────────────────": None,
            "1":  ("Список проєктів",          self.list_projects),
            "2":  ("Переглянути проєкт",        self.view_project),
            "3":  ("Додати проєкт",             self.add_project),
            "4":  ("Редагувати проєкт",         self.edit_project),
            "5":  ("Видалити проєкт",           self.delete_project),
            "── Задачі ───────────────────────────": None,
            "6":  ("Додати задачу",             self.add_task),
            "7":  ("Редагувати задачу",         self.edit_task),
            "8":  ("Видалити задачу",           self.delete_task),
            "── Звіти ────────────────────────────": None,
            "9":  ("Прострочені елементи",      self.show_overdue),
            "10": ("Зведення",                  self.show_summary),
            "── Інше ─────────────────────────────": None,
            "11": ("Видалити всі проєкти",      self.delete_all_projects),
            "12": ("Завантажити демо-дані",     self.load_demo),
            "0":  ("Вийти",                     None),
        }

        while True:
            print()
            hr()
            print("  МЕНЮ")
            hr()
            for key, val in MENU.items():
                if val is None and not key.isdigit():
                    print(f"  {key}")
                elif val:
                    print(f"    {key:>2}. {val[0]}")
            hr()

            choice = input("  Вибір: ").strip()
            print()

            if choice == "0":
                print("  До побачення!")
                self.save_data()
                break
            elif choice in MENU and isinstance(MENU[choice], tuple):
                MENU[choice][1]()
            else:
                print("  Невідома команда.")


# ─────────────────────────────────────────
if __name__ == "__main__":
    tracker = ProjectTracker()
    tracker.run()