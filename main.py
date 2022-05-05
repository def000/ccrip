"""
    Rip South Park episodes in highest quality from official website
    Copyright (C) 2022  Def

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import json

from bs4 import BeautifulSoup
from lxml import etree


def download_episode(ep_url: str):
    response = requests.get(ep_url)

    soup = BeautifulSoup(response.text, 'html.parser')

    dom = etree.HTML(str(soup))
    
    episode_data = json.loads(dom.xpath('/html/body/div[1]/main/div/div[1]/script')[0].text)


def download_season():
    pass
