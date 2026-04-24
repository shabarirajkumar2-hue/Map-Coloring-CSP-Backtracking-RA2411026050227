"""
Constraint Engine - Validates and analyzes CSP constraints for Map Coloring.
"""


class ConstraintEngine:
    def __init__(self, regions, neighbors, colors):
        self.regions = regions
        self.neighbors = neighbors
        self.colors = colors

    def validate_input(self):
        """Validate user inputs before solving."""
        errors = []
        warnings = []

        if len(self.regions) < 2:
            errors.append("At least 2 regions are required.")

        if len(self.colors) < 2:
            errors.append("At least 2 colors are required.")

        for region in self.regions:
            if not region.strip():
                errors.append("Region names cannot be empty.")
                break

        # Check neighbor references validity
        for region, nbrs in self.neighbors.items():
            if region not in self.regions:
                errors.append(f"Neighbor reference '{region}' is not a defined region.")
            for n in nbrs:
                if n not in self.regions:
                    errors.append(f"Neighbor '{n}' of region '{region}' is not a defined region.")

        # Chromatic number estimation
        max_degree = max((len(v) for v in self.neighbors.values()), default=0)
        if max_degree >= len(self.colors):
            warnings.append(
                f"High connectivity detected (max degree={max_degree}). "
                f"Solution may be hard to find with only {len(self.colors)} colors."
            )

        return {"errors": errors, "warnings": warnings, "valid": len(errors) == 0}

    def analyze_constraints(self, solution):
        """
        Analyze the final solution for constraint satisfaction.
        Returns a full constraint breakdown.
        """
        satisfied = []
        violated = []
        seen = set()

        for region in self.regions:
            for neighbor in self.neighbors.get(region, []):
                pair = tuple(sorted([region, neighbor]))
                if pair in seen:
                    continue
                seen.add(pair)

                r_color = solution.get(region, "Unassigned")
                n_color = solution.get(neighbor, "Unassigned")

                if r_color != "Unassigned" and n_color != "Unassigned":
                    if r_color != n_color:
                        satisfied.append({
                            "pair": f"{region} ↔ {neighbor}",
                            "status": "satisfied",
                            "detail": f"{r_color} ≠ {n_color}",
                            "icon": "✓"
                        })
                    else:
                        violated.append({
                            "pair": f"{region} ↔ {neighbor}",
                            "status": "violated",
                            "detail": f"Both = {r_color}",
                            "icon": "✗"
                        })

        total = len(satisfied) + len(violated)
        pct = round(len(satisfied) / total * 100, 1) if total > 0 else 0.0

        return {
            "satisfied": satisfied,
            "violated": violated,
            "total": total,
            "satisfaction_percentage": pct,
            "fully_satisfied": len(violated) == 0
        }

    def compute_complexity(self, backtracks, regions_count):
        """Determine map complexity label."""
        score = backtracks + regions_count
        if score <= 5:
            return "LOW COMPLEXITY MAP"
        elif score <= 15:
            return "MEDIUM COMPLEXITY MAP"
        else:
            return "HIGH COMPLEXITY MAP"

    def get_adjacency_matrix(self):
        """Return adjacency matrix for visualization."""
        matrix = []
        for r1 in self.regions:
            row = []
            for r2 in self.regions:
                if r1 == r2:
                    row.append(0)
                elif r2 in self.neighbors.get(r1, []):
                    row.append(1)
                else:
                    row.append(0)
            matrix.append(row)
        return {"regions": self.regions, "matrix": matrix}

    def get_degree_info(self):
        """Return degree (number of neighbors) for each region."""
        return [
            {"region": r, "degree": len(self.neighbors.get(r, []))}
            for r in self.regions
        ]
