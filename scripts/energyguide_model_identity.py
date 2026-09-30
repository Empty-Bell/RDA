"""Shared printed EnergyGuide model inclusion rule for PDP identity checks.

This is a label/PDP rule. EPA Current registration keeps its independent
dataset-specific model matching rules.
"""

import re


def normalize_pdp(value, *, strip_terminal_aa=False):
    identifier = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    return identifier[:-2] if strip_terminal_aa and identifier.endswith("AA") else identifier


def normalize_label(value):
    return re.sub(r"[^A-Z0-9*?]", "", str(value or "").upper())


def matches_printed_model(label_model, pdp_model, *, strip_terminal_aa=False):
    """Match all visible fixed positions; trailing stars may be empty.

    A printed token may be shorter than the PDP configuration suffix. A token
    longer than the PDP may only exceed it with trailing wildcard characters.
    Fixed text after an internal wildcard still has to agree positionally.
    """
    pattern = normalize_label(label_model)
    identifier = normalize_pdp(pdp_model, strip_terminal_aa=strip_terminal_aa)
    fixed_prefix = re.split(r"[*?]", pattern, maxsplit=1)[0]
    # A one- or two-character OCR fragment is not model identity evidence.
    # Six fixed characters is the minimum observed in the accepted corpus;
    # shorter future captures remain unresolved instead of becoming PASS.
    if len(fixed_prefix) < 6 or not identifier.startswith(fixed_prefix):
        return False
    if not all(token in "*?" or token == character for token, character in zip(pattern, identifier)):
        return False
    return all(token in "*?" for token in pattern[len(identifier):])
