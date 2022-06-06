#Define ET to be the ElementTree library
import xml.etree.ElementTree as ET
# Create a function to learn from the ConstraintsBuildeR and return the root
# element of the xml file

#Learn the case and store  in the case case_library
def learn_case(root: ET.Element, case_library: dict) -> None:
    # Get the case name
    case_name = root.find("caseName").text
    # Get the case ingredients
    case_ingredients = root.find("caseIngredients").text
    # Get the case score
    case_score = root.find("caseScore").text
    # Store the case in the case_library
    case_library[case_name] = [case_ingredients, case_score]
    print("Learned case: " + case_name)



def learn_from_cbr(cbr_path: str, cbr_file: str) -> ET.Element:
    import zipfile
    import xml.etree.ElementTree as ET

    zip_ref = zipfile.ZipFile(cbr_path, "r")
    zip_ref.extractall(cbr_file)
    zip_ref.close()

    tree = ET.parse(cbr_file)
    root = tree.getroot()
    return root


