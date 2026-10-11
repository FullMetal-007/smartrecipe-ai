"""Typed contracts shared by retrieval, Gemini, validation, and UI."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

class RecipeCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    minutes: int = 0
    ingredients: List[str] = Field(default_factory=list)
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    calories: Optional[float] = None
    protein: Optional[float] = None
    average_rating: Optional[float] = None
    baseline_rank: int = 0
    baseline_similarity_score: Optional[float] = None
    local_suitability_score: Optional[float] = None
    local_score_breakdown: Dict[str, float] = Field(default_factory=dict)
    local_reasons: List[str] = Field(default_factory=list)

    @property
    def recipe_id(self) -> str:
        # Name-derived identifier keeps candidate identity stable without altering the dataset.
        import hashlib, re
        slug = re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")[:48]
        suffix = hashlib.sha1(self.name.lower().strip().encode("utf-8")).hexdigest()[:8]
        return f"{slug}_{suffix}"

class CandidateEvaluation(BaseModel):
    recipe_id: str
    recipe_name: str
    ingredient_match_score: float = Field(ge=0, le=100)
    intent_match_score: float = Field(ge=0, le=100)
    constraint_match_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    missing_ingredients: List[str] = Field(default_factory=list)
    constraint_violations: List[str] = Field(default_factory=list)
    reason: str

class AIRankingResponse(BaseModel):
    selected_recipe_id: str
    candidate_evaluations: List[CandidateEvaluation]
    final_reason: str

    @property
    def selected_recipe(self) -> str:
        for item in self.candidate_evaluations:
            if item.recipe_id == self.selected_recipe_id:
                return item.recipe_name
        return self.selected_recipe_id

class ParsedRequirements(BaseModel):
    raw_query: str
    max_cooking_minutes: Optional[int] = None
    required_ingredients: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    meal_type: Optional[str] = None
    servings: Optional[int] = None
    cuisine_style: Optional[str] = None
    other_constraints: List[str] = Field(default_factory=list)

class ValidationResult(BaseModel):
    valid: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    selected_recipe_id: Optional[str] = None

class ExperimentRecord(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_query: str
    parsed_requirements: Dict[str, Any] = Field(default_factory=dict)
    candidate_names: List[str] = Field(default_factory=list)
    baseline_top_pick: str = ""
    baseline_retrieval_latency_s: float = 0.0
    ai_provider: str = ""
    ai_model: str = ""
    prompt_version: str = ""
    config_version: str = ""
    ai_selected_recipe: str = ""
    ai_scores: List[Dict[str, Any]] = Field(default_factory=list)
    final_reason: str = ""
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    correction_required: bool = False
    correction_succeeded: Optional[bool] = None
    api_calls: int = 0
    ai_latency_s: float = 0.0
    total_latency_s: float = 0.0
    cache_hit: bool = False
    final_recommendation: str = ""
    selection_changed_from_baseline: bool = False


class RecipeEnrichment(BaseModel):
    """AI generated practical recipe card for one baseline retrieved recipe."""
    recipe_id: str
    recipe_name: str
    short_description: str = Field(description="One short sentence describing the dish")
    difficulty_estimate: str = Field(description="Easy, Moderate, Challenging, or Unknown; this is an estimate")
    cooking_steps: List[str] = Field(description="Three or four concise practical suggested steps based on supplied name and ingredients; not original source instructions")
    additional_ingredients: List[str] = Field(default_factory=list, description="Optional ingredients suggested by AI that are not listed in the dataset; never mix these into source ingredients")
    missing_ingredients: List[str] = Field(default_factory=list, description="User requested ingredients missing from the source recipe, when clear")
    practical_tip: str = Field(description="One short useful cooking tip")
    warnings: List[str] = Field(default_factory=list, description="Only important caveats supported by supplied data; no generic warning spam")

class RecipeEnrichmentResponse(BaseModel):
    """Practical AI generated recipe cards for all baseline candidates in the original order."""
    recipes: List[RecipeEnrichment]
