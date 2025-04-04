import os
import re
import spacy
import nltk
import shutil
from typing import Dict, List, Tuple, Set, Optional

try:
    nltk.data.find('corpora/names')
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('names', quiet=True)
    nltk.download('words', quiet=True)

from nltk.corpus import names, words

class FocusedPIIRedactor:
    """
    A PII redactor that specifically targets personal identifiable information
    like names, emails, and phone numbers, while minimizing false positives.
    """
    
    def __init__(self):
        
        self.nlp = spacy.load('en_core_web_sm')
        
        # Build name sets
        self.male_names = set(name.lower() for name in names.words('male.txt'))
        self.female_names = set(name.lower() for name in names.words('female.txt'))
        self.all_names = self.male_names.union(self.female_names)
        
        # Common words to avoid false positives
        self.common_words = set(word.lower() for word in words.words())
        
        # Compiled regex patterns for specific PII types
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            'linkedin': re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?'),
            'ssn': re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{16}\b')
        }
        
        # Additional patterns for name detection in resume context
        self.title_pattern = re.compile(r'\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')

    def _is_likely_name(self, text: str) -> bool:
        """
        Check if a string is likely to be a name.
        
        Args:
            text: Text to check
            
        Returns:
            Boolean indicating if text is likely a name
        """
        words = text.split()
        
        # Too many words to be a name
        if len(words) > 3:
            return False
        
        # Check for common name patterns
        first_word_lower = words[0].lower()
        
        # If first word is in name lists
        if first_word_lower in self.all_names:
            # If only one word, it's likely a name
            if len(words) == 1:
                return True
            
            # For multiple words, check if they follow name patterns
            if len(words) >= 2:
                # Check if second word is a name or initial
                second_word = words[1]
                if (second_word.lower() in self.all_names or
                    (len(second_word) == 2 and second_word[1] == '.')):
                    return True
                
                # Check if it looks like a last name (capitalized and not a common word)
                if (second_word[0].isupper() and 
                    second_word.lower() not in self.common_words):
                    return True
        
        # Check for patterns like First M. Last or First Middle Last
        if (len(words) >= 2 and 
            all(word[0].isupper() for word in words) and
            any(word.lower() in self.all_names for word in words)):
            return True
        
        return False

    def _find_name_candidates(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Find potential name candidates in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of tuples (name, start_pos, end_pos)
        """
        candidates = []
        
        # Use spaCy's NER to find PERSON entities
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                candidates.append((ent.text, ent.start_char, ent.end_char))
        
        # Find names with titles (Mr., Ms., etc.)
        for match in self.title_pattern.finditer(text):
            name = match.group(1)
            start = match.start(1)
            end = match.end(1)
            candidates.append((name, start, end))
        
        # Find common first/last name combinations
        lines = text.split("\n")
        # Check the first few lines for headers/resume names
        for line in lines[:5]:
            words = line.split()
            if 2 <= len(words) <= 3 and all(word[0].isupper() for word in words):
                potential_name = " ".join(words)
                if self._is_likely_name(potential_name):
                    start = text.find(potential_name)
                    if start != -1:
                        candidates.append((potential_name, start, start + len(potential_name)))
        
        return candidates

    def _redact_pii_by_pattern(self, text: str) -> str:
        """
        Redact PII based on regex patterns.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        redacted = text
        
        # Redact emails
        redacted = self.pii_patterns['email'].sub('[EMAIL]', redacted)
        
        # Redact phone numbers
        redacted = self.pii_patterns['phone'].sub('[PHONE]', redacted)
        
        # Redact LinkedIn URLs
        redacted = self.pii_patterns['linkedin'].sub('[LINKEDIN]', redacted)
        
        # Redact SSNs
        redacted = self.pii_patterns['ssn'].sub('[SSN]', redacted)
        
        # Redact credit card numbers
        redacted = self.pii_patterns['credit_card'].sub('[CREDIT_CARD]', redacted)
        
        return redacted

    def redact_text(self, text: str) -> str:
        """
        Redact PII from text while preserving other content.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        # First, redact pattern-based PII (emails, phones, etc.)
        redacted = self._redact_pii_by_pattern(text)
        
        # Find name candidates
        name_candidates = self._find_name_candidates(text)
        
        # Sort by position in reverse order to maintain correct indices when replacing
        name_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Redact names
        for name, start, end in name_candidates:
            if self._is_likely_name(name):
                redacted = redacted[:start] + '[NAME]' + redacted[end:]
        
        return redacted

    def process_file(self, input_path: str, output_path: str) -> None:
        """
        Process a single file to redact PII.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            redacted_text = self.redact_text(text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
                
            print(f"Successfully redacted: {input_path}")
        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")

    def _redact_filename(self, filename: str) -> str:
        """
        Redact potential PII from filenames - more aggressive approach.
        
        Args:
            filename: Original filename
            
        Returns:
            Redacted filename
        """
        # Remove file extension for processing
        base_name, extension = os.path.splitext(filename)
        
        # Default to redacting the filename in the following scenarios:
        
        # 1. Any common name patterns in the filename
        for name in self.all_names:
            if name in base_name.lower():
                return f"candidate_{hash(base_name) % 10000:04d}{extension}"
        
        # 2. Check for CamelCase or capitalized word patterns typical of names
        if re.search(r'[A-Z][a-z]+[A-Z][a-z]+', base_name):  # CamelCase
            return f"candidate_{hash(base_name) % 10000:04d}{extension}"
        
        # 3. Check for separated capitalized words (First Last)
        capitalized_words = re.findall(r'[A-Z][a-z]+', base_name)
        if len(capitalized_words) >= 2:
            return f"candidate_{hash(base_name) % 10000:04d}{extension}"
        
        # 4. Check for common name prefixes/titles
        if re.search(r'\b(Mr|Mrs|Ms|Miss|Dr|Prof)[_\.\s-]', base_name, re.IGNORECASE):
            return f"candidate_{hash(base_name) % 10000:04d}{extension}"
        
        # 5. Check for resume patterns that often include names
        name_patterns = [
            r'resume[_\.\s-]of[_\.\s-]',
            r'cv[_\.\s-]of[_\.\s-]',
            r'resume[_\.\s-]',
            r'cv[_\.\s-]'
        ]
        
        for pattern in name_patterns:
            if re.search(pattern, base_name, re.IGNORECASE):
                return f"candidate_{hash(base_name) % 10000:04d}{extension}"
        
        # If none of the patterns match, keep the original filename
        return filename
    
    def process_folder(self, input_folder: str, output_folder: str, redact_filenames: bool = True) -> None:
        """
        Process all text files in a folder to redact PII.
        
        Args:
            input_folder: Path to input folder
            output_folder: Path to output folder
            redact_filenames: Whether to redact PII from filenames
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        file_count = 0
        filename_mapping = {}  # To keep track of original to redacted filename mapping
        
        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                input_path = os.path.join(input_folder, filename)
                
                if redact_filenames:
                    redacted_filename = self._redact_filename(filename)
                    filename_mapping[filename] = redacted_filename
                    output_path = os.path.join(output_folder, redacted_filename)
                else:
                    output_path = os.path.join(output_folder, filename)
                
                self.process_file(input_path, output_path)
                file_count += 1
        
        # Save filename mapping if any filenames were redacted
        if redact_filenames and filename_mapping:
            mapping_path = os.path.join(output_folder, "filename_mapping.txt")
            with open(mapping_path, 'w', encoding='utf-8') as f:
                for original, redacted in filename_mapping.items():
                    f.write(f"{original} -> {redacted}\n")
            print(f"Filename mapping saved to: {mapping_path}")
        
        print(f"Completed! Processed {file_count} files.")



if __name__ == "__main__":
    redactor = FocusedPIIRedactor()
    # Set redact_filenames=True to also anonymize filenames that contain names
    redactor.process_folder("extracted_resumes", "redacted_resumes", redact_filenames=True)