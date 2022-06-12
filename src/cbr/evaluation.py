import os
import shutil

import numpy as np


# This script is going to have different functions to do the evaluation in the CBR
def get_jaccard_simmularity(list1, list2):
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
# and return the mean of the similarity
# The similarity is computed using the jaccard index
# The case_library is a list of the cases
# The new_solution is the new solution
# The mean_similarity is the mean of the similarity
def evaluate_similarity_all_cases(case_library: list, new_solution: list) -> float:
    # Initialize the mean_similarity
    mean_similarity = 0
    # For each case in the case_library
    # Compute the similarity between the new solution and the case
    # Add the similarity to the mean_similarity
    # Divide by the number of cases
    # Return the mean_similarity
    for case in case_library:
        similarity = get_jaccard_simmularity(new_solution, case)
        mean_similarity += similarity
    mean_similarity /= len(case_library)
    return mean_similarity 


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
    similarity = get_jaccard_simmularity(adapted_solution, original_solution)
    return similarity

    
#Create a class that implements the evaluation of the solution
class Evaluation:
    def __init__(self, root: ET.Element):
        self.root = root
        self.adapted_solution = root.find("adaptedSolution").text
        self.original_solution = root.find("originalSolution").text
        self.similarity = get_jaccard_simmularity(self.adapted_solution, self.original_solution)
        self.pearson_corr_metric, self.p_corr_metric = get_pearson_corr_metric(self.adapted_solution, self.original_solution, np.mean(self.adapted_solution), np.mean(self.original_solution))
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

