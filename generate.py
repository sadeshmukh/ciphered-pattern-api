import os
from collections import defaultdict
import re
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# generate patternlists from multiple input files in parallel
# 1. WORD separated by newlines
# 2. WORD COUNT separated by newlines

# outputs 
# PATTERN (e.g. 11213) WORD WORD WORD WORD WORD

DEFAULT_PATHS = ["data/american-words.95"]
INPUT_FILES = os.getenv("INPUT_FILES", "").split(",") + DEFAULT_PATHS # turns out I typoed my env variable for 20 minutes
print("Processing files: ", INPUT_FILES)

def is_valid_word(word):
    """Validate if a string is a reasonable word from SCOWL data."""
    if not (1 <= len(word) <= 20):
        return False
    
    if not word.replace("'", "").isalpha():
        return False
    
    if len(word) == 1 and word.upper() in ["A", "I"]:
        return True
    
    # reject all same letters, but see exception ^^
    if len(set(word.replace("'", ""))) == 1:
        return False
    
    # I'm lazy
    if "'" in word:
        return False
    
    # Reject words with too many consecutive same letters
    max_consecutive = 3 
    current_consecutive = 1
    for i in range(1, len(word)):
        if word[i] == word[i-1]:
            current_consecutive += 1
            if current_consecutive > max_consecutive:
                return False
        else:
            current_consecutive = 1
    
    letter_counts = {}
    for c in word:
        letter_counts[c] = letter_counts.get(c, 0) + 1
        if letter_counts[c] > 4:
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
        word = line.strip().split()[0].upper()
        if is_valid_word(word):
            return word
    except IndexError:
        pass
    return None

async def process_chunk(chunk, pattern_dict):
    """Process a chunk of lines asynchronously."""
    for line in chunk:
        word = process_line(line)
        if word:
            pattern = get_pattern(word)
            pattern_dict[pattern].append(word)

async def process_single_file(file_path, global_pattern_dict):
    """Process a SINGLE input file and in-place add words to global pattern dict."""
    file_pattern_dict = defaultdict(list)
    
    print(f"Processing: {file_path}")
    
    try:
        total_lines = sum(1 for _ in open(file_path).readlines())
        print(f"  Lines in {file_path}: {total_lines}")
        
        pbar = tqdm(total=total_lines, desc=f"Processing {os.path.basename(file_path)}", 
                   unit="words", position=len(global_pattern_dict))
        
        async with aiofiles.open(file_path, mode='r') as f:
            chunk = []
            async for line in f:
                chunk.append(line)
                if len(chunk) >= 1000:
                    await process_chunk(chunk, file_pattern_dict)
                    pbar.update(len(chunk))
                    chunk = []
            
            if chunk:
                await process_chunk(chunk, file_pattern_dict)
                pbar.update(len(chunk))
        
        pbar.close()
        
        for pattern, words in file_pattern_dict.items():
            global_pattern_dict[pattern].extend(words)
        
        print(f"  Patterns from {file_path}: {len(file_pattern_dict)}")
        
    except FileNotFoundError:
        print(f"  WARNING: File not found: {file_path}")
    except Exception as e:
        print(f"  ERROR processing {file_path}: {e}")

async def main():
    print(f"Processing {len(INPUT_FILES)} file(s) in parallel:")
    for i, file_path in enumerate(INPUT_FILES):
        print(f"  {i+1}. {file_path.strip()}")
    
    global_pattern_dict = defaultdict(list)
    
    tasks = []
    for file_path in INPUT_FILES:
        file_path = file_path.strip()
        if file_path:
            task = process_single_file(file_path, global_pattern_dict)
            tasks.append(task)
    
    await asyncio.gather(*tasks) # asyncio is so cool
    
    for pattern in global_pattern_dict:
        global_pattern_dict[pattern] = sorted(list(set(global_pattern_dict[pattern])))
    
    print(f"\nCombined results:")
    print(f"  Total patterns: {len(global_pattern_dict)}")
    total_words = sum(len(words) for words in global_pattern_dict.values())
    print(f"  Total unique words: {total_words}")
    
    if len(global_pattern_dict) == 0:
        print("No patterns found! Check your input files.")
        return

    os.makedirs('output', exist_ok=True)

    pbar = tqdm(total=len(global_pattern_dict), desc="Writing patterns", unit="patterns")    
    async with aiofiles.open('output/patterns.txt', mode='w') as f:
        sorted_patterns = sorted(global_pattern_dict.items(), 
                               key=lambda x: len(x[1][0]) if x[1] else 0)
        
        for pattern, words in sorted_patterns:
            sorted_words = sorted(words, key=len)
            await f.write(f"{pattern} {' '.join(sorted_words)}\n")
            pbar.update(1)
    pbar.close()
    
    print(f"Patterns written to output/patterns.txt")

if __name__ == "__main__":
    asyncio.run(main())

