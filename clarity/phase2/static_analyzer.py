"""Thin wrapper around radon for cyclomatic complexity and LOC measurement."""

from typing import List, Tuple

from radon.complexity import cc_visit


class StaticAnalyzer:
    """Calculates static complexity metrics for a subset of covered lines."""

    def calculate_complexity(
        self, filepath: str, covered_lines: List[int]
    ) -> Tuple[int, float]:
        """Return (loc, cc) for the covered lines in a single source file.

        loc is simply the count of covered lines.
        cc is the sum of cyclomatic complexity scores for every
        function/method/class whose line range overlaps the covered set.

        Args:
            filepath: Absolute path to the Python source file.
            covered_lines: Lines measured as executed during the scenario.

        Returns:
            (loc, cc) — both zero if the file cannot be read or parsed.
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except OSError:
            return 0, 0.0

        loc = len(covered_lines)
        if loc == 0:
            return 0, 0.0

        covered_set = set(covered_lines)

        try:
            blocks = cc_visit(source)
        except SyntaxError:
            return loc, 0.0

        total_cc = 0.0
        for block in blocks:
            end = block.endline if block.endline else block.lineno
            block_lines = set(range(block.lineno, end + 1))
            if block_lines & covered_set:
                total_cc += block.complexity

        return loc, round(total_cc, 2)
