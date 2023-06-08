import os

import requests
from bs4 import BeautifulSoup

from utils import fs_utils

GROBID_URL = 'https://kermitt2-grobid.hf.space/api/processFulltextDocument'


def extract_text_from_pdf(cleaned_pdf_path: str, debug: bool = False) -> None:
    folder_path = os.path.dirname(cleaned_pdf_path)

    # Delete old files
    files_to_delete = fs_utils.filter_files_in_folder(folder_path, ['debug.xml', 'chapters.json', '.txt'])
    fs_utils.delete_files(files_to_delete)

    with open(cleaned_pdf_path, 'rb') as cleaned_pdf_file:
        tei_xml = requests.post(GROBID_URL, files={'input': cleaned_pdf_file}).text
        soup = BeautifulSoup(tei_xml, features='xml')

        chapters = []
        for sec in soup.select('div:has(head):has(p)'):
            heading = sec.select_one('head').text
            paragraphs = []
            for p in sec.select('p'):
                paragraphs.append(p.text)
            chapters.append({
                'heading': heading,
                'paragraphs': paragraphs
            })

        if debug:
            # Save xml
            xml_path = os.path.join(folder_path, 'debug.xml')
            fs_utils.write_file(xml_path, tei_xml)
            # Save chapters
            chapters_path = os.path.join(folder_path, 'chapters.json')
            fs_utils.save_json_file(chapters_path, chapters)

        for index, chapter in enumerate(chapters):
            chapter_text = chapter['heading'] + '\n\n'
            for p in chapter['paragraphs']:
                chapter_text += p + '\n'

            chapter_path = os.path.join(folder_path, f'chapter_{index}.txt')
            fs_utils.write_file(chapter_path, chapter_text)
