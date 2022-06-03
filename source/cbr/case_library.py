from lxml import etree

from definitions import CASE_BASE


class CaseLibrary:

    def __init__(self):
        self.tree = etree.parse(CASE_BASE)


if __name__ == '__main__':
    cl = CaseLibrary()
