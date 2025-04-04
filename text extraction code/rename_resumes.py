import os

# Folder containing extracted resume files
resume_folder = "/Users/khyatimorparia/Desktop/DataScience_Resumes_Included/extracted_resumes"

# List all text files and rename them
for index, file_name in enumerate(os.listdir(resume_folder)):
    if file_name.endswith(".txt"):  # Ensure only text files are renamed
        new_file_name = f"resume_{index+1:03d}.txt"  # e.g., resume_001.txt, resume_002.txt
        old_path = os.path.join(resume_folder, file_name)
        new_path = os.path.join(resume_folder, new_file_name)

        os.rename(old_path, new_path)  # Rename the file
        print(f"🔄 Renamed {file_name} ➝ {new_file_name}")

print(" All files renamed successfully!")
