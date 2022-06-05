#Define ET to be the ElementTree library
import xml.etree.ElementTree as ET
# Create a function to learn from the ConstraintsBuildeR and return the root
# element of the xml file
def learn_from_cbr(cbr_path: str, cbr_file: str) -> ET.Element:
    import zipfile
    import xml.etree.ElementTree as ET

    zip_ref = zipfile.ZipFile(cbr_path, "r")
    zip_ref.extractall(cbr_file)
    zip_ref.close()

    tree = ET.parse(cbr_file)
    root = tree.getroot()
    return root

# Evaluate the learning rate of the ConstraintsBuildeR
def evaluate_learning_rate(root: ET.Element) -> float:
    # Get the learning rate
    learning_rate = root.find("learningRate").text
    return float(learning_rate)