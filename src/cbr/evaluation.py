import os
import shutil

import numpy as np


# This script is going to have different functions to do the evaluation in the CBR
def get_jaccard_simmilarity(list1, list2):
    """
    Compute the jaccard index between two sets

    Input: Two set of list
    output: Jaccard metric
    """

    set1, set2 = set(list1), set(list2)
    n = len(set.intersection(set2))
    jaccard_metric = n / float(len(set1) + len(set2) - n)

    return jaccard_metric


# Fucntion to evaluate the similarity between all the cases in the case_library with the new solution
# and return the score similarity and the case that has the highest similarity with the new solution
def evaluate_similarity_with_case_library(root: ET.Element, case_library: list) -> tuple:
    # Get the adapted solution
    adapted_solution = root.find("adaptedSolution").text
    # Get the original solution
    original_solution = root.find("originalSolution").text
    # Get the similarity between the two solutions
    similarity = get_jaccard_simmilarity(adapted_solution, original_solution)
    # Get the case that has the highest similarity with the new solution
    case_with_highest_similarity = get_case_with_highest_similarity(adapted_solution, case_library)
    return similarity, case_with_highest_similarity


# Function yo get case with highest similarity with the new solution
def get_case_with_highest_similarity(adapted_solution, case_library):
    # Get the similarity between the two solutions
    similarity = get_jaccard_simmilarity(adapted_solution, case_library)
    # Get the case that has the highest similarity with the new solution
    case_with_highest_similarity = case_library[similarity.index(max(similarity))]
    return case_with_highest_similarity


def get_pearson_corr_metric(item1, item2, mean1, mean2):
    """
    Compute the pearson correlation between two items

    Input: Two items and their mean
    output: Pearson correlation metric
    """

    pearson_corr_metric = np.corrcoef(item1, item2)[0, 1]
    num = sum((item1 - mean1) * (item2 - mean2))
    den = np.sqrt(sum((item1 - mean1))) * np.sqrt(sum((item2 - mean2)))
    p_corr_metric = num / den

    return pearson_corr_metric, p_corr_metric if den != 0 else 0


# evaluate the adapted solution using the ConstraintsBuildeR
def evaluate_adapted_solution(root: ET.Element) -> float:
    # Get the adapted solution
    adapted_solution = root.find("adaptedSolution").text
    return float(adapted_solution)


# Evaluate similarity between two solutions using the ConstraintsBuilder
def evaluate_similarity(root: ET.Element) -> float:
    # Get the adapted solution
    adapted_solution = root.find("adaptedSolution").text
    # Get the original solution
    original_solution = root.find("originalSolution").text
    # Get the similarity between the two solutions
    similarity = get_jaccard_simmilarity(adapted_solution, original_solution)
    return similarity


# Create a class that implements the evaluation of the solution

class Evaluation:
    def __init__(self, root: ET.Element):
        self.root = root
        self.adapted_solution = root.find("adaptedSolution").text
        self.original_solution = root.find("originalSolution").text
        self.similarity = get_jaccard_simmilarity(self.adapted_solution, self.original_solution)
        self.pearson_corr_metric, self.p_corr_metric = get_pearson_corr_metric(
            self.adapted_solution,
            self.original_solution,
            np.mean(self.adapted_solution),
            np.mean(self.original_solution),
        )
        self.adapted_solution_score = float(root.find("adaptedSolutionScore").text)
        self.original_solution_score = float(root.find("originalSolutionScore").text)
        self.adapted_solution_score_diff = self.adapted_solution_score - self.original_solution_score
        self.similarity_diff = self.similarity - self.original_solution_score
        self.pearson_corr_metric_diff = self.pearson_corr_metric - self.original_solution_score
        self.p_corr_metric_diff = self.p_corr_metric - self.original_solution_score

    def get_adapted_solution(self):
        return self.adapted_solution

    def get_original_solution(self):
        return self.original_solution

    def get_similarity(self):
        return self.similarity

    def get_pearson_corr_metric(self):
        return self.pearson_corr_metric

    def get_p_corr_metric(self):
        return self.p_corr_metric

    def get_adapted_solution_score(self):
        return self.adapted_solution_score
