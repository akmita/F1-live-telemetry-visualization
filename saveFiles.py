import pickle

# Save an object to a file
def save_object(obj, filename):
    try:
        with open(filename, 'wb') as file:  # Open file in binary write mode
            pickle.dump(obj, file)  # Serialize the object
        print(f"Object saved to {filename}")
    except Exception as e:
        print(f"Error saving object: {e}")

# Load an object from a file
def load_object(filename):
    try:
        with open(filename, 'rb') as file:  # Open file in binary read mode
            obj = pickle.load(file)  # Deserialize the object
        print(f"Object loaded from {filename}")
        return obj
    except Exception as e:
        print(f"Error loading object: {e}")
        return None

    # # Save the object to a file
    # save_object(student, "object.pkl")
    #
    # # Load the object back from the file
    # loaded_student = load_object("object.pkl")

