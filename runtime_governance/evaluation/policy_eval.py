from collections import Counter

def policy_confusion(rows):
    """
    rows: list of (true_label, decision)
    """
    cm = Counter()
    for y, d in rows:
        cm[(y, d)] += 1
    return cm
