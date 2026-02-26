# Legal NLP
#
# file_utils.py

import datetime
import filecmp
import os


def read_dir(path):
    """
    Directory listing
    :param path:
    :return:
    """
    print(path)
    return os.listdir(path)


def read_file_first_line(path):
    """
    Read only the first line of every file
    :param path:
    :return:
    """
    with open(path) as f:
        return f.readline().strip('\n')


def read_file(fpath):
    """
    :param fpath: path to the file
    :return: contents of entire file
    """
    if os.path.exists(fpath) and os.path.isfile(fpath) and fpath.split('.')[-1] == 'txt':
        with open(fpath, "r") as f:
            text = f.read()
        return text
    raise FileExistsError


def read_file_lines(file):
    """
    :param file: path to the file
    :return: contents of the file by line
    """
    if os.path.exists(file):
        with open(file, 'r') as f:
            text = f.readlines()
        return text
    return ""


def cmp_files(file1, file2):
    """
    Needed to access if two of the case files are the same or not
    :param file1: source file
    :param file2: target file
    :return:
    """
    return filecmp.cmp(file2, file1)


def file_set_diff(file1, file2):
    """
    Get the set of lines in the two cases are that different
    :param file1:
    :param file2:
    :return:
    """
    f1 = set(read_file_lines(file1))
    f2 = set(read_file_lines(file2))
    diff = f1.difference(f2)
    return len(diff)


def main():
    pass


if __name__ == "__main__":
    main()
