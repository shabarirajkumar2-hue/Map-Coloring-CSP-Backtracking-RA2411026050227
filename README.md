# 🗺️ Map Coloring Problem Solver using CSP

**AI Lab Assignment — Constraint Satisfaction Problem (CSP) with Backtracking Search**

---

## 📌 Problem Description

The **Map Coloring Problem** is a classic Constraint Satisfaction Problem (CSP) where:
- A map consists of **regions**
- Adjacent regions must be assigned **different colors**
- The goal is to color all regions using the **minimum number of colors** such that no two neighboring regions share the same color

This is equivalent to the **Graph Coloring Problem** in graph theory and has real-world applications in:
- Frequency assignment in wireless networks
- Register allocation in compilers
- Scheduling problems
- Sudoku solving

---

## 🧠 Algorithm Used

### Constraint Satisfaction Problem (CSP) — Backtracking Search

The solver uses a combination of three techniques:

| Technique | Description |
|-----------|-------------|
| **Backtracking Search** | Recursively assigns colors to regions; undoes assignments when a conflict is detected |
| **MRV Heuristic** | Minimum Remaining Values — selects the region with the fewest legal color options next |
| **LCV Heuristic** | Least Constraining Value — tries the color that restricts neighbors the least |

### Algorithm Flow

```
1. Select unassigned region (MRV heuristic)
2. Order available colors (LCV heuristic)
3. For each color:
   a. Check adjacency constraints (is_consistent)
   b. If valid → assign color, recurse
   c. If recursion succeeds → return solution
   d. Else → undo assignment (backtrack), try next color
4. If no color works → return failure (propagates up)
5. If all regions assigned → return solution
```

---

## 📂 Project Structure

```
map_coloring_csp/
│
├── app.py                  # Flask application — routes, logic
├── models.py               # SQLAlchemy DB models (User, MapExecution)
├── csp_solver.py           # Core CSP Backtracking algorithm (MRV + LCV)
├── constraint_engine.py    # Constraint validation and adjacency analysis
├── explanation_engine.py   # Reasoning timeline and step explanation generator
├── report_generator.py     # ReportLab PDF report generator
├── requirements.txt        # Python dependencies
│
├── templates/
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Overview dashboard
│   ├── solver.html         # Interactive solver + visualization
│   ├── history.html        # Paginated execution history
│   └── insights.html       # Analytics with Chart.js
│
├── static/
│   ├── css/style.css       # Dark mode dashboard stylesheet
│   └── js/main.js          # AJAX solver, tag input, animations
│
└── instance/
    └── csp_solver.db       # SQLite database (auto-created)
```

---

## 🗃️ Database Schema

### `users` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment ID |
| name | VARCHAR(120) | Full name |
| username | VARCHAR(80) UNIQUE | Login username |
| password | VARCHAR(256) | Hashed password (Werkzeug) |
| created_at | DATETIME | Registration timestamp |

### `map_executions` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment ID |
| user_id | INTEGER FK | References users.id |
| regions_json | TEXT | JSON array of region names |
| neighbors_json | TEXT | JSON dict of adjacency |
| colors_json | TEXT | JSON array of colors |
| solution_json | TEXT | JSON dict of solution |
| confidence_score | FLOAT | 0–100 algorithm confidence |
| complexity_label | VARCHAR | LOW / MEDIUM / HIGH |
| backtracks | INTEGER | Backtracking steps taken |
| elapsed_ms | FLOAT | Execution time in ms |
| success | BOOLEAN | Whether solution was found |
| timestamp | DATETIME | Execution time |

---

## 📊 Confidence Score Logic

The confidence score (0–100%) is calculated as:

```python
base_score          = 100.0
backtrack_penalty   = min(backtracks * 2, 30)   # max 30 points off
constraint_bonus    = (satisfied / total) * 20

confidence = base_score - backtrack_penalty + (constraint_bonus - 20)
confidence = clamp(confidence, 0, 100)
```

| Score Range | Complexity Label |
|-------------|-----------------|
| Low backtracks + few regions | LOW COMPLEXITY MAP |
| Medium backtracks | MEDIUM COMPLEXITY MAP |
| High backtracks + many regions | HIGH COMPLEXITY MAP |

---

## 🚀 Execution Steps (Local Setup)

### 1. Clone / Setup Project

```bash
cd map_coloring_csp
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🌐 Sample Execution

### Input

```
Regions:   A, B, C, D, E
Colors:    Red, Green, Blue
Adjacency:
  A → B, C
  B → A, C, D
  C → A, B, D, E
  D → B, C, E
  E → C, D
```

### Output

```
STEP 1:  Trying Red for Region A
STEP 2:  Assigned Red to Region A ✓
STEP 3:  Trying Red for Region B
STEP 4:  Conflict: Red already used by adjacent region of B
STEP 5:  Trying Green for Region B
STEP 6:  Assigned Green to Region B ✓
STEP 7:  Trying Red for Region C
STEP 8:  Conflict detected
STEP 9:  Trying Blue for Region C
STEP 10: Assigned Blue to Region C ✓
...

Final Solution:
  A → Red
  B → Green
  C → Blue
  D → Red
  E → Green
```

---

## 🌍 Deployment on Render

### 1. Create `render.yaml` (optional) or configure manually:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Environment Variable:** `SECRET_KEY=your-secret-key`

### 2. Port Binding (already configured in `app.py`):

```python
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
```

### 3. Push to GitHub and connect to Render.

---

## 📄 PDF Report Contents

Each generated PDF includes:
- Student / user name and timestamp
- Execution summary table (regions, colors, time, confidence)
- Colored solution table (region → color with color-coded cells)
- Full adjacency relationship list
- Execution timeline (first 15 reasoning steps)
- Algorithm metadata footer

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.x |
| ORM | Flask-SQLAlchemy + SQLite |
| Auth | Werkzeug password hashing |
| PDF | ReportLab |
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Charts | Chart.js 4.x |
| Fonts | Google Fonts — Inter |
| Deployment | Render / Gunicorn |

---

## 👨‍💻 Author

**AI Lab Assignment — Map Coloring Problem Solver (CSP)**  
Algorithm: Backtracking Search + MRV + LCV Heuristics  
Subject: Artificial Intelligence Lab

---

## 📜 License

This project is for academic purposes only.
