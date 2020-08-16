import os
import sys
import shutil


def is_in_path(path, name):
    if name in os.listdir(path):
        return True
    return False


def yes_no_sensitive(phrase: str) -> bool:
    answer = input(f"{phrase} [Yes / no] ")
    if answer.isalpha() and "Yes" in answer:
        return True
    if answer.isalpha() and "n" in answer.lower():
        return False
    print("The answer doesn't match! Try again!")
    return yes_no_sensitive(phrase)


def url_check(base_url: str) -> bool:
    url = input("Please provide the search url: ")
    if base_url in url:
        return url
    print("Sorry the provided url is invalid! Try again.")
    return url_check(base_url)


def folder_exists_check(path, folder_name):
    if folder_name in os.listdir(path):
        return True
    return False


def make_folder(path):
    folder = input("Name your search: ")
    folder_path = f"{path}/{folder}"
    if folder_exists_check(path, folder):
        if yes_no_sensitive("Do you want to overwrite? All data will be lost! "):
            shutil.rmtree(folder_path, ignore_errors=True)
            os.mkdir(folder_path)
        else:
            make_folder(path)

    else:
        os.mkdir(f"{path}/{folder}")
    return folder_path


def numeric_selector(selections: dict):
    resp = input("Select number: ")
    if resp.isnumeric():
        if int(resp) <= len(selections):
            return int(resp)
        else:
            print("Please provide valid number")
            return numeric_selector(selections)
    else:
        print("Only numbers are supported! Try again.")
        return numeric_selector(selections)
