# Legal NLP
#
# utils.py


import re
import fitz
from spellchecker import SpellChecker
from collections import Counter

spell = SpellChecker(language="en")
from file_utils import read_file, read_file_lines


def check_is_ascii(text):
    """
    Checks if input string contains only ASCII characters or not
    :param text: Input text
    :return: True if text contains only ASCII else False
    """
    return text.isascii()


def is_pdf_scanned(fpath):
    """
    Checks if the document is a pdf scanned or not using text and image bounding boxes
    True digital documents have more text than Scanned documents
    :param fpath: Document to check
    :return:
    """
    doc = fitz.open(fpath)
    report = []

    for i in range(len(doc)):
        page = doc[i]
        page_area = page.rect.width * page.rect.height
        text = page.get_text().strip()
        images = page.get_images(full=True)

        # Calculate area covered by images
        image_area_sum = 0
        for img in page.get_image_info():
            bbox = img['bbox']
            image_area_sum += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

        is_searchable = len(text) > 0
        is_image_heavy = image_area_sum > (page_area * 0.8)

        if is_searchable and is_image_heavy:
            status = "Scanned with OCR Layer"
        elif is_searchable and not is_image_heavy:
            status = "True Digital"
        elif not is_searchable and len(images) > 0:
            status = "Raw Scan (No OCR)"
        else:
            status = "Empty or Vector Graphics Only"

        report.append(f"Page {i + 1}: {status}")

    doc.close()
    return report


def list_misspelled_words(text):
    """
    Return a sorted list of unique misspelled words found in the text.
    :param text: Input text
    :return: List of unique misspelled words
    """
    words = re.findall(r"[A-Za-z']+", text)
    words_lower = [w.lower() for w in words]
    misspelled = spell.unknown(set(words_lower))
    return sorted(misspelled)


def list_misspelled_words_with_counts(text):
    """
    Return a frequency distribution of misspelled words
    :param text: Input text
    :return: freq dist of (misspelled_word, count_in_text) sorted by count in desc
    """
    words = re.findall(r"[A-Za-z']+", text)
    words_lower = [w.lower() for w in words]
    counts = Counter(words_lower)
    misspelled = spell.unknown(counts.keys())

    return sorted(
        [(w, counts[w]) for w in misspelled],
        key=lambda x: x[1],
        reverse=True,
    )


def add_words_to_spell_checker(word_list):
    """
    Adds words to spell checker
    :param word_list: Roman script of words to add
    :return:
    """
    spell.word_frequency.load_words(word_list)


def test_scanned_pdf():
    """
    ['Page 1: Scanned with OCR Layer', 'Page 2: Scanned with OCR Layer', 'Page 3: Scanned with OCR Layer', 'Page 4: Scanned with OCR Layer', 'Page 5: Scanned with OCR Layer', 'Page 6: Scanned with OCR Layer', 'Page 7: Scanned with OCR Layer', 'Page 8: Scanned with OCR Layer', 'Page 9: Scanned with OCR Layer', 'Page 10: Scanned with OCR Layer', 'Page 11: Scanned with OCR Layer']
    ['Page 1: True Digital', 'Page 2: True Digital', 'Page 3: True Digital', 'Page 4: True Digital']
    ['Page 1: True Digital', 'Page 2: True Digital', 'Page 3: True Digital', 'Page 4: True Digital']
    """
    test_file1 = "./data/bench=taphc/data/HBHC010000012024_1_2025-04-15.pdf"
    test_file2 = "./data/bench=taphc/data/HBHC010000022025_1_2025-01-22.pdf"
    test_file3 = "./data/bench=hcaurdb/data/HCBM030000012025_1_2025-02-04.pdf"
    print(is_pdf_scanned(test_file1))
    print(is_pdf_scanned(test_file2))
    print(is_pdf_scanned(test_file3))


def test_spellings():
    """
    ['additionat', 'addrttonat', 'bandlaguda', 'barkas', 'bnss', "c'", 'cc', 'ccs', 'chandrayangutta', 'chiei', 'copyii', 'crlp', 'cum', 'dismlssing', 'famity', 'fetb', 'hanumantha', 'hari', 'honourable', "i'", 'iii', 'ingly', 'itl', 'jubitee', 'juose', 'laneous', 'll', 'lrfan', 'lsr', 'mahmood', 'miscel', 'occ', 'onat', 'optjc', 'petitioneryaccused', 'prasad', 'rao', 'respon', 'rl', 'sd', 'sho', 'sio', 'smt', 'sujana', 'telangana', 'tetangana', 'tion', 'xxilt', "yi'"]

    ['anr', 'app', 'arun', 'baburaon', 'bhc', 'coram', 'cri', 'deore', 'deshmukh', 'facie', 'gangakhed', 'gangakhedkar', 'hereinabove', 'ii', 'iii', 'karnani', 'lotan', 'mahesh', 'nos', 'offences', 'pandurang', 'parbhani', 'pedneker', 'prakash', 'purushottam', 'santosh', 'shailendra', 'shirse', 'tak', 'tauseef', 'vithal']
    """
    test_file1 = "./data/bench=taphc/text/HBHC010000032025_1_2025-01-10.txt"  # Flagged as scanned file
    test_file2 = "./data/bench=hcaurdb/text/HCBM030000012025_1_2025-02-04.txt"  # True digital file

    print(list_misspelled_words(read_file(test_file1)))
    print(list_misspelled_words(read_file(test_file2)))


