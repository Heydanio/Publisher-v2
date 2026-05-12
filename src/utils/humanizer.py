"""
Stylometric Humanizer 2026

TikTok et YouTube détectent les textes générés par LLM via:
- Perplexité (texte trop prévisible)
- Structure syntaxique parfaite
- Vocabulaire générique

Ce module ajoute du "bruit humain" pour casser ces signaux.
"""
import random
import re
from typing import Optional


# Variations naturelles
HUMAN_CONNECTORS = ["btw", "tho", "ngl", "fr", "lowkey", "honestly"]
HUMAN_FILLERS = ["uhh", "hmm", "wait", "ok so"]

# Typos contrôlés (rares mais réalistes)
CONTROLLED_TYPOS = {
    "the": "teh",      # ~0.5% rate
    "and": "adn",      
    "you": "yuo",
    "have": "hve",
    "really": "rly",
}


def add_human_imperfection(
    text: str, 
    intensity: float = 0.1,
    seed: Optional[str] = None
) -> str:
    """
    Ajoute des imperfections humaines au texte.
    
    Args:
        text: Texte à humaniser
        intensity: 0.0-1.0 (0=aucune modif, 1=maximum)
        seed: Pour reproductibilité
    
    Returns:
        Texte humanisé
    """
    if seed:
        random.seed(seed)
    
    words = text.split()
    new_words = []
    
    for word in words:
        # Random typo (very rare)
        if random.random() < intensity * 0.05:
            word_lower = word.lower().strip(".,!?")
            if word_lower in CONTROLLED_TYPOS:
                word = word.replace(word_lower, CONTROLLED_TYPOS[word_lower])
        
        # Random lowercase Start of word (10% intensity-adjusted)
        if random.random() < intensity * 0.1:
            if len(word) > 1 and word[0].isupper():
                word = word[0].lower() + word[1:]
        
        new_words.append(word)
    
    result = " ".join(new_words)
    
    # Random missing capital at sentence start
    if random.random() < intensity * 0.3:
        if result and result[0].isupper():
            result = result[0].lower() + result[1:]
    
    if seed:
        random.seed()
    
    return result


def vary_sentence_structure(sentences: list, seed: Optional[str] = None) -> list:
    """
    Varie la structure des phrases pour éviter la prévisibilité.
    """
    if seed:
        random.seed(seed)
    
    result = []
    for sentence in sentences:
        # 20% chance d'inverser ordre des mots clés
        if random.random() < 0.2 and len(sentence.split()) > 4:
            parts = sentence.split(",")
            if len(parts) > 1:
                random.shuffle(parts)
                sentence = ",".join(parts)
        
        result.append(sentence)
    
    if seed:
        random.seed()
    
    return result


def diversify_emoji_usage(text: str, max_emojis: int = 2) -> str:
    """
    Limite l'usage d'emojis pour rester naturel.
    Les bots ont tendance à mettre trop d'emojis.
    """
    emoji_pattern = re.compile(
        r'[\U0001F300-\U0001F9FF]|[\U00002600-\U000027BF]'
    )
    
    emojis = emoji_pattern.findall(text)
    if len(emojis) <= max_emojis:
        return text
    
    # Garde seulement max_emojis aléatoires
    kept = random.sample(emojis, max_emojis)
    result = text
    
    for emoji in emojis:
        if emoji not in kept:
            result = result.replace(emoji, "", 1)
        else:
            kept.remove(emoji)
    
    return result.strip()


def humanize_description(
    description: str,
    seed: Optional[str] = None,
    aggressive: bool = False
) -> str:
    """
    Humanise une description complète.
    
    Args:
        description: Texte à humaniser
        seed: Pour reproductibilité (ex: video_id)
        aggressive: Mode aggressive (plus d'imperfections)
    """
    intensity = 0.3 if aggressive else 0.1
    
    # Step 1: Diversify emojis
    text = diversify_emoji_usage(description)
    
    # Step 2: Add imperfections
    text = add_human_imperfection(text, intensity=intensity, seed=seed)
    
    return text
