import re


def execution_function(encoding, keywords_filename, text_filename):
    """
    made for initialization of parameters values

    :param encoding: is the type of the decryption needed to open the file of the text (the text which
           we are looking for patterns in).
    :param keywords_filename: is the filename from which we read the keywords.
    :param text_filename: is the filename from which we read the whole text (the text which we are
           looking for patterns in)
    :return: void
    """
    encoding[0] = "utf-8"
    keywords_filename[0] = "keywords.txt"
    text_filename[0] = "text.txt"


def read_key_words(filename):
    keywords = set()
    try:
        f_key_words = open(filename, "r")
        for keyword in f_key_words:
            keywords.add(keyword.replace("\n", ""))
        f_key_words.close()
    except Exception as e:
        print(str(e))
    finally:
        return keywords


def read_text(text_filename, text, encoding):
    """Read from config file the relevant parameters according to configuration file format"""
    try:
        f_text = open(text_filename[0], "r", encoding=encoding[0])
        text[0] = f_text.read()
        f_text.close()
    except Exception as e:
        print(str(e))


class Patterns_Finder:
    def __init__(self, keywords_filename, text):
        self.keywords = read_key_words(keywords_filename)
        self.text = text

    def find_patterns(self):
        output_list = []
        for keyword in self.keywords:
            # The r means that the string is to be treated as a raw string, which means all escape codes
            # will be ignored.
            # escape(string): Return string with all non-alphanumerics backslashed;
            # re.sub(r'(?:\\[ -])+', r'[\\s-]*' - replaces \[ -]+ with the expression [\\s-]* which mean that any
            # kind of space can be there 0 or more times.
            # (?<!\w) - doesn't exists any alphanumeric character before
            # (?!\w) - doesn't exists any alphanumeric character afterwards
            # re.I - perform case-insensitive matching
            if re.search(r"(?<!\w)" + re.sub(r'(?:\\[ -])+', r'[\\s-]*', re.escape(keyword)) + r"(?!\w)",
                         self.text, re.I) and keyword not in output_list:
                output_list.append(keyword)
        return output_list


def main():
    keywords_filename = [""]
    text_filename = [""]
    text = [""]
    encoding = [""]
    execution_function(encoding, keywords_filename, text_filename)
    read_text(text_filename, text, encoding)
    finder = Patterns_Finder(keywords_filename[0], text[0])
    print(finder.find_patterns())


if __name__ == "__main__":
    main()
