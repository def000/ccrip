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
import m3u8
import youtube_dl
import subprocess
import os

from bs4 import BeautifulSoup
from lxml import etree
from dataclasses import dataclass


@dataclass
class Episode:
    id: str
    url: str
    title: str
    season: int
    episode: int


MTVN_EPISODE_DATA_URL = "https://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:episode:southpark.intl:{}&configtype=edge&ref={}"
MTVN_MASTER_FEED_DATA_URL = "https://media-utils.mtvnservices.com/services/MediaGenerator/{}?arcStage=staging&accountOverride=intl.mtvi.com&billingSection=intl&ep=90877963&format=json&acceptMethods=hls&tveprovider=null"


def download_episode(ep_url: str):
    response = requests.get(ep_url)

    soup = BeautifulSoup(response.text, 'html.parser')

    dom = etree.HTML(str(soup))
    
    episode_data = json.loads(dom.xpath('/html/body/div[1]/main/div/div[1]/script')[0].text)

    # Extract basic data
    episode = Episode(
        id=episode_data["@id"],
        url=episode_data["url"],
        title=episode_data["name"],
        season=episode_data["partOfSeason"]["seasonNumber"],
        episode=episode_data["episodeNumber"]
    )

    cdn_episode_data = requests.get(MTVN_EPISODE_DATA_URL.format(episode.id, episode.url)).json()
    
    # The South Park video player splits the video into ad-seperated segments,
    # so we have to fetch all of them in order to have the whole episode.
    video_feed_ids = []
    for feed in cdn_episode_data['feed']['items']:
        video_feed_ids.append(feed['group']['category']['id'])

    # Download all segments
    segment_number = 1
    downloaded_segments = []
    for video_feed_id in video_feed_ids:
        master_feed_data = requests.get(MTVN_MASTER_FEED_DATA_URL.format(video_feed_id)).json()

        # Retrieve m3u8 feed
        feed_src_m3u = master_feed_data["package"]["video"]["item"][0]["rendition"][0]["src"]

        # Choose VTT subtitles
        subtitle_paths = master_feed_data["package"]["video"]["item"][0]["transcript"][0]["typographic"]

        subtitle_path = ""
        for sub in subtitle_paths:
            if sub["format"] == "vtt":
                subtitle_path = sub["src"]
                break

        playlists = m3u8.load(feed_src_m3u)

        # a junky way to find the best quality
        # Normally we'd use max() here but then there would be no way to track the URI
        # (well, there *is* a way, but this one is cleaner...)
        highest_resolution = 0

        feed_source = ""

        for playlist in playlists.playlists:

            feed_resolution = playlist.stream_info.resolution[0]

            if feed_resolution > highest_resolution:

                highest_resolution = feed_resolution

                feed_source = playlist.absolute_uri
        
        # Download segment
        with youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': f'{segment_number}.mp4'
        }) as ydl:
            # There is most likely a better way to do all this, but it works

            info = ydl.extract_info(feed_source)
            
            # We download to .mp4 because it is set so automatically, but we delete it afterwards
            temporary_filename = ydl.prepare_filename(info)
            subtitle_filename = f"{segment_number}.vtt"
            
            ydl.download([feed_source])

            # Download .vtt subtitles
            with open(subtitle_filename, "w") as f:
                f.write(requests.get(subtitle_path).text)

            # Attach subtitles and convert to mkv
            subprocess.call(f"ffmpeg -i {temporary_filename} -i {subtitle_filename} -map 0:v -map 0:a -map 1 -metadata:s:s:0 language=eng -c:v copy -c:a copy -c:s srt {segment_number}.mkv", shell=True)

            # Remove temporary .mp4 and subtitle file
            os.remove(temporary_filename)
            os.remove(subtitle_filename)

            downloaded_segments.append(f"{segment_number}.mkv")

            segment_number += 1
    
    with open("input.txt", "w") as f:
        for segment in downloaded_segments:
            f.write(f'file {segment}\n')

    # Stitch all .mkv files together
    ffmp_str = f"ffmpeg -f concat -i input.txt -codec copy \"S{episode.season}E{episode.episode} - {episode.title}.mkv\""
    subprocess.call(ffmp_str, shell=True)

    # cleanup
    os.remove("input.txt")
    for segment in downloaded_segments:
        os.remove(segment)


def download_season():
    pass
