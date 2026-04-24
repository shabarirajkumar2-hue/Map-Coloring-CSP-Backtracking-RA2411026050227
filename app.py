"""
app.py — Main Flask Application for Map Coloring CSP Solver
"""

import os
import json
import io
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, MapExecution
from csp_solver import CSPSolver
from constraint_engine import ConstraintEngine
from explanation_engine import ExplanationEngine
from report_generator import generate_pdf_report

# ── App Configuration ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "csp-map-coloring-secret-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(os.path.abspath("instance"), "csp_solver.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ── Auth Decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Helper ────────────────────────────────────────────────────────────────────
def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"]   = user.id
            session["user_name"] = user.name
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not name or not username or not password:
            flash("All fields are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        else:
            user = User(
                name=name,
                username=username,
                password=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    total   = MapExecution.query.filter_by(user_id=user.id).count()
    solved  = MapExecution.query.filter_by(user_id=user.id, success=True).count()
    failed  = total - solved
    avg_conf = db.session.query(
        db.func.avg(MapExecution.confidence_score)
    ).filter_by(user_id=user.id).scalar() or 0.0

    recent = (MapExecution.query
              .filter_by(user_id=user.id)
              .order_by(MapExecution.timestamp.desc())
              .limit(5).all())

    return render_template(
        "dashboard.html",
        user=user,
        total=total, solved=solved, failed=failed,
        avg_conf=round(avg_conf, 1),
        recent=recent
    )


# ── Solver ────────────────────────────────────────────────────────────────────
@app.route("/solver")
@login_required
def solver():
    user = current_user()
    return render_template("solver.html", user=user)


@app.route("/solve_map", methods=["POST"])
@login_required
def solve_map():
    user = current_user()
    data = request.get_json()

    regions_raw  = data.get("regions", [])
    neighbors_raw = data.get("neighbors", {})
    colors_raw   = data.get("colors", ["Red", "Green", "Blue"])

    # Normalise inputs
    regions   = [r.strip() for r in regions_raw if r.strip()]
    colors    = [c.strip() for c in colors_raw if c.strip()]
    neighbors = {}
    for region in regions:
        nbrs = neighbors_raw.get(region, [])
        neighbors[region] = [n.strip() for n in nbrs if n.strip() and n.strip() in regions]

    # Validate
    engine = ConstraintEngine(regions, neighbors, colors)
    validation = engine.validate_input()
    if not validation["valid"]:
        return jsonify({"success": False, "errors": validation["errors"]}), 400

    # Solve
    solver_inst = CSPSolver(regions, neighbors, colors)
    result = solver_inst.solve()

    # Constraint analysis
    constraint_analysis = engine.analyze_constraints(result["solution"])
    complexity_label = engine.compute_complexity(result["backtracks"], len(regions))
    adj_matrix = engine.get_adjacency_matrix()
    degree_info = engine.get_degree_info()

    # Explanation
    explain = ExplanationEngine(
        result["steps"], result["solution"], regions, neighbors, colors
    )
    timeline = explain.generate_timeline()
    constraint_exp = explain.generate_constraint_explanation(constraint_analysis)

    # Save to DB
    execution = MapExecution(
        user_id          = user.id,
        regions_json     = json.dumps(regions),
        neighbors_json   = json.dumps(neighbors),
        colors_json      = json.dumps(colors),
        solution_json    = json.dumps(result["solution"]),
        confidence_score = result["confidence_score"],
        complexity_label = complexity_label,
        backtracks       = result["backtracks"],
        elapsed_ms       = result["elapsed_ms"],
        success          = result["success"],
    )
    db.session.add(execution)
    db.session.commit()

    return jsonify({
        "success":               result["success"],
        "solution":              result["solution"],
        "confidence_score":      result["confidence_score"],
        "complexity_label":      complexity_label,
        "backtracks":            result["backtracks"],
        "elapsed_ms":            result["elapsed_ms"],
        "constraints_satisfied": constraint_analysis["satisfied"],
        "constraints_violated":  constraint_analysis["violated"],
        "satisfaction_pct":      constraint_analysis["satisfaction_percentage"],
        "fully_satisfied":       constraint_analysis["fully_satisfied"],
        "timeline":              timeline,
        "constraint_exp":        constraint_exp,
        "adj_matrix":            adj_matrix,
        "degree_info":           degree_info,
        "warnings":              validation["warnings"],
        "execution_id":          execution.id,
        "regions_colored":       result["regions_colored"],
        "total_regions":         result["total_regions"],
    })


# ── Insights ──────────────────────────────────────────────────────────────────
@app.route("/insights")
@login_required
def insights():
    user = current_user()
    executions = (MapExecution.query
                  .filter_by(user_id=user.id)
                  .order_by(MapExecution.timestamp.desc())
                  .all())

    # Build chart data
    dates  = [e.timestamp.strftime("%m/%d") for e in executions[-10:]]
    scores = [e.confidence_score for e in executions[-10:]]

    complexity_counts = {"LOW COMPLEXITY MAP": 0, "MEDIUM COMPLEXITY MAP": 0, "HIGH COMPLEXITY MAP": 0}
    for e in executions:
        label = e.complexity_label
        if label in complexity_counts:
            complexity_counts[label] += 1

    return render_template(
        "insights.html",
        user=user,
        executions=executions,
        chart_dates=json.dumps(dates),
        chart_scores=json.dumps(scores),
        complexity_counts=json.dumps(list(complexity_counts.values())),
        total_executions=len(executions),
        avg_confidence=round(sum(scores) / len(scores), 1) if scores else 0,
    )


# ── History ───────────────────────────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    executions = (MapExecution.query
                  .filter_by(user_id=user.id)
                  .order_by(MapExecution.timestamp.desc())
                  .paginate(page=page, per_page=10, error_out=False))
    return render_template("history.html", user=user, executions=executions)


# ── PDF Report ────────────────────────────────────────────────────────────────
@app.route("/generate_report/<int:execution_id>")
@login_required
def generate_report(execution_id):
    user = current_user()
    execution = MapExecution.query.filter_by(
        id=execution_id, user_id=user.id
    ).first_or_404()

    # Build explanation timeline for PDF
    explain = ExplanationEngine(
        [], execution.solution, execution.regions,
        execution.neighbors, execution.colors
    )

    pdf_data = {
        "username":              user.name,
        "regions":               execution.regions,
        "neighbors":             execution.neighbors,
        "colors_used":           execution.colors,
        "solution":              execution.solution,
        "confidence_score":      execution.confidence_score,
        "complexity_label":      execution.complexity_label,
        "constraints_satisfied": 0,
        "total_constraints":     sum(len(v) for v in execution.neighbors.values()) // 2,
        "backtracks":            execution.backtracks,
        "elapsed_ms":            execution.elapsed_ms,
        "timeline":              [],
        "timestamp":             execution.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Constraint analysis
    ce = ConstraintEngine(execution.regions, execution.neighbors, execution.colors)
    ca = ce.analyze_constraints(execution.solution)
    pdf_data["constraints_satisfied"] = len(ca["satisfied"])

    pdf_bytes = generate_pdf_report(pdf_data)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"csp_report_{execution_id}.pdf"
    )


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
