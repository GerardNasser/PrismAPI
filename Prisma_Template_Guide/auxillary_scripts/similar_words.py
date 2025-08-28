# similar_words.py (MODIFIED to work with Reticulate)

import sys
import nltk
from nltk.corpus import wordnet
import inflect

# NOTE: The NLTK download check has been removed.
# The R script now handles this setup step before running this script.

def get_variants(word):
    """Gets plural, possessive, and other forms of a word."""
    variants = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            name = lemma.name()
            if (
                name.startswith(word)
                and name != word
                and ' ' not in name
                and '-' not in name
                and '_' not in name
            ):
                variants.add(name)
    p = inflect.engine()
    plural = p.plural(word)
    if plural and plural != word and ' ' not in plural and '-' not in plural and '_' not in plural:
        variants.add(plural)
    possessive = word + "'s"
    if ' ' not in possessive and '-' not in possessive and '_' not in possessive:
        variants.add(possessive)
    variants.discard(word)
    return list(variants)[:20]

def get_synonyms(word):
    """Gets words with similar meanings."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    synonyms.discard(word)
    return list(synonyms)[:10]

def get_related_words(word):
    """Gets words with conceptual relationships (e.g., car -> wheel)."""
    related = set()
    for syn in wordnet.synsets(word):
        for rel in syn.hypernyms() + syn.hyponyms() + syn.part_meronyms() + syn.substance_meronyms() + syn.member_holonyms():
            for lemma in rel.lemmas():
                related.add(lemma.name())
    morph = wordnet.morphy(word)
    if morph and morph != word:
        related.add(morph)
    related.discard(word)
    return list(related)[:10]

def find_similar_words(keywords_list):
    """
    Main function to be called from R.
    Takes a list of keywords and returns a single formatted string with all results.
    """
    # If no words are provided, return an informative message.
    if not keywords_list:
        return "Please provide words as arguments."

    output_lines = [] # Collect all print lines into a list
    for word in keywords_list:
        variants = get_variants(word)
        synonyms = get_synonyms(word)
        related = get_related_words(word)

        output_lines.append(f"\nWord: {word}")
        
        output_lines.append("Variants:")
        if variants:
            for v in variants:
                output_lines.append(f"  - {v}")
        else:
            output_lines.append("  None found.")
            
        output_lines.append("Synonyms:")
        if synonyms:
            for s in synonyms:
                output_lines.append(f"  - {s}")
        else:
            output_lines.append("  None found.")

        output_lines.append("Related words:")
        if related:
            for r in related:
                output_lines.append(f"  - {r}")
        else:
            output_lines.append("  None found.")
        
        output_lines.append("-" * 40)
    
    # Join all the collected lines into a single string to return to R
    return "\n".join(output_lines)

# This block allows the script to STILL be run from the command line
if __name__ == "__main__":
    # Get words from command-line arguments
    words_from_cli = sys.argv[1:]
    # Call the main function
    result_string = find_similar_words(words_from_cli)
    # Print the final result
    print(result_string)