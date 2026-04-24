"""
Explanation Engine - Generates human-readable reasoning steps for the CSP solver.
"""


class ExplanationEngine:
    def __init__(self, steps, solution, regions, neighbors, colors):
        self.steps = steps
        self.solution = solution
        self.regions = regions
        self.neighbors = neighbors
        self.colors = colors

    def generate_timeline(self):
        """
        Convert raw solver steps into a structured explanation timeline.
        Returns list of timeline events with step number, title, detail, type.
        """
        timeline = []
        step_num = 1

        type_meta = {
            "start":     {"icon": "🚀", "label": "Initialization",   "cls": "start"},
            "try":       {"icon": "🔍", "label": "Attempting",        "cls": "try"},
            "assign":    {"icon": "✅", "label": "Assignment",         "cls": "assign"},
            "conflict":  {"icon": "❌", "label": "Conflict Detected",  "cls": "conflict"},
            "backtrack": {"icon": "↩️", "label": "Backtracking",      "cls": "backtrack"},
            "success":   {"icon": "🎉", "label": "Solution Found",    "cls": "success"},
            "failure":   {"icon": "⛔", "label": "No Solution",       "cls": "failure"},
        }

        for raw in self.steps:
            t = raw.get("type", "try")
            meta = type_meta.get(t, {"icon": "•", "label": t.title(), "cls": t})

            timeline.append({
                "step": step_num,
                "type": t,
                "cls": meta["cls"],
                "icon": meta["icon"],
                "label": meta["label"],
                "region": raw.get("region"),
                "color": raw.get("color"),
                "message": raw.get("message", ""),
            })
            step_num += 1

        return timeline

    def generate_summary(self, confidence_score, backtracks, elapsed_ms, complexity_label):
        """Generate a human-readable text summary of the solving process."""
        lines = []
        lines.append("=== EXPLANATION SUMMARY ===")
        lines.append(f"Regions: {', '.join(self.regions)}")
        lines.append(f"Colors Available: {', '.join(self.colors)}")
        lines.append("")

        if self.solution:
            lines.append("Solution Found:")
            for region, color in self.solution.items():
                lines.append(f"  Region {region}  →  {color}")
        else:
            lines.append("No valid coloring was found.")

        lines.append("")
        lines.append(f"Algorithm: Backtracking CSP with MRV + LCV heuristics")
        lines.append(f"Backtracks Required: {backtracks}")
        lines.append(f"Execution Time: {elapsed_ms} ms")
        lines.append(f"Confidence Score: {confidence_score}%")
        lines.append(f"Complexity: {complexity_label}")
        return "\n".join(lines)

    def generate_constraint_explanation(self, constraint_analysis):
        """Produce detailed text explanation of each constraint."""
        explanations = []

        for item in constraint_analysis.get("satisfied", []):
            explanations.append({
                "pair": item["pair"],
                "status": "Satisfied",
                "detail": item["detail"],
                "icon": "✓",
                "cls": "satisfied"
            })

        for item in constraint_analysis.get("violated", []):
            explanations.append({
                "pair": item["pair"],
                "status": "Violated",
                "detail": item["detail"],
                "icon": "✗",
                "cls": "violated"
            })

        return explanations

    def get_key_decisions(self):
        """Extract only the key assignment decisions from step list."""
        decisions = []
        for s in self.steps:
            if s.get("type") in ("assign", "backtrack", "conflict"):
                decisions.append({
                    "type": s["type"],
                    "region": s.get("region"),
                    "color": s.get("color"),
                    "message": s.get("message")
                })
        return decisions
