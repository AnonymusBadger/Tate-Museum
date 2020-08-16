import os
import sys

import database
from checkers import make_folder, numeric_selector, url_check
from decorators import body, footer, head
from fixers import set_first_page
from licences import select_license
from scraper import main as crawler
from text import center_text


class Screen:
    def __init__(self, options: dict = None):
        self._options = options

    @head
    def head(self, item, *args, **kwargs):
        if callable(item):
            return item(*args, **kwargs)
        print(item)

    @body
    def pbody(self, item, *args, **kwargs):
        if callable(item):
            return item(*args, **kwargs)
        print(item)

    @body
    def options(self):
        print(*[f"[{key}] {self._options[key][0]} " for key in self._options],)

    @footer
    def select(self):
        return numeric_selector(self._options)


class Scrape(Screen):
    def __init__(self, path, *args, **kwargs):
        self._base_url = "https://www.tate.org.uk/search"
        self._title = center_text("New Search")
        self._path = path
        self._options = {
            1: ("Start", True),
            # 2: ("Without images", False),
            0: ("Back", None),
        }
        super().__init__(options=self._options)

    def print(self):
        def new_search(resp, path, base_url):
            url = url_check(base_url)
            url = set_first_page(url)
            selector = self._options[resp][1]
            return url, make_folder(path), selector

        os.system("clear")
        self.head(self._title)
        self.options()
        resp = self.select()
        if resp == 0:
            return
        url, save_path, selector = self.pbody(
            new_search, resp=resp, path=self._path, base_url=self._base_url
        )
        crawler(url, save_path)
        input("Press Enter to continue")


class dbEditor(Screen):
    def __init__(self, database):
        self._title = center_text(f"Editing: {database[0]}")
        self._database = database[0]
        self._db_path = database[1]
        self._options = {
            1: ("Delete", None),
            0: ("Back", None),
        }

    def print(self):
        os.system("clear")
        self.head(self._title)
        self.options()
        resp = self.select()
        if resp == 0:
            return
        return


class Database(Screen):
    def __init__(self, path, *args, **kwargs):
        self._title = center_text("Database Explorer")
        self._path = path
        self._options = {}
        self.db = database.Database(path)
        super().__init__(options=self._options)

    def print(self):
        while True:
            os.system("clear")
            self.head(self._title)
            dbs = self.db.find_db()
            [
                self._options.update({n: (dbs.get(n), f"{self._path}/{dbs.get(n)}")})
                for n in dbs
            ]
            self._options.update({0: ("Back", None)})
            self.options()
            resp = self.select()
            if resp == 0:
                return
            database = self._options.get(resp)
            dbEditor(database).print()


class MainMenu(Screen):
    def __init__(self, licence_, author, title, description, year, *args, **kwargs):
        self._license = center_text(
            select_license(licence_, author, title, description, year)
        )
        self._options = {
            1: ("New Search", Scrape),
            # 2: ("Database Explorer", Database),
            0: ("Quit", None),
        }
        super().__init__(options=self._options)

    def print(self):
        os.system("clear")
        self.head(self._license)
        self.options()
        resp = self.select()
        if resp == 0:
            sys.exit()
        return self._options[resp][1]


class UI:
    def __init__(self, path, *args, **kwargs):
        self._main = MainMenu(*args, **kwargs)
        self._path = path

    def start(self, *args, **kwargs):
        while True:
            next_manu = self._main.print()
            next_manu(path=self._path, *args, **kwargs).print()


def main(path):
    ui = UI(
        author="Kajetan Orzełek",
        year=2020,
        title="Tate Museum",
        description="Tate Museum artwork data scraper",
        licence_="GPL3",
        path=path,
    )
    ui.start()
