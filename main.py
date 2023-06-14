import os
import shutil

from utils import fs_utils, pdf_cleaner, pdf_text_extractor

INPUT_FOLDER = os.path.join('input')
OUTPUT_FOLDER = os.path.join('output')


if __name__ == '__main__':
    # Create output folder and copy raw files into it
    fs_utils.create_folder(OUTPUT_FOLDER)
    input_raw_files = fs_utils.filter_files_in_folder(INPUT_FOLDER, ['raw.pdf', '.xlsx'])
    for input_raw_file in input_raw_files:
        output_raw_file = input_raw_file.replace(INPUT_FOLDER, OUTPUT_FOLDER)
        fs_utils.create_folder(os.path.dirname(output_raw_file))
        shutil.copy2(input_raw_file, output_raw_file)

    # Clean raw files in output folder
    raw_files = fs_utils.filter_files_in_folder(OUTPUT_FOLDER, ['raw.pdf'])
    for raw_file in raw_files:
        print(f'Cleaning {raw_file}...')
        cleand_file = raw_file.replace('raw.pdf', 'cleaned.pdf')
        pdf_cleaner.clean_pdf(raw_file, cleand_file, force=False)

    # Extract text from cleaned file
    cleand_files = fs_utils.filter_files_in_folder(OUTPUT_FOLDER, ['cleaned.pdf'])
    for cleand_file in cleand_files:
        print(f'Extracting {cleand_file}...')
        pdf_text_extractor.extract_text_from_pdf(cleand_file, force=False, debug=False)