def test_spellings_with_count():
    """
    [('telangana', 3), ('hanumantha', 2), ('sujana', 2), ('honourable', 2), ('cum', 2), ('chandrayangutta', 2), ('rao', 2), ('smt', 2), ('bnss', 1), ('sho', 1), ("i'", 1), ('sd', 1), ('respon', 1), ('laneous', 1), ('tion', 1), ('ll', 1), ('petitioneryaccused', 1), ('ingly', 1), ('xxilt', 1), ('lrfan', 1), ('jubitee', 1), ('crlp', 1), ('tetangana', 1), ('ccs', 1), ('hari', 1), ('juose', 1), ('barkas', 1), ('fetb', 1), ('itl', 1), ("yi'", 1), ('sio', 1), ('onat', 1), ("c'", 1), ('bandlaguda', 1), ('occ', 1), ('additionat', 1), ('chiei', 1), ('mahmood', 1), ('optjc', 1), ('rl', 1), ('copyii', 1), ('cc', 1), ('dismlssing', 1), ('addrttonat', 1), ('miscel', 1), ('lsr', 1), ('prasad', 1), ('iii', 1), ('famity', 1)]

    [('tauseef', 4), ('app', 4), ('offences', 2), ('nos', 2), ('gangakhed', 2), ('pedneker', 2), ('parbhani', 2), ('arun', 2), ('deore', 1), ('coram', 1), ('purushottam', 1), ('tak', 1), ('prakash', 1), ('facie', 1), ('shailendra', 1), ('anr', 1), ('cri', 1), ('bhc', 1), ('hereinabove', 1), ('ii', 1), ('shirse', 1), ('pandurang', 1), ('deshmukh', 1), ('santosh', 1), ('karnani', 1), ('lotan', 1), ('mahesh', 1), ('iii', 1), ('vithal', 1), ('baburaon', 1), ('gangakhedkar', 1)]

    [('chandrayangutta', 2), ('barkas', 1), ('respon', 1), ('iii', 1), ('bandlaguda', 1), ('onat', 1), ('ccs', 1), ('addrttonat', 1), ('tion', 1), ('lrfan', 1), ('occ', 1), ('lsr', 1), ('juose', 1), ("c'", 1), ('ll', 1), ('ingly', 1), ('crlp', 1), ('fetb', 1), ('chiei', 1), ("i'", 1), ("yi'", 1), ('miscel', 1), ('bnss', 1), ('tetangana', 1), ('mahmood', 1), ('optjc', 1), ('dismlssing', 1), ('jubitee', 1), ('sio', 1), ('additionat', 1), ('xxilt', 1), ('famity', 1), ('petitioneryaccused', 1), ('itl', 1), ('laneous', 1), ('cc', 1), ('copyii', 1), ('sho', 1)]

    [('app', 4), ('pedneker', 2), ('nos', 2), ('offences', 2), ('gangakhed', 2), ('shirse', 1), ('iii', 1), ('tak', 1), ('karnani', 1), ('baburaon', 1), ('deore', 1), ('coram', 1), ('cri', 1), ('gangakhedkar', 1), ('anr', 1), ('facie', 1), ('hereinabove', 1), ('bhc', 1), ('ii', 1)]

    [('copyii', 1), ('laneous', 1), ('sho', 1), ("c'", 1), ('jubitee', 1), ('tetangana', 1), ('dismlssing', 1), ('optjc', 1), ('fetb', 1), ('crlp', 1), ("i'", 1), ('sio', 1), ("yi'", 1), ('iii', 1), ('xxilt', 1), ('additionat', 1), ('itl', 1), ('juose', 1), ('occ', 1), ('ccs', 1), ('miscel', 1), ('lrfan', 1), ('petitioneryaccused', 1), ('ll', 1), ('mahmood', 1), ('bnss', 1), ('addrttonat', 1), ('cc', 1), ('lsr', 1), ('famity', 1), ('ingly', 1), ('respon', 1), ('onat', 1), ('chiei', 1), ('tion', 1)]

    [('app', 4), ('pedneker', 2), ('gangakhed', 2), ('nos', 2), ('offences', 2), ('tak', 1), ('hereinabove', 1), ('cri', 1), ('deore', 1), ('bhc', 1), ('anr', 1), ('baburaon', 1), ('iii', 1), ('karnani', 1), ('gangakhedkar', 1), ('coram', 1), ('facie', 1), ('shirse', 1), ('ii', 1)]
    """
    test_file1 = "./data/bench=taphc/text/HBHC010000032025_1_2025-01-10.txt"  # Flagged as scanned file
    test_file2 = "./data/bench=hcaurdb/text/HCBM030000012025_1_2025-02-04.txt"  # True digital file

    print(list_misspelled_words_with_counts(read_file(test_file1)))
    print(list_misspelled_words_with_counts(read_file(test_file2)))


def main():
    # Test pdf scanned
    # test_scanned_pdf()

    # Test spellings
    # test_spellings()

    # Test adding words to checker
    add_words_list = read_file_lines('./data/regions.txt') + read_file_lines('./data/name_list.txt')
    add_words_list = [item.lower().strip() for item in add_words_list]
    add_words_to_spell_checker(add_words_list)
    
    test_spellings_with_count()


if __name__ == "__main__":
    main()
