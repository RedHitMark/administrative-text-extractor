import json
import os
from typing import List


MANUAL_CRAWLED_FOLDER = os.path.join('manual_crawled')

OUTPUT_FOLDER = os.path.join('output')

CRAWLING_RESULTS_FOLDER = os.path.join(OUTPUT_FOLDER, 'crawling_results')
METADATA_FOLDER = os.path.join(OUTPUT_FOLDER, 'metadata')
DOCUMENTS_FOLDER = os.path.join(OUTPUT_FOLDER, 'documents')


def file_exists(path: str) -> bool:
    return os.path.exists(path)


def create_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def delete_files(files: List[str]) -> None:
    for file in files:
        os.remove(file)


def read_json(path: str) -> any:
    with open(file=path, mode='r', encoding='utf8') as file:
        return json.load(file)


def save_json_file(path: str, data: any) -> None:
    with open(file=path, mode='w', encoding='utf8') as file:
        json.dump(data, file, indent=4)


def write_file(path: str, data: str) -> None:
    with open(file=path, mode='w', encoding='utf8') as file:
        file.write(data)


def filter_files_in_folder(folder_path: str, extensions: List[str]) -> List[str]:
    filtered_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(tuple(extensions)):
                filtered_files.append(os.path.join(root, file))
    return filtered_files