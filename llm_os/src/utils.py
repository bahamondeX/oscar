# src/utils.py
import spacy

nlp = spacy.load("en_core_web_sm")


def chunk_sentences(text: str, n: int = 4) -> list[str]:
    """Divide el texto en bloques de n oraciones"""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    chunks = [" ".join(sentences[i : i + n]) for i in range(0, len(sentences), n)]
    return chunks
