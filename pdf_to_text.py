# Legal NLP
#
# pdf_to_text.py

import os
import argparse
from tqdm import tqdm
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pdfminer.pdfparser import PDFSyntaxError
import datetime
from utils import check_is_ascii


class UnicodeException(Exception):
    pass


class LengthException(Exception):
    pass


# convert pdf file to a string which has space among words
def convert_pdf_to_txt(fpath):
    rsc_mgr = PDFResourceManager()
    ret_str = StringIO()
    la_params = LAParams()
    device = TextConverter(rsc_mgr, ret_str, laparams=la_params)
    interpreter = PDFPageInterpreter(rsc_mgr, device)

    with open(fpath, 'rb') as fp:
        if len(list(PDFPage.get_pages(fp))) < 3:
            raise LengthException
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
    output_text = ret_str.getvalue()
    if not check_is_ascii(output_text):
        raise UnicodeException

    fp.close()
    device.close()
    ret_str.close()
    # breakpoint()
    return output_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_dir', default="./data/data/tar/bench=taphc/data", help='Path to pdf files directory', required=True)
    parser.add_argument('-o', '--output_dir', default="./data/text/bench=taphc/text", help='Path to output directory',)

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    c = 0
    print(datetime.datetime.now())
    output_f = "./data/conversion.csv"
    with open(output_f, 'w') as csv_file:

        for filename in tqdm(os.listdir(input_dir)):
            f = os.path.join(input_dir, filename)
            if not f.split('.')[-1] == 'pdf':
                print("{}, NOTPDF".format(f), file=csv_file)
                continue
            if not os.path.isfile(f):
                print("{}, NOTFILE".format(f), file=csv_file)
                continue
            if os.path.getsize(f) == 0:
                print("{}, ZEROSIZE".format(f), file=csv_file)
                continue

            try:
                new_path = os.path.join(output_dir, filename.replace(".pdf", ".txt"))
                try:
                    text = convert_pdf_to_txt(f)
                except UnicodeException:
                    print("{}, UnicodeDetected".format(f), file=csv_file)
                except LengthException:
                    print("{}, LessThan3Pages".format(f), file=csv_file)

                if text is not None:
                    with open(new_path, "w") as filz:
                        filz.write(text)
                    print("{}, CONVERTED".format(f), file=csv_file)
                    c += 1
                    if c == 5050:
                        break
                else:
                    print("{}, LessThan3Pages".format(f), file=csv_file)
            except PDFSyntaxError as e:
                print("{}, 0bytes".format(f), file=csv_file)

    print(datetime.datetime.now())


if __name__ == '__main__':
    main()
