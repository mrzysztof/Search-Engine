"""
Script used to gather text files for tests.

Positional arguments:
n - number of articles to gather

Optional arguments:
-d - destination directory
-h, --help
"""

import argparse
import sys
import wikipediaapi

def main():
    n_articles, dest_dir = get_args()
    Crawler(n_articles, dest_dir)
    
def get_args():
    parser = setup_parser()
    args = parser.parse_args()

    n_articles = get_number(args)
    dest_dir = args.d
    return n_articles, dest_dir

def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('n', help='number of articles to gather')
    parser.add_argument('-d', help='destination directory')
    return parser

def get_number(args):
    n_articles = int(args.n)
    if n_articles < 0:
        print('Number of articles has to be a positive number.')
        sys.exit(1)
    return n_articles


class Crawler:
    def __init__(self, n_articles, dest_dir):
        self.articles = set()
        self.n_articles = n_articles
        if dest_dir == None:
            self.dest_dir = '.'
        else: self.dest_dir = dest_dir

        wiki = wikipediaapi.Wikipedia(
            'en', extract_format=wikipediaapi.ExtractFormat.WIKI)
        init_page = wiki.page('Category:Philosophy')
        #level determining the depth of crawling from the initial page
        self.max_level = 2
        #mapping used to remove forbidden characters from filename
        self.filename_trans = {ord(char):'' for char in '\/:*?"<>|'}

        self.crawl(init_page.categorymembers)

    def crawl(self, page, level=0):
        for subpage in page.values():
            if (subpage.ns == wikipediaapi.Namespace.CATEGORY 
                and level < self.max_level):
                self.crawl(subpage.categorymembers, level=level + 1)
            elif self.is_unique_article(subpage):
                    self.get_article(subpage)
                    self.show_progress()
                    if len(self.articles) == self.n_articles:
                        sys.exit(0)
    
    def is_unique_article(self, page):
        return (
            #page is actually an article
            page.ns == wikipediaapi.Namespace.MAIN
            and not page.title in self.articles
            )

    def get_article(self, page):
        self.articles.add(page.title)
        path = self.make_path(page)
        try:     
            with open(path, 'w', encoding='UTF-8') as output:
                output.write(page.text)
        except FileNotFoundError:
            print('Could not find the provided directory.')
            sys.exit(1)
        except PermissionError:
            print('Could not save to the provided directory.')
            sys.exit(1)

    def make_path(self, page):
        arc_title = page.title.translate(self.filename_trans)
        path = self.dest_dir + '/' + arc_title + '.txt'
        return path

    def show_progress(self):
        print(f'Downloaded {len(self.articles)}/{self.n_articles}.', end='\r')

if __name__ == '__main__':
    main()