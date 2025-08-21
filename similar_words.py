
import sys
import nltk
from nltk.corpus import wordnet
import inflect

# Check if WordNet data is already downloaded
try:
    nltk.data.find('corpora/wordnet')
# If not, download WordNet quietly (no output)
except LookupError:
    nltk.download('wordnet', quiet=True)

# Function to get word variants (words that start with the input and are single words)
def get_variants(word):
    variants = set()  # Create an empty set to store variants
    # Loop through all synsets (groups of synonyms) for the word
    for syn in wordnet.synsets(word):
        # Loop through all lemmas (word forms) in each synset
        for lemma in syn.lemmas():
            name = lemma.name()  # Get the actual word
            # Only add if it starts with the input word, is not the word itself, and has no spaces, hyphens, or underscores
            if (
                name.startswith(word)
                and name != word
                and ' ' not in name
                and '-' not in name
                and '_' not in name
            ):
                variants.add(name)
    # Use inflect to get the plural form of the word
    p = inflect.engine()
    plural = p.plural(word)
    # Add plural if it's different and is a single word
    if plural and plural != word and ' ' not in plural and '-' not in plural and '_' not in plural:
        variants.add(plural)
    # Add possessive form (e.g., car's) if it's a single word
    possessive = word + "'s"
    if ' ' not in possessive and '-' not in possessive and '_' not in possessive:
        variants.add(possessive)
    # Remove the original word if it got added
    variants.discard(word)
    # Return up to 20 variants as a list
    return list(variants)[:20]

# Function to get synonyms (words with similar meaning)
def get_synonyms(word):
    synonyms = set()  # Create an empty set for synonyms
    # Loop through all synsets for the word
    for syn in wordnet.synsets(word):
        # Loop through all lemmas in each synset
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())  # Add the word form
    synonyms.discard(word)  # Remove the original word
    # Return up to 10 synonyms as a list
    return list(synonyms)[:10]

# Function to get related words (words with conceptual relationships)
def get_related_words(word):
    related = set()  # Create an empty set for related words
    # Loop through all synsets for the word
    for syn in wordnet.synsets(word):
        # For each synset, get related synsets (hypernyms, hyponyms, holonyms, meronyms)
        for rel in syn.hypernyms() + syn.hyponyms() + syn.part_meronyms() + syn.substance_meronyms() + syn.member_holonyms():
            # Add all lemma names from these related synsets
            for lemma in rel.lemmas():
                related.add(lemma.name())
    # Add a morphological variant (different form of the word)
    morph = wordnet.morphy(word)
    if morph and morph != word:
        related.add(morph)
    related.discard(word)  # Remove the original word
    # Return up to 10 related words as a list
    return list(related)[:10]

# Main script execution starts here
if __name__ == "__main__":
    # Get words from command-line arguments (ignoring the script name)
    words_list = sys.argv[1:]
    # If no words are provided, print a message and exit
    if not words_list:
        print("Please provide words as arguments.")
        sys.exit(1)
    # For each word provided
    for word in words_list:
        # Get variants, synonyms, and related words
        variants = get_variants(word)
        synonyms = get_synonyms(word)
        related = get_related_words(word)
        # Print the word being processed
        print(f"\nWord: {word}")
        # Print variants
        print("Variants:")
        if variants:
            for v in variants:
                print(f"  - {v}")
        else:
            print("  None found.")
        # Print synonyms
        print("Synonyms:")
        if synonyms:
            for s in synonyms:
                print(f"  - {s}")
        else:
            print("  None found.")
        # Print related words
        print("Related words:")
        if related:
            for r in related:
                print(f"  - {r}")
        else:
            print("  None found.")
        # Print a separator line
        print("-" * 40)