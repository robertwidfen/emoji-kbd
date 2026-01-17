"""Test the SearchGroup.match function for word boundary scoring."""

import sys

sys.path.insert(0, "src")

from board import SearchGroup


def test_match():
    tests = [
        [
            "Testing exact matches:",
            ("ear", "ear"),
            ("ear ", "ear"),
            (" ear", "ear"),
            (" ear ", "ear"),
        ],
        [
            "Testing matches at word start:",
            ("ears", "ear"),
            (" ears", "ear"),
            ("ears ", "ear"),
            (" ears ", "ear"),
        ],
        [
            "Testing matches at word end:",
            ("hear", "ear"),
            (" hear", "ear"),
            ("hear", "ear"),
            (" hear  ", "ear"),
        ],
        [
            "Testing matches within words:",
            ("hear", "ear"),
            (" hear", "ear"),
            ("hear ", "ear"),
            (" hear ", "ear"),
        ],
        [
            "Testing multiple matches:",
            (" ear, hear", "ear"),
            (" ear, hear ", "ear"),
            ("hear, ear", "ear"),
        ],
        [
            "Testing odd cases:",
            (" licht ", "lich"),
            (" unlich, anlich", "lich"),
            ("ohr", "ohr"),
            (" ohr,", "ohr"),
            ("ohr mit", "ohr"),
            (" ohr", "ohr"),
        ],
        [
            "Testing no matches:",
            ("hello", "ear"),
            ("test", "ear"),
        ],
    ]

    search = SearchGroup()

    for t in tests:
        print(t[0])
        for text, needle in t[1:]:
            score = search.match(text, needle)
            print(f"  match('{text}', '{needle}') = {score}")


if __name__ == "__main__":
    test_match()
