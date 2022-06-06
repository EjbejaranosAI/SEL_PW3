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
