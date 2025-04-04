import os
import re
import json
import spacy
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple, Optional

class EnhancedResumeParser:
    """
    Resume parser with section detection and structured information extraction.
    """
    
    def __init__(self):
        
        self.nlp = spacy.load('en_core_web_sm')
        
        
        self.section_patterns = {
            'contact': {
                'patterns': [
                    r'^contact\s+information$', r'^contact\s+info$', r'^contact$', 
                    r'^personal\s+information$', r'^personal\s+info$', r'^personal\s+details$'
                ],
                'weight': 1.0
            },
            'summary': {
                'patterns': [
                    r'^summary$', r'^professional\s+summary$', r'^executive\s+summary$',
                    r'^profile$', r'^about\s+me$', r'^career\s+objective$', r'^objective$'
                ],
                'weight': 0.9
            },
            'education': {
                'patterns': [
                    r'^education$', r'^educational\s+background$', r'^academic\s+background$',
                    r'^academic\s+qualifications$', r'^qualifications$', r'^degrees$',
                    r'^educational\s+qualifications$'
                ],
                'weight': 0.95
            },
            'experience': {
                'patterns': [
                    r'^experience$', r'^work\s+experience$', r'^professional\s+experience$',
                    r'^employment\s+history$', r'^work\s+history$', r'^career\s+history$',
                    r'^professional\s+background$'
                ],
                'weight': 0.95
            },
            'skills': {
                'patterns': [
                    r'^skills$', r'^technical\s+skills$', r'^core\s+skills$',
                    r'^key\s+skills$', r'^competencies$', r'^areas\s+of\s+expertise$',
                    r'^expertise$'
                ],
                'weight': 0.9
            },
            'certifications': {
                'patterns': [
                    r'^certifications$', r'^certificates$', r'^professional\s+certifications$',
                    r'^licenses$', r'^accreditations$'
                ],
                'weight': 0.85
            },
            'projects': {
                'patterns': [
                    r'^projects$', r'^key\s+projects$', r'^project\s+experience$',
                    r'^major\s+projects$', r'^highlighted\s+projects$'
                ],
                'weight': 0.8
            }
        }

        # Common educational degrees for pattern matching
        self.degree_patterns = [
            r'(?i)(BS|BA|B\.S\.|B\.A\.|BSc|Master|MS|M\.S\.|MSc|MBA|PhD|Ph\.D\.|Bachelor|Associate)',
            r'(?i)(Bachelor of [A-Za-z\s]+|Master of [A-Za-z\s]+|Doctor of [A-Za-z\s]+)',
            r'(?i)(Diploma in [A-Za-z\s]+|Certificate in [A-Za-z\s]+)'
        ]
        
        # Build skills taxonomy
        self.skills_taxonomy = self._build_skills_taxonomy()
        
    def _build_skills_taxonomy(self) -> Dict[str, List[str]]:
        """Build a comprehensive taxonomy of skills by category"""
        return {
            'programming_languages': [
                'Python', 'Java', 'C++', 'C#', 'JavaScript', 'TypeScript', 'PHP', 
                'Ruby', 'Go', 'Swift', 'Kotlin', 'R', 'MATLAB', 'Scala', 'Perl',
                'HTML', 'CSS', 'SQL', 'Shell', 'Bash', 'PowerShell', 'Assembly'
            ],
            'frameworks_libraries': [
                'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring', 'Laravel',
                'Express.js', 'Node.js', 'TensorFlow', 'PyTorch', 'Keras', 'scikit-learn',
                'pandas', 'NumPy', 'Matplotlib', 'Bootstrap', 'jQuery', '.NET', 'ASP.NET'
            ],
            'databases': [
                'MySQL', 'PostgreSQL', 'Oracle', 'SQL Server', 'MongoDB', 'Redis',
                'Cassandra', 'SQLite', 'Elasticsearch', 'DynamoDB', 'Firebase'
            ],
            'cloud_platforms': [
                'AWS', 'Azure', 'Google Cloud', 'IBM Cloud', 'Oracle Cloud',
                'DigitalOcean', 'Heroku', 'Vercel', 'Netlify'
            ],
            'tools_technologies': [
                'Docker', 'Kubernetes', 'Git', 'GitHub', 'GitLab', 'Bitbucket',
                'Jenkins', 'Travis CI', 'CircleCI', 'Jira', 'Confluence', 'Terraform',
                'Ansible', 'Chef', 'Puppet', 'Selenium', 'Postman', 'Swagger'
            ],
            'methodologies': [
                'Agile', 'Scrum', 'Kanban', 'Waterfall', 'DevOps', 'CI/CD',
                'Test-Driven Development', 'Behavior-Driven Development',
                'Domain-Driven Design', 'Microservices', 'REST API', 'GraphQL'
            ],
            'soft_skills': [
                'Communication', 'Leadership', 'Teamwork', 'Problem Solving',
                'Critical Thinking', 'Time Management', 'Adaptability', 'Creativity',
                'Attention to Detail', 'Project Management', 'Conflict Resolution'
            ]
        }
    
    def _identify_sections(self, text: str) -> Dict[str, List[str]]:
        """
        Identify resume sections with improved detection.
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary with section types as keys and lines of content as values
        """
        lines = text.split('\n')
        current_section = 'header'
        sections = {'header': []}
        
        # First pass: identify section headers
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            best_match = None
            best_confidence = 0
            
            for section, config in self.section_patterns.items():
                for pattern in config['patterns']:
                    if re.match(pattern, line.lower()):
                        confidence = config['weight']
                        # Bonus confidence for all caps or title case headers
                        if line.isupper() or line.istitle():
                            confidence += 0.1
                        # Bonus for headers followed by separator lines (e.g., "----")
                        if i < len(lines) - 1 and re.match(r'^[=\-_]{3,}$', lines[i+1].strip()):
                            confidence += 0.15
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = section
            
            if best_match and best_confidence > 0.5:
                current_section = best_match
                sections[current_section] = []
            else:
                # Not a section header, add to current section
                sections[current_section].append(line)
        
        return sections
    
    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """
        Extract contact information with improved pattern matching.
        
        Args:
            text: Text from the contact section
            
        Returns:
            Dictionary with contact details
        """
        # Better email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Better phone pattern that handles multiple formats
        phone_pattern = r'\b(?:\+?\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b'
        
        # LinkedIn pattern
        linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9\-_]{5,30}/?'
        
        # GitHub pattern
        github_pattern = r'github\.com/[a-zA-Z0-9\-_]{1,39}/?'
        
        # Website/portfolio pattern
        website_pattern = r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
        
        # Process with spaCy for location detection
        doc = self.nlp(text)
        
        contact_info = {
            'email': re.findall(email_pattern, text),
            'phone': re.findall(phone_pattern, text),
            'linkedin': re.findall(linkedin_pattern, text),
            'github': re.findall(github_pattern, text),
            'website': re.findall(website_pattern, text),
            'location': [ent.text for ent in doc.ents if ent.label_ in ('GPE', 'LOC')],
        }
        
        # Clean up and take only first valid instance of each
        for key in contact_info:
            if contact_info[key]:
                contact_info[key] = contact_info[key][0]
            else:
                contact_info[key] = None
        
        return contact_info
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """
        Extract education information with improved detection.
        
        Args:
            text: Text from the education section
            
        Returns:
            List of dictionaries with education details
        """
        education = []
        
        # Process with spaCy for entity recognition
        doc = self.nlp(text)
        
        # Find all degree mentions
        degree_matches = []
        for pattern in self.degree_patterns:
            matches = re.finditer(pattern, text)
            degree_matches.extend([(match.group(), match.start(), match.end()) for match in matches])
        
        # Sort matches by position in text
        degree_matches.sort(key=lambda x: x[1])
        
        # Find education entries
        for i, (degree, start, end) in enumerate(degree_matches):
            next_start = len(text) if i == len(degree_matches) - 1 else degree_matches[i+1][1]
            
            # Extract the text segment for this degree
            segment = text[start:next_start].strip()
            edu_entry = {'degree': degree}
            
            # Look for institution
            for ent in doc.ents:
                if ent.label_ == 'ORG' and start <= ent.start_char < next_start:
                    edu_entry['institution'] = ent.text
                    break
            
            # Look for dates
            date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current|Now)'
            date_pattern2 = r'\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current|Now)'
            
            dates = re.findall(date_pattern, segment, re.IGNORECASE)
            if not dates:
                dates = re.findall(date_pattern2, segment)
            
            if dates:
                edu_entry['dates'] = dates[0]
            
            # Look for GPA
            gpa_pattern = r'GPA\s*(?:of|:)?\s*(\d+\.\d+|\d+)'
            gpa_matches = re.findall(gpa_pattern, segment, re.IGNORECASE)
            if gpa_matches:
                edu_entry['gpa'] = gpa_matches[0]
            
            # Only add if we have both degree and institution
            if 'degree' in edu_entry and ('institution' in edu_entry or len(degree) > 10):
                education.append(edu_entry)
        
        return education
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience with improved detection.
        
        Args:
            text: Text from the experience section
            
        Returns:
            List of dictionaries with experience details
        """
        experience = []
        
        # Process with spaCy for entity recognition
        doc = self.nlp(text)
        
        # Split text into probable job entries (looking for date patterns as separators)
        date_patterns = [
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current|Now)',
            r'\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current|Now)'
        ]
        
        # Combined pattern for matching dates
        combined_date_pattern = '|'.join(f'({pattern})' for pattern in date_patterns)
        
        # Find all date matches to use as potential job entry separators
        date_matches = list(re.finditer(combined_date_pattern, text))
        
        if date_matches:
            # Use dates to split into job entries
            job_segments = []
            for i, match in enumerate(date_matches):
                start = 0 if i == 0 else date_matches[i-1].end()
                end = match.start()
                if i > 0:  # Skip the first segment as it might be incomplete
                    job_segments.append(text[start:end].strip())
                
                # For the last date, include text after it
                if i == len(date_matches) - 1:
                    job_segments.append(text[match.end():].strip())
                
                # Always include the date with the following segment
                job_segments.append(text[match.start():match.end()].strip())
            
            # Process each job segment
            current_job = {}
            for segment in job_segments:
                # If segment is a date, add it to current job
                if any(re.match(pattern, segment) for pattern in date_patterns):
                    if current_job:
                        if 'dates' in current_job:
                            current_job['dates'] += ' ' + segment
                        else:
                            current_job['dates'] = segment
                    continue
                
                # Process job segment for company and title
                lines = segment.split('\n')
                if lines:
                    # First line might contain title and company
                    first_line = lines[0].strip()
                    
                    # Look for patterns like "Title at Company" or "Title - Company"
                    at_pattern = r'(.*?)\s+(?:at|@)\s+(.*)'
                    dash_pattern = r'(.*?)\s+[-–]\s+(.*)'
                    
                    at_match = re.match(at_pattern, first_line)
                    dash_match = re.match(dash_pattern, first_line) if not at_match else None
                    
                    if at_match or dash_match:
                        match = at_match or dash_match
                        current_job['title'] = match.group(1).strip()
                        current_job['company'] = match.group(2).strip()
                    else:
                        # Try to use first line as title and check for company in other lines
                        current_job['title'] = first_line
                        
                        # Check for company in other lines or using NER
                        for ent in doc.ents:
                            if (ent.label_ == 'ORG' and 
                                segment.find(ent.text) != -1 and
                                ent.text not in first_line):
                                current_job['company'] = ent.text
                                break
                    
                    # Extract responsibilities/achievements
                    responsibilities = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line and not any(re.match(pattern, line) for pattern in date_patterns):
                            responsibilities.append(line)
                    
                    if responsibilities:
                        current_job['responsibilities'] = responsibilities
                
                # If we have basic job details, save it and start a new one
                if current_job and ('title' in current_job or 'company' in current_job):
                    experience.append(current_job)
                    current_job = {}
        
        return experience
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills using taxonomy and context awareness.
        
        Args:
            text: Text from the skills section
            
        Returns:
            Dictionary with skill categories and detected skills
        """
        skills_by_category = {category: [] for category in self.skills_taxonomy}
        
        # Flatten skills taxonomy for easier lookup
        all_skills = {}
        for category, skills in self.skills_taxonomy.items():
            for skill in skills:
                all_skills[skill.lower()] = category
        
        # Find skills using taxonomy
        for skill in all_skills:
            # Create pattern that matches whole words only
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                category = all_skills[skill]
                matched_skill = re.search(pattern, text, re.IGNORECASE).group()
                skills_by_category[category].append(matched_skill)
        
        # Look for bullet-pointed or comma-separated skills
        bullet_pattern = r'(?:^|\n)(?:[\s•\-*])+(.+?)(?=\n|$)'
        comma_pattern = r'(?:^|:)\s*([^,]+(?:,[^,]+)+)(?=\n|$)'
        
        bullet_matches = re.findall(bullet_pattern, text)
        comma_matches = re.findall(comma_pattern, text)
        
        # Process bullet points
        for match in bullet_matches:
            words = match.strip().split()
            for word in words:
                word = word.strip('.,;:()[]{}').lower()
                if word in all_skills:
                    category = all_skills[word]
                    skills_by_category[category].append(word)
        
        # Process comma-separated lists
        for match in comma_matches:
            items = [item.strip() for item in match.split(',')]
            for item in items:
                item_lower = item.lower()
                if item_lower in all_skills:
                    category = all_skills[item_lower]
                    skills_by_category[category].append(item)
        
        # Remove duplicates and empty categories
        result = {}
        for category, skills in skills_by_category.items():
            unique_skills = list(set(skills))
            if unique_skills:
                result[category] = unique_skills
        
        return result
    
    def parse_resume(self, text: str) -> Dict[str, Any]:
        """
        Parse resume text into structured data with improved accuracy.
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary with structured resume data
        """
        # Identify sections in the resume
        sections = self._identify_sections(text)
        
        # Structure for parsed data
        structured_data = {
            'contact_info': {},
            'summary': '',
            'education': [],
            'experience': [],
            'skills': {},
            'certifications': [],
            'projects': [],
            'raw_text': text
        }
        
        # Extract data from each section
        for section, lines in sections.items():
            section_text = '\n'.join(lines)
            
            if section == 'header' or section == 'contact':
                structured_data['contact_info'] = self._extract_contact_info(section_text)
            elif section == 'summary':
                structured_data['summary'] = section_text
            elif section == 'education':
                structured_data['education'] = self._extract_education(section_text)
            elif section == 'experience':
                structured_data['experience'] = self._extract_experience(section_text)
            elif section == 'skills':
                structured_data['skills'] = self._extract_skills(section_text)
            elif section == 'certifications':
                # Simple extraction for certifications
                cert_lines = [line.strip() for line in lines if line.strip()]
                structured_data['certifications'] = cert_lines
            elif section == 'projects':
                # Simple extraction for projects
                project_lines = [line.strip() for line in lines if line.strip()]
                structured_data['projects'] = project_lines
        
        # Remove empty sections
        structured_data = {k: v for k, v in structured_data.items() 
                          if v or k == 'raw_text'}
        
        return structured_data
        
    def process_resume_file(self, input_path: str, output_path: str) -> bool:
        """
        Process a single resume file.
        
        Args:
            input_path: Path to input resume file
            output_path: Path to output JSON file
            
        Returns:
            Boolean indicating success
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            structured_data = self.parse_resume(text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")
            return False

    def process_resume_folder(self, input_folder: str, output_folder: str) -> None:
        """
        Process all resume files in a folder.
        
        Args:
            input_folder: Path to input folder with resume files
            output_folder: Path to output folder for JSON files
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        success_count = 0
        total_count = 0
        
        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                total_count += 1
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(
                    output_folder, 
                    os.path.splitext(filename)[0] + '.json'
                )
                
                if self.process_resume_file(input_path, output_path):
                    success_count += 1
                    print(f"Processed: {filename}")
        
        print(f"\nCompleted! Successfully processed {success_count} out of {total_count} resumes.")



if __name__ == "__main__":
    parser = EnhancedResumeParser()
    parser.process_resume_folder("redacted_resumes", "structured_resumes")