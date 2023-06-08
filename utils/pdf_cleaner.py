import numpy as np
import pdfplumber
import pikepdf


def is_point_in_bbox(point, bbox):
    x, y = point
    x1, y1, x2, y2 = bbox
    return x1 <= x <= x2 and y1 <= y <= y2


def find_table_bbox_per_page(pdf_path: str) -> dict:
    tables_bboxes_per_page = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables_bboxes_per_page[page_index] = []
            for table in page.find_tables():
                tables_bboxes_per_page[page_index].append(table.bbox)
    return tables_bboxes_per_page


def clean_pdf(original_pdf_path: str, cleaned_pdf_path: str) -> None:
    tables_bboxes_per_page = find_table_bbox_per_page(original_pdf_path)

    with pikepdf.open(original_pdf_path, allow_overwriting_input=True) as pdf:
        height_per_page = {}

        bt_indexes_per_page = {}
        et_indexes_per_page = {}
        tm_points_per_page = {}
        tj_text_per_page = {}

        header_footer_threshold = int(len(pdf.pages) * 0.8)
        possible_header_footer_elements_per_page = {}

        indices_to_delete_per_page = {}

        # Parsing pdf pages
        for page in pdf.pages:
            height_per_page[page.index] = float(page.mediabox[3])

            bt_indexes_per_page[page.index] = []
            et_indexes_per_page[page.index] = []
            tm_points_per_page[page.index] = []
            tj_text_per_page[page.index] = []

            indices_to_delete_per_page[page.index] = set()

            # Get content stream
            content_stream = pikepdf.parse_content_stream(page)

            # Parse content stream
            bt_indexes_per_page[page.index] = [i for i, e in enumerate(content_stream) if str(e.operator) == "BT"]
            et_indexes_per_page[page.index] = [i for i, e in enumerate(content_stream) if str(e.operator) == "ET"]
            for bt, et in zip(bt_indexes_per_page[page.index], et_indexes_per_page[page.index]):
                for i in range(bt, et + 1):
                    if str(content_stream[i].operator) == 'Tm':
                        tm_points_per_page[page.index].append(
                            (float(content_stream[i].operands[4]), height_per_page[page.index] - float(content_stream[i].operands[5])))
                        break
                for i in range(bt, et + 1):
                    if str(content_stream[i].operator) == 'TJ':
                        tj_text_per_page[page.index].append(''.join([str(s) for i, s in enumerate(content_stream[i].operands[0]) if (i % 2) == 0]))
                        break

        # Detect elements of tables and schedule them for deletion
        for page_index in tables_bboxes_per_page:
            for table_bbox in tables_bboxes_per_page[page_index]:
                for i, point in enumerate(tm_points_per_page[page_index]):
                    if is_point_in_bbox(point, table_bbox):
                        for i_ in range(bt_indexes_per_page[page_index][i], et_indexes_per_page[page_index][i] + 1):
                            indices_to_delete_per_page[page_index].add(i_)

        # Detect possible header and footer element
        for page_index in bt_indexes_per_page:
            if len(tm_points_per_page[page_index]) == 0:
                continue
            top_point_index = np.argmin([p[1] for p in tm_points_per_page[page_index]])
            bottom_point_index = np.argmax([p[1] for p in tm_points_per_page[page_index]])

            possible_header_footer_elements_per_page[page_index] = []
            for index, (point, text) in enumerate(zip(tm_points_per_page[page_index], tj_text_per_page[page_index])):
                if point[1] <= tm_points_per_page[page_index][top_point_index][1] + (height_per_page[page_index] * 0.1):
                    possible_header_footer_elements_per_page[page_index].append({
                        'index': index,
                        'point': point,
                        'text': text
                    })
                if point[1] >= tm_points_per_page[page_index][bottom_point_index][1] - (height_per_page[page_index] * 0.1):
                    possible_header_footer_elements_per_page[page_index].append({
                        'index': index,
                        'point': point,
                        'text': text
                    })
        for page in possible_header_footer_elements_per_page:
            possibly_header_elements = possible_header_footer_elements_per_page[page]
            for element in possibly_header_elements:
                numer_of_matching_elements = 0
                for _page in possible_header_footer_elements_per_page:
                    if _page == page:
                        continue
                    for _element in possible_header_footer_elements_per_page[_page]:
                        if abs(element['point'][1] - _element['point'][1]) < 1 and (
                                element['text'] == _element['text'] or (element['text'].isnumeric() and _element['text'].isnumeric())):
                            numer_of_matching_elements += 1
                if numer_of_matching_elements > header_footer_threshold:
                    for i in range(bt_indexes_per_page[page][element['index']], et_indexes_per_page[page][element['index']] + 1):
                        indices_to_delete_per_page[page].add(i)

        # Delete elements
        for page in pdf.pages:
            # remove images
            for image in page.images:
                del page.Resources.XObject[image]

            # Get content stream
            content_stream = pikepdf.parse_content_stream(page)

            # remove stroke and fill and graphic elements
            for i in range(len(content_stream)):
                if str(content_stream[i].operator) in ['re', 'b', 'b*', 'B', 'B*', 'f', 'F', 's', 'S', 'n', 'f*', 'm', 'l', 'c', 'v', 'y', 'h', 'w',
                                                       'cs', 'J', 'j', 'M', 'd', 'ri', 'i', 'gs', 'Do', 'BDC']:
                    indices_to_delete_per_page[page.index].add(i)

            new_cs = []
            for i in range(len(content_stream)):
                if i not in indices_to_delete_per_page[page.index]:
                    new_cs.append(content_stream[i])
            new_cs = pikepdf.unparse_content_stream(new_cs)
            page.Contents = pdf.make_stream(new_cs)
        pdf.save(cleaned_pdf_path)
