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


MTVN_EPISODE_DATA_URL = "https://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:episode:southpark.intl:{}&configtype=edge&ref={}"


def download_episode(ep_url: str):
    response = requests.get(ep_url)

    soup = BeautifulSoup(response.text, 'html.parser')

    dom = etree.HTML(str(soup))
    
    episode_data = json.loads(dom.xpath('/html/body/div[1]/main/div/div[1]/script')[0].text)
    
    cdn_episode_data = requests.get(MTVN_EPISODE_DATA_URL.format(episode_data['@id'], ep_url)).json()
    
    # The South Park video player splits the video into ad-seperated segments,
    # so we have to fetch all of them in order to have the whole episode.
    video_feed_ids = []
    for feed in cdn_episode_data['feed']['items']:
        video_feed_ids.append(feed['group']['category']['id'])

def download_season():
    pass
