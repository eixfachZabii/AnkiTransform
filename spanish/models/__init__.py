from spanish.models import vocab, cloze, grammar

ALL_MODELS = [vocab.spec(), cloze.spec(), grammar.spec()]

__all__ = ["ALL_MODELS", "vocab", "cloze", "grammar"]
