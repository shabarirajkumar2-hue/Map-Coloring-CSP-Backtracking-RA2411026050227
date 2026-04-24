"""
Database Models - SQLAlchemy ORM models for Map Coloring CSP application.
"""

import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    executions = db.relationship("MapExecution", backref="user", lazy=True,
                                 cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "username":   self.username,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class MapExecution(db.Model):
    __tablename__ = "map_executions"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Stored as JSON strings
    regions_json     = db.Column(db.Text, nullable=False)   # ["A","B","C"]
    neighbors_json   = db.Column(db.Text, nullable=False)   # {"A":["B"],...}
    colors_json      = db.Column(db.Text, nullable=False)   # ["Red","Green","Blue"]
    solution_json    = db.Column(db.Text, nullable=True)    # {"A":"Red",...}

    confidence_score = db.Column(db.Float, default=0.0)
    complexity_label = db.Column(db.String(40), default="")
    backtracks       = db.Column(db.Integer, default=0)
    elapsed_ms       = db.Column(db.Float, default=0.0)
    success          = db.Column(db.Boolean, default=False)
    timestamp        = db.Column(db.DateTime, default=datetime.utcnow)

    # ── helpers ──────────────────────────────────────────────────────────────
    @property
    def regions(self):
        return json.loads(self.regions_json)

    @property
    def neighbors(self):
        return json.loads(self.neighbors_json)

    @property
    def colors(self):
        return json.loads(self.colors_json)

    @property
    def solution(self):
        return json.loads(self.solution_json) if self.solution_json else {}

    def to_dict(self):
        return {
            "id":               self.id,
            "user_id":          self.user_id,
            "regions":          self.regions,
            "neighbors":        self.neighbors,
            "colors":           self.colors,
            "solution":         self.solution,
            "confidence_score": self.confidence_score,
            "complexity_label": self.complexity_label,
            "backtracks":       self.backtracks,
            "elapsed_ms":       self.elapsed_ms,
            "success":          self.success,
            "timestamp":        self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
