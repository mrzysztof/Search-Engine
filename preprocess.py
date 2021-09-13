"""
Module used to construct term-by-document matrix 
and denoise it using SVD.
"""

import os
import unidecode
import numpy as np
from scipy import sparse
from nltk.corpus import stopwords
from binaryornot.check import is_binary

term_translation = {ord(char):'' for char in ':.,()";'}
stops = set(stopwords.words('english'))

def tokenize(entry):
    buff = ''
    with open(entry.path, 'r', encoding='utf-8') as file:
        buff = unidecode.unidecode(file.read())
    terms = buff.split()
    return terms      

def prepare_term(term):
    term = term.translate(term_translation)
    return term.lower()
    
def map_browsedir(dir, func, recursive):
    for entry in os.scandir(dir):
        try:
            if entry.is_dir() and recursive:
                map_browsedir(entry.path, func, recursive)
            elif entry.is_file() and not is_binary(entry.path):
                func(entry)
        except (PermissionError, FileNotFoundError):
            """
            ignore files for which user has no permissions
            or could be deleted during execution of this function
            """
            pass


class TBD_Matrix:
    def __init__(self, dir, recursive):
        self.dir = dir
        self.recursive = recursive
        self.n_files = 0
        #bag of words represented as dict {term:number of files containing it}
        self.bow = {}
        #dictionary mapping each term to its index in tbd_matrix
        self.term_index = {}
        self.filenames = []
        self.filepaths = {}
        self.matrix = None
        self.norms = None

        self.make_bow()
        self.make_matrix()
        self.bow.clear()

    def make_bow(self):
        map_browsedir(self.dir, self.update_bow, self.recursive)
    
    def make_matrix(self):
        n_terms = len(self.bow)
        self.matrix = np.zeros((n_terms, self.n_files))
        self.term_index = {key:i for i, key in enumerate(self.bow.keys())}

        map_browsedir(self.dir, self.update_matrix, self.recursive)
        self.calc_idf()
        self.normalize_matrix()
        self.svd()
        
    def update_bow(self, entry):
        self.n_files += 1
        terms = tokenize(entry)
        article_wordset = set()

        for term in terms:
            keyword = prepare_term(term)
            if (not keyword in stops and 
                not keyword in article_wordset):
                    article_wordset.add(keyword)
                    if keyword in self.bow:
                        self.bow[keyword] += 1
                    else: self.bow[keyword] = 1 

    def update_matrix(self, entry):
        self.filenames.append(entry.name)
        self.filepaths[entry.name] = entry.path
        terms = tokenize(entry)
        column = len(self.filenames) - 1

        for term in terms:
            keyword = prepare_term(term)
            if keyword in self.term_index:
                idx = self.term_index[keyword]
                self.matrix[idx, column] += 1

    def calc_idf(self):
        unique_occurrs = np.array(list(self.bow.values()), dtype=float)
        #vector of idf values for each term
        idfs = np.log(self.n_files * np.reciprocal(unique_occurrs))
        for row, idf in enumerate(idfs):
            self.matrix[row, :] *= idf

    def normalize_matrix(self):
        self.norms = np.zeros((1, self.n_files))
        for col in range(self.n_files):
            col_norm = np.linalg.norm(self.matrix[:, col])
            self.norms[:, col] = col_norm
            if col_norm != 0:
                self.matrix[:, col] /= col_norm

    def svd(self):
        k = int(0.9*self.n_files)
        self.matrix = sparse.csc_matrix(self.matrix)

        U_k, S_k, V_k = sparse.linalg.svds(self.matrix, k=k)
        S_k = S_k * np.eye(k)
        self.matrix = U_k @ S_k @ V_k