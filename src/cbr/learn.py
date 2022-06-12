# Define ET to be the ElementTree library
import xml.etree.ElementTree as ET

# Create a function to learn from the ConstraintsBuildeR and return the root
# element of the xml file

# Learn the case and store  in the case case_library
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





# Function to learn from the ConstraintsBuilder and return the root element of the xml file
def learn_from_cbr(cbr_path: str, cbr_file: str) -> ET.Element:
    import xml.etree.ElementTree as ET
    import zipfile

    zip_ref = zipfile.ZipFile(cbr_path, "r")
    zip_ref.extractall(cbr_file)
    zip_ref.close()

    tree = ET.parse(cbr_file)
    root = tree.getroot()
    return root



# Create a class that implements the learning of the solution from the ConstraintsBuilder and storage in the case_library

class Learning:
    def __init__(self, root: ET.Element, case_library: dict):
        self.root = root
        
        
        self.case_library = case_library
        self.learn_case(root, case_library)
    

    
    def learn_from_cbr(self, cbr_path: str, cbr_file: str) -> ET.Element:
        import xml.etree.ElementTree as ET
        import zipfile

        zip_ref = zipfile.ZipFile(cbr_path, "r")
        zip_ref.extractall(cbr_file)
        zip_ref.close()

        tree = ET.parse(cbr_file)
        root = tree.getroot()
        return root
    
    # function to Storage in the case_library
    # input is the root element of the xml file learned from the ConstraintsBuilder
    # output is the case_library
    def learn_from_cbr(self, root: ET.Element, case_library: dict) -> None:
        # Get the case name
        case_name = root.find("caseName").text
        # Get the case ingredients
        case_ingredients = root.find("caseIngredients").text
        # Get the case score
        case_score = root.find("caseScore").text
        # Store the case in the case_library
        case_library[case_name] = [case_ingredients, case_score]
        print("Learned case: " + case_name)

    # Function to ask the user the score of the case
    # input is the evaluation element
    # output is the score of the case from the users input
    def ask_user_score(self, evaluation: ET.Element) -> str:
        # Get the case name
        case_name = evaluation.find("caseName").text
        # Get the case score
        case_score = evaluation.find("caseScore").text
        # Ask the user the score of the case
        user_score = input("What is the score of the case " + case_name + "? ")
        # Return the score of the case
        return user_score
    # function to print the score of the case
    # input is the score of the case
    # output is the score of the case
    def print_score(self, score: str) -> None:
        print("The score of the case is " + score)
    
# conditional where the learn class is used to determine if the user input is more than 0.8 
# if it is, the case is learned and the score is printed
# if it is not, the case is not learned and the score is printed
if __name__ == "__main__":
    # Create a case_library dictionary
    case_library = {}
    # Create a learning object
    learning = Learning(root, case_library)
    # Learn the case
    learning.learn_from_cbr(root, case_library)
    # Ask the user the score of the case
    user_score = learning.ask_user_score(evaluation)
    # Print the score of the case
    learning.print_score(user_score)
    # If the user score is more than 0.8, the case is learned and the score is printed
    if float(user_score) > 0.8:
        learning.learn_case(root, case_library)
        learning.print_score(user_score)
    # If the user score is less than 0.8, the case is not learned and the score is printed
    else:
        learning.print_score(user_score)
    # Print the case library
    print(case_library)
    