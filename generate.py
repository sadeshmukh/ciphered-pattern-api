import os
from collections import defaultdict
import re
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# generate patternlists from either of 2 formats:
# 1. WORD separated by newlines
# 2. WORD COUNT separated by newlines

# outputs 
# PATTERN (e.g. 11213) WORD WORD WORD WORD WORD

INPUT_FILE = os.getenv("INPUT_FILE") or "data/words.txt"

def is_valid_word(word):
    """Validate if a string is a reasonable word from Google Ngram data."""
    # Must be at least 1 character and at most 20 characters
    if not (1 <= len(word) <= 20):
        return False
    
    # Must contain only letters
    if not word.isalpha():
        return False
    
    # Special case for single letters A and I
    if len(word) == 1 and word.upper() in ["A", "I"]:
        return True
    
    # Reject words that are all the same letter
    if len(set(word)) == 1:
        return False
    
    # Reject common abbreviations (2-3 letters)
    common_abbrevs = {
        "BBC", "CNN", "CIA", "FBI", "USA", "UK", "EU", "UN", "NATO", "WHO", "WTO",
        "EEC", "EEG", "EKG", "DNA", "RNA", "HIV", "AIDS", "UFO", "CCTV", "AARP",
        "DDT", "EPA", "FBI", "FDA", "IRS", "NASA", "NATO", "NBA", "NFL", "NHL",
        "NPR", "PBS", "TV", "VCR", "VHS", "WWW", "WWI", "WWII"
    }
    if word in common_abbrevs:
        return False
    
    # Reject words with too many consecutive same letters
    max_consecutive = 2
    current_consecutive = 1
    for i in range(1, len(word)):
        if word[i] == word[i-1]:
            current_consecutive += 1
            if current_consecutive > max_consecutive:
                return False
        else:
            current_consecutive = 1
    
    # Reject words that look like abbreviations (all consonants or all vowels)
    vowels = {'A', 'E', 'I', 'O', 'U'}
    if all(c in vowels for c in word) or all(c not in vowels for c in word):
        return False
    
    # Reject words with too many repeated letters
    letter_counts = {}
    for c in word:
        letter_counts[c] = letter_counts.get(c, 0) + 1
        if letter_counts[c] > 3:  # Allow at most 3 occurrences of any letter
            return False
    
    return True

def get_pattern(word):
    """Convert a word to its pattern where each letter is represented by its position in the word."""
    pattern = []
    seen = {}
    for char in word.lower():
        if char not in seen:
            seen[char] = len(seen) + 1
        pattern.append(str(seen[char]))
    return ''.join(pattern)

def process_line(line):
    """Process a line that could be either 'WORD' or 'WORD COUNT' format."""
    try:
        # Just take the first word from the line, ignoring any count
        word = line.strip().split()[0].upper()  # Convert to uppercase
        if is_valid_word(word):
            return word
    except IndexError:
        # Skip empty lines
        pass
    return None

async def process_chunk(chunk, pattern_dict):
    """Process a chunk of lines asynchronously."""
    for line in chunk:
        word = process_line(line)
        if word:
            pattern = get_pattern(word)
            pattern_dict[pattern].append(word)

async def main():
    pattern_dict = defaultdict(list)
    
    # Debug: Print input file path
    print(f"Reading from: {INPUT_FILE}")
    
    total_lines = sum(1 for _ in open(INPUT_FILE).readlines())
    print(f"Total lines in file: {total_lines}")
    
    pbar = tqdm(total=total_lines, desc="Processing words", unit="words", position=0)
    
    async with aiofiles.open(INPUT_FILE, mode='r') as f:
        chunk = []
        async for line in f:
            chunk.append(line)
            if len(chunk) >= 1000:
                await process_chunk(chunk, pattern_dict)
                pbar.update(len(chunk))
                chunk = []
        
        if chunk:
            await process_chunk(chunk, pattern_dict)
            pbar.update(len(chunk))
    
    pbar.close()

    # Debug: Print pattern counts
    print(f"Total patterns found: {len(pattern_dict)}")
    if len(pattern_dict) == 0:
        print("No patterns found! Checking first few lines of input file...")
        with open(INPUT_FILE, 'r') as f:
            for i, line in enumerate(f):
                if i >= 5:  # Just check first 5 lines
                    break
                print(f"Line {i}: {line.strip()}")
                word = process_line(line)
                if word:
                    pattern = get_pattern(word)
                    print(f"  Word: {word}, Pattern: {pattern}")
                else:
                    print("  Word rejected")

    os.makedirs('output', exist_ok=True)

    pbar = tqdm(total=len(pattern_dict), desc="Writing patterns", unit="patterns", position=1)    
    async with aiofiles.open('output/patterns.txt', mode='w') as f:
        # Sort patterns by the length of their first word
        sorted_patterns = sorted(pattern_dict.items(), 
                               key=lambda x: len(x[1][0]) if x[1] else 0)
        
        for pattern, words in sorted_patterns:
            # Sort words within each pattern by length
            sorted_words = sorted(words, key=len)
            await f.write(f"{pattern} {' '.join(sorted_words)}\n")
            pbar.update(1)
    pbar.close()

if __name__ == "__main__":
    asyncio.run(main())

