# utils/nlp_utils.py

import spacy

class NLPUtils:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')

    def parse_intent(self, text):
        doc = self.nlp(text)
        intents = [token.lemma_ for token in doc if token.pos_ == 'VERB']
        return intents

    def extract_entities(self, text):
        doc = self.nlp(text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities