import openai
import pandas as pd
import time
import re

openai.api_key = 'insert key here'

base_title = input("Enter a job title: ")
num_titles = int(input("Enter the number of job listings: "))

def generate_similar_job_titles(job_title: str, num_titles) -> list:
    title_prompt = f"""Generate {num_titles} realistic job titles related to "{job_title}".
    The titles should span entry-level to senior positions, with the following distribution:
    - 30% Entry-level positions
    - 40% Mid-level positions
    - 30% Senior-level positions
    
    Guidelines:
    - Most titles (70%) should use common base titles like 'Data Scientist' or 'Data Engineer'
    - 30% of titles should be long/detailed with specific industry/department context
    - Use simple seniority prefixes (Junior, Senior, Lead, Principal) for most titles
    - Entry-level can use Junior, Associate, or no prefix
    - Include a few different but related roles (e.g., ML Engineer, Analytics Engineer)
    
    Examples mix:
    - Data Scientist
    - Senior Data Scientist
    - Junior Data Engineer
    - Lead Machine Learning Engineer
    - Principal Data Scientist, Enterprise Risk Analytics
    
    Provide only the job titles in a list format, one per line.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a HR manager."},
                {"role": "user", "content": title_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message['content'].strip().split("\n")
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return []

def get_job_titles(base_title: str, num_titles) -> list:
    titles = []
    batch = 0
    
    print(f"Generating {num_titles} variations of {base_title}...")
    
    while len(titles) < num_titles:
        batch += 1
        new_titles = generate_similar_job_titles(base_title, num_titles)  
        titles.extend(new_titles)
        titles = list(dict.fromkeys(titles))  # Remove duplicates 
        
        print(f"Batch {batch}: Got {len(titles)} unique titles so far")
        
        time.sleep(21)  
    
    return titles[:num_titles]  

def generate_job_batch(job_titles: list) -> list:
    """Generate realistic job descriptions."""
    job_listings = []
    total_jobs = len(job_titles)
    
    for index, job_title in enumerate(job_titles, 1):
        prompt = f"""Generate a detailed and realistic job posting for the role "{job_title}". Each job should include:
        - Job Title
        - Description (2-3 sentences summarizing the role and its responsibilities)
        - Responsibilities (8-10 key responsibilities)
        - Qualifications (8-10 essential qualifications)
        - Preferred Qualifications (3 optional, but desirable qualifications)

        Format each job listing as follows:
        ---
        Title: [Job Title]
        Description: [Brief job description]
        Responsibilities:
        - [Responsibility 1]
        - [Responsibility 2]
        - [Responsibility 3]
        - [Responsibility 4]
        - [Responsibility 5]
        - [Responsibility 6]
        - [Responsibility 7]
        - [Responsibility 8]
        - [Responsibility 9]
        - [Responsibility 10]
        Qualifications:
        - [Qualification 1]
        - [Qualification 2]
        - [Qualification 3]
        - [Qualification 4]
        - [Qualification 5]
        - [Qualification 6]
        - [Qualification 7]
        - [Qualification 8]
        - [Qualification 9]
        - [Qualification 10]
        Preferred Qualifications:
        - [Preferred Qualification 1]
        - [Preferred Qualification 2]
        - [Preferred Qualification 3]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert HR consultant with deep knowledge of job roles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            job_content = response.choices[0].message['content']
            lines = job_content.split("\n")
            
            # Initialize job details
            job_details = {
                "Job Title": "Unknown Title",
                "Description": "",
                "Responsibilities": [],
                "Qualifications": [],
                "Preferred Qualifications": []
            }
            
            current_section = None

            for line in lines:
                line = line.strip()

                # Extract job title
                title_match = re.match(r"^Title:\s*(.+)$", line, re.IGNORECASE)
                if title_match:
                    job_details["Job Title"] = title_match.group(1).strip()
                    continue

                if line.startswith("Description:"):
                    job_details["Description"] = "'" + line.split(":", 1)[1].strip()  # Add protection
                    continue

                if re.match(r"^Responsibilities:", line, re.IGNORECASE):
                    current_section = "Responsibilities"
                    continue
                elif re.match(r"^Qualifications:", line, re.IGNORECASE):
                    current_section = "Qualifications"
                    continue
                elif re.match(r"^Preferred Qualifications:", line, re.IGNORECASE):
                    current_section = "Preferred Qualifications"
                    continue

                if line.startswith("-"):
                    item = line  
                    if current_section == "Responsibilities":
                        job_details["Responsibilities"].append(item)
                    elif current_section == "Qualifications":
                        job_details["Qualifications"].append(item)
                    elif current_section == "Preferred Qualifications":
                        job_details["Preferred Qualifications"].append(item)

            for section in ["Responsibilities", "Qualifications", "Preferred Qualifications"]:
                job_details[section] = "'" + "\n".join(job_details[section])

            job_listings.append(job_details)
            print(f"Generated job {index}/{total_jobs}: {job_details['Job Title']}")
            
        except Exception as e:
            print(f"API Error: {str(e)}")

        
        time.sleep(21)
    
    return job_listings

def save_jobs_to_csv(job_list: list, filename="job_listings.csv"):
    df = pd.DataFrame(job_list)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"{len(job_list)} job listings saved to {filename}")

unique_titles = get_job_titles(base_title, num_titles)  
print(f"\nGenerated {len(unique_titles)} unique titles. Starting job descriptions...")
job_listings = generate_job_batch(unique_titles)

save_jobs_to_csv(job_listings)