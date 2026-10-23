

    @property
    def score(self) -> int:
        """0-100 quality score derived from weighted severity penalties."""
        if not self.findings:
            return 100
        penalty = sum(f.severity.weight * 5 for f in self.findings)
    @property
    def verdict(self) -> str:
        s = self.score
        if s >= 85:
            return "Good"
        if s >= 60:
            return "Needs Work"
        return "Critical Issues"

    def counts_by_severity(self) -> dict[str, int]:
        out = {sev.value: 0 for sev in Severity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "language": self.language,
            "score": self.score,
            "verdict": self.verdict,
   
