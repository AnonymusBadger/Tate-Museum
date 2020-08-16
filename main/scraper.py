import asyncio
import json
import logging
import os
import re

# import socket
from asyncio import sleep
from pprint import pprint as pp
from random import randint

import aiohttp
import pandas
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from math import ceil

# from lxml import html


logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(message)s", datefmt="%H:%M:%S",
)


async def get_page(url, session):
    logging.debug(f"Trying {url}")
    # await sleep(randint(0, 2))
    async with session.get(url) as resp:
        logging.debug(f"Got response [{resp.status}] for URL: {url}")
        html = await resp.read()
        return BeautifulSoup(html, "html.parser")


async def get_image(url, title, path, session):
    try:
        if len(url) < 1:
            return
        logging.debug(f"Downloading Image {url}")
        if "/" in title:
            title = re.sub("/", "\\\\", title)
        if "Images" not in os.listdir(path):
            os.mkdir(f"{path}/Images")
        file = f"{path}/Images/{title}.jpg"
        async with session.get(url) as resp:
            with open(file, "wb") as fd:
                while True:
                    await sleep(0.1)
                    chunk = await resp.content.read(1000000)
                    if not chunk:
                        logging.debug(f"Finished Downloading {url}")
                        break
                    fd.write(chunk)
    except Exception:
        pass


async def get_one(base_url, *args, **kwargs):
    soup = await get_page(*args, **kwargs)
    arts = soup.findAll("div", class_="card")
    links = [f"{base_url}{item.find('a').get('href')}" for item in arts]
    return links


async def get_artwork_urls(base_url, query, session):
    start = await get_page(query, session)
    total_artworks = (
        start.find("span", class_="card-group__range-last").find_parent().text
    )
    temp = re.findall(r"\d+", total_artworks)
    res = list(map(int, temp))[-1]
    if res <= 60:
        total = ceil(res / 20)
    else:
        pager = start.findAll("li", class_="pager__item")
        total = int(pager[-2].text)
    tasks = [
        get_one(base_url, f"{query}&page={i}", session) for i in range(1, total + 1)
    ]
    tasks_list = [tasks[i : i + 100] for i in range(0, len(tasks), 100)]
    artworks = list()
    for tasks in tasks_list:
        artworks_urls = await asyncio.gather(*tasks)
        artworks.append([url for urls in artworks_urls for url in urls])
    artworks = [artwork_url for data_list in artworks for artwork_url in data_list]
    return artworks


async def parse_data(url, session):
    soup = await get_page(url, session)
    data = {"Artwork URL": url}
    data.update({"Author": soup.find("h1", class_="gamma").text.strip()})
    data.update({"Title": soup.find("h2", class_="beta").text.strip()})
    try:
        data.update({"Date": soup.find("h2", class_="header__date").text.strip()})
    except AttributeError:
        data.update({"Date": "No Info Provided"})
    keys = [
        item.find("dt").text.strip()
        for item in soup.findAll("div", class_="tombstone__row")
    ]
    items = [
        item.find("dd").text.strip()
        for item in soup.findAll("div", class_="tombstone__row")
    ]
    general = dict(zip(keys, items))
    data.update({"Medium": general["Medium"]})
    data.update({"Dimensions": general["Dimensions"]})
    data.update({"Reference number": general["Reference"]})
    license_ = soup.find("figcaption").text.strip()
    if "Creative Commons" in license_:
        data.update({"License": "Creative Commons"})
    else:
        data.update({"License": "Restricted"})
    metadata = "".join(
        soup.find("article", class_="artwork")
        .find("script", {"type": "text/javascript"})
        .contents
    )
    image = re.findall(r"(https\S*10.jpg)", metadata)
    if len(image) == 0:
        image = re.findall(r"(https\S*9.jpg)", metadata)
        if len(image) == 0:
            image = re.findall(r"(https\S*8.jpg)", metadata)
    data.update({"Image URL": image[0]})
    try:
        entries = soup.find("div", class_="tabs__content")
        keys = [
            item.text.strip()
            for item in entries.findAll("h3", class_="tab-section__title")
        ]
        items = [
            item.text.strip()
            for item in entries.findAll("div", class_="tab-section__content")
        ]
        data.update(zip(keys, items))
    except AttributeError:
        try:
            artwork_text = soup.find("div", class_="artwork__text")
            title = artwork_text.h3.extract().text.strip()
            entry = artwork_text.text.strip()
            data.update({title: entry})
        except AttributeError:
            pass
    return data


async def Session(query, path):
    base_url = "https://www.tate.org.uk"
    timeout = ClientTimeout(total=600)
    async with ClientSession(
        timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
        # Pasring pages of search query
        logging.info("Getting urls of all artworks in the query")
        artworks_urls = await get_artwork_urls(base_url, query, session)
        logging.info("Done!")
        # Parsing artwork pages
        logging.info("Parsing Artworks Data")
        tasks = [parse_data(artwork_url, session) for artwork_url in artworks_urls]
        tasks_list = [tasks[i : i + 100] for i in range(0, len(tasks), 100)]
        data = list()
        for tasks in tasks_list:
            data.append(await asyncio.gather(*tasks))
        data = [artwork_data for data_list in data for artwork_data in data_list]
        logging.info("Done!")
        # Creating csv file
        logging.info("Saving to file")
        df = pandas.DataFrame(data)
        new_order = [
            "Reference number",
            "Title",
            "Author",
            "Date",
            "Medium",
            "Dimensions",
            "License",
            "Summary",
            "Artwork URL",
            "Img URL",
        ]
        cols = [col for col in new_order if col in df] + [
            col for col in df if col not in new_order
        ]
        df = df[cols]
        save_path = f"{path}/data.csv"
        df.to_csv(save_path)
        logging.info("Done!")
        # Downloading artwork images
        logging.info("Downloaing Images")
        titles = [data_set["Reference number"] for data_set in data]
        urls = [data_set["Image URL"] for data_set in data]
        download_data = tuple(zip(titles, urls))
        tasks = [
            get_image(url=tuple_[1], title=tuple_[0], path=path, session=session)
            for tuple_ in download_data
        ]
        await asyncio.gather(*tasks)


def main(url, path):
    logging.info("Starting scraping")
    asyncio.run(Session(url, path))
    logging.info("Done!")
