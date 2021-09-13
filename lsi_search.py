"""
Main script performing the actual search.

Positional arguments:
query - query to search across files

Optional arguments:
-d - directory to search
-r, --recursive - search subdirectories
"""

import argparse
from process import Query_Analyzer
import sys


def main():
    parser = setup_parser()
    args = get_args(parser)
    results = make_search(args)
    show_results(results)


def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='query to search across files')
    parser.add_argument('-d', help='directory to search')
    parser.add_argument(
        '-r', '--recursive', help='search subdirectories', action='store_true')
    return parser

def get_args(parser):
    args = parser.parse_args()
    if args.d == None:
        args.d = './'
    return args

def make_search(args):
    try:
        analyzer = Query_Analyzer(args.d, args.recursive)
        analyzer.analyze_query(args.query)
    except PermissionError:
        print(f'{args.d}: Permission denied')
        sys.exit(1)
    except FileNotFoundError:
        print(f'{args.d}: No such directory')
        sys.exit(1)
    
    return analyzer.get_matched_paths()
        
def show_results(results):
    for path in results:
        print(path)

if __name__ == '__main__':
    main()    