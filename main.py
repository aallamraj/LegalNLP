# Legal NLP
#
# main.py
import argparse
import os
import csv
import re
from utils import list_misspelled_words_with_counts, is_pdf_scanned, add_words_to_spell_checker
from file_utils import read_file, read_file_lines


def check_pdfs(dpath):
    pdf_summary_file = './data/pdf_summary.csv'
    with open(pdf_summary_file, 'a') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['File', 'Type'])
        i = 0
        for filename in os.listdir(dpath):
            f = os.path.join(dpath, filename)
            flist = is_pdf_scanned(f)
            r = re.compile(".*OCR")
            ocr_list = list(filter(r.match, flist))
            if ocr_list:
                csv_writer.writerow([f, "SCANNED"])
            else:
                csv_writer.writerow([f, "TRUE DIGITAL"])
            i += 1
            if i == 5050:
                break


def check_misspellings(dpath):
    print(dpath)
    add_words_list = read_file_lines('./data/regions.txt') + read_file_lines('./data/name_list.txt')
    add_words_list = [item.lower().strip() for item in add_words_list]
    add_words_to_spell_checker(add_words_list)

    spelling_summary_file = './data/spelling_summary.csv'
    with open(spelling_summary_file, 'a') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['File', 'WordCount', 'MisCount', 'Percent'])
        for filename in os.listdir(dpath):
            f = os.path.join(dpath, filename)
            file_text = read_file(f)
            flist = list_misspelled_words_with_counts(file_text)
            wc = len(file_text.split())
            mc = len(flist)
            csv_writer.writerow([filename, wc, mc, mc/wc*100])


def main():
    parser = argparse.ArgumentParser()

    # ./data/bench=taphc/text ./data/bench=hcaurdb/text ./data/bench=hcaurdb/data
    parser.add_argument('-i', '--input_dir', default="./data/bench=taphc/text", help='Path files directory')

    args = parser.parse_args()
    input_dir = args.input_dir

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"{input_dir} does not exist")

    if input_dir.split("/")[-1] == "data":
        check_pdfs(input_dir)
    elif input_dir.split("/")[-1] == "text":
        check_misspellings(input_dir)
    else:
        raise FileNotFoundError(f"{input_dir} does not contain data or text path")


if __name__ == '__main__':
    main()