import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
import os
from convert import html_to_numpy
from grading import table_similarity


def parse_html(path: str) -> npt.NDArray[np.str_]:
    with open(path, "r") as f:
        html = f.read()
    return html_to_numpy(html)


predicted_folder_path = (
    "/Users/nischithshadagopan/Sarvam/rd-tablebench/data/providers/sarvam-parse"
)
ground_truth_folder_path = (
    "/Users/nischithshadagopan/Sarvam/rd-tablebench/data/groundtruth"
)

table_similarity_scores = []
for predicted_file in os.listdir(predicted_folder_path):
    ground_truth_path = os.path.join(ground_truth_folder_path, predicted_file)
    predicted_path = os.path.join(predicted_folder_path, predicted_file)
    ground_truth = parse_html(ground_truth_path)
    prediction = parse_html(predicted_path)

    table_similarity_score = table_similarity(ground_truth, prediction)
    if table_similarity_score < 0.6:
        print(predicted_file)
    table_similarity_scores.append(table_similarity_score)
average_table_similarity_score = sum(table_similarity_scores) / len(
    table_similarity_scores
)
# plot the table similarity scores as a frequency line plot
plt.hist(table_similarity_scores, bins=20)
plt.show()
print(average_table_similarity_score)
