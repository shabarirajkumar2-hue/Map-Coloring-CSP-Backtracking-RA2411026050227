"""
CSP Solver - Map Coloring using Backtracking Search Algorithm
Implements Constraint Satisfaction Problem for map coloring.
"""

import time


class CSPSolver:
    def __init__(self, regions, neighbors, colors):
        """
        Initialize the CSP solver.
        :param regions: list of region names
        :param neighbors: dict {region: [adjacent_regions]}
        :param colors: list of available colors
        """
        self.regions = regions
        self.neighbors = neighbors
        self.colors = colors
        self.assignment = {}
        self.steps = []
        self.backtracks = 0
        self.constraints_checked = 0
        self.start_time = None

    def is_consistent(self, region, color):
        """Check if assigning color to region violates any constraint."""
        for neighbor in self.neighbors.get(region, []):
            if neighbor in self.assignment and self.assignment[neighbor] == color:
                self.constraints_checked += 1
                return False
        self.constraints_checked += 1
        return True

    def select_unassigned_variable(self):
        """MRV heuristic - select region with fewest remaining legal values."""
        unassigned = [r for r in self.regions if r not in self.assignment]
        if not unassigned:
            return None
        # Minimum Remaining Values (MRV) heuristic
        def remaining_values(region):
            return sum(1 for c in self.colors if self.is_consistent(region, c))
        return min(unassigned, key=remaining_values)

    def order_domain_values(self, region):
        """Least Constraining Value (LCV) heuristic."""
        def count_conflicts(color):
            count = 0
            for neighbor in self.neighbors.get(region, []):
                if neighbor not in self.assignment:
                    for c in self.colors:
                        if c != color and self.is_consistent(neighbor, c):
                            count += 1
            return count
        return sorted(self.colors, key=count_conflicts, reverse=True)

    def backtrack(self):
        """Recursive backtracking search."""
        if len(self.assignment) == len(self.regions):
            return True

        region = self.select_unassigned_variable()
        if region is None:
            return True

        for color in self.order_domain_values(region):
            self.steps.append({
                "type": "try",
                "region": region,
                "color": color,
                "message": f"Trying {color} for Region {region}"
            })

            if self.is_consistent(region, color):
                self.assignment[region] = color
                self.steps.append({
                    "type": "assign",
                    "region": region,
                    "color": color,
                    "message": f"Assigned {color} to Region {region} ✓"
                })

                result = self.backtrack()
                if result:
                    return True

                # Backtrack
                del self.assignment[region]
                self.backtracks += 1
                self.steps.append({
                    "type": "backtrack",
                    "region": region,
                    "color": color,
                    "message": f"Backtracking from Region {region} — conflict detected"
                })
            else:
                self.steps.append({
                    "type": "conflict",
                    "region": region,
                    "color": color,
                    "message": f"Conflict: {color} already used by adjacent region of {region}"
                })

        return False

    def solve(self):
        """
        Solve the map coloring CSP.
        Returns a dict with solution, steps, confidence_score, metadata.
        """
        self.start_time = time.time()
        self.assignment = {}
        self.steps = []
        self.backtracks = 0
        self.constraints_checked = 0

        self.steps.append({
            "type": "start",
            "region": None,
            "color": None,
            "message": f"Starting CSP Backtracking — {len(self.regions)} regions, {len(self.colors)} colors available"
        })

        success = self.backtrack()
        elapsed = round((time.time() - self.start_time) * 1000, 2)

        # Calculate total possible adjacency constraints
        total_constraints = sum(len(v) for v in self.neighbors.values())

        # Calculate satisfied constraints
        satisfied = 0
        violated = 0
        constraint_details = []
        for region, neighbors_list in self.neighbors.items():
            for neighbor in neighbors_list:
                if region in self.assignment and neighbor in self.assignment:
                    if self.assignment[region] != self.assignment[neighbor]:
                        satisfied += 1
                        constraint_details.append({
                            "pair": f"{region} — {neighbor}",
                            "status": "satisfied",
                            "detail": f"{self.assignment[region]} ≠ {self.assignment[neighbor]}"
                        })
                    else:
                        violated += 1
                        constraint_details.append({
                            "pair": f"{region} — {neighbor}",
                            "status": "violated",
                            "detail": f"Both assigned {self.assignment[region]}"
                        })

        # Confidence score calculation
        score = self._calculate_confidence(success, satisfied, total_constraints)

        if success:
            self.steps.append({
                "type": "success",
                "region": None,
                "color": None,
                "message": f"Solution found! All {len(self.regions)} regions colored successfully."
            })
        else:
            self.steps.append({
                "type": "failure",
                "region": None,
                "color": None,
                "message": "No solution found. Try adding more colors."
            })

        return {
            "success": success,
            "solution": self.assignment if success else {},
            "steps": self.steps,
            "backtracks": self.backtracks,
            "constraints_checked": self.constraints_checked,
            "satisfied_constraints": satisfied,
            "total_constraints": total_constraints // 2,  # undirected
            "violated_constraints": violated // 2,
            "constraint_details": constraint_details[::2],  # deduplicate
            "confidence_score": score,
            "elapsed_ms": elapsed,
            "regions_colored": len(self.assignment),
            "total_regions": len(self.regions)
        }

    def _calculate_confidence(self, success, satisfied, total):
        """
        Confidence score 0–100 based on:
        - Whether a solution was found
        - Constraint satisfaction ratio
        - Backtracking penalty
        """
        if not success:
            return 0.0

        base = 100.0
        # Backtracking penalty (max 30 points off)
        backtrack_penalty = min(self.backtracks * 2, 30)
        # Constraint bonus
        constraint_ratio = (satisfied / total * 20) if total > 0 else 20

        score = base - backtrack_penalty + (constraint_ratio - 20)
        return round(max(0, min(100, score)), 1)
