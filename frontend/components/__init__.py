"""
frontend/components/__init__.py
NeuralHire components package — re-exports all UI primitives.
"""
from .ui import (
    score_color, decision_from_score, badge_class, badge_icon, score_class,
    sidebar_brand, sidebar_status, sidebar_footer,
    page_header, section_label,
    stat_row,
    score_hero,
    draw_donut, draw_radar, draw_component_bars,
    draw_model_comparison_chart, draw_ranking_chart,
    skill_chips, skill_section,
    ai_recommendation_panel,
    feature_card, architecture_table,
    ranking_card,
    swot_section, recommendations_section,
)

__all__ = [
    "score_color", "decision_from_score", "badge_class", "badge_icon", "score_class",
    "sidebar_brand", "sidebar_status", "sidebar_footer",
    "page_header", "section_label",
    "stat_row",
    "score_hero",
    "draw_donut", "draw_radar", "draw_component_bars",
    "draw_model_comparison_chart", "draw_ranking_chart",
    "skill_chips", "skill_section",
    "ai_recommendation_panel",
    "feature_card", "architecture_table",
    "ranking_card",
    "swot_section", "recommendations_section",
]
