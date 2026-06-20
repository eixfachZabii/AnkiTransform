from spanish.normalize import normalize


def test_strips_lektion_prefix():
    assert normalize("1. la tarde") == "la tarde"
    assert normalize("0. ¿Cómo te llamas?") == "¿cómo te llamas?"


def test_lowercases_and_collapses_whitespace():
    assert normalize("  La   Tarde ") == "la tarde"


def test_nfc_equivalence():
    # combining tilde vs precomposed ñ must normalize equal
    assert normalize("español") == normalize("español")


def test_no_prefix_left_untouched():
    assert normalize("el coche") == "el coche"
