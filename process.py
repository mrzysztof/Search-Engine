from os import write
import numpy as np
import unidecode
from preprocess import TBD_Matrix, prepare_term

class Query_Analyzer:
    def __init__(self, dir, recursive):
        self.dir = dir
        self.recursive = recursive
        self.tbd_matrix = TBD_Matrix(dir, recursive)
        self.n_files = self.tbd_matrix.n_files
        self.files_indices = np.array([])

    def analyze_query(self, query):
        self.files_indices = np.array([])
        q_bow = self.query_to_bow(query)
        q_norm = np.linalg.norm(q_bow[0])

        if not np.isclose(q_norm, 0.):
            files_score = (q_bow @ self.tbd_matrix.matrix)
            self.files_indices = np.argsort(files_score).flatten()[::-1]
            self.files_indices = [idx for idx in self.files_indices 
                                  if files_score[0, idx] > 0]

    def query_to_bow(self, query):
        terms = self.tokenize_query(query)
        n_terms = len(self.tbd_matrix.term_index)
        q = np.zeros((1, n_terms), dtype=np.single)
        for term in terms:
            if term in self.tbd_matrix.term_index:
                q[0, self.tbd_matrix.term_index[term]] += 1
        return q

    def tokenize_query(self, query):
        buff = unidecode.unidecode(query)
        terms = [prepare_term(term) for term in buff.split()]
        return terms

    def pop_most_accurate(self, k=10):
        k = min(len(self.files_indices), k)
        filenames = [self.tbd_matrix.filenames[idx] for idx in self.files_indices[:k]]
        self.files_indices = self.files_indices[k:]
        return filenames

    def get_matched_paths(self):
        filenames = [self.tbd_matrix.filenames[idx] for idx in self.files_indices]
        paths = [self.tbd_matrix.filepaths[filename] for filename in filenames]
        return paths
