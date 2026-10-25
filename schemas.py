from pydantic import BaseModel, Field

class IngredientEstimate(BaseModel):
    name: str; grams_low: float = Field(ge=0); grams_high: float = Field(ge=0); visible: bool = True; reason: str | None = None
class Recognition(BaseModel):
    is_food: bool; dish_name: str = ""; cuisine: str = ""; confidence: float = Field(default=0.6, ge=0, le=1); ingredients: list[IngredientEstimate] = []; hidden_ingredients: list[IngredientEstimate] = []; servings_estimate: int = Field(default=1, ge=1)
class Match(BaseModel):
    ingredient_name: str; fdc_id: str | None; grams_low: float = Field(ge=0); grams_high: float = Field(ge=0)
class SwapChange(BaseModel):
    from_: str = Field(default="ingredient", alias="from"); to: str = "updated amount"; why: str = "Supports the selected goal."
class SwapVersion(BaseModel):
    title: str = "Lighter version"; authenticity_note: str = "Keeps the dish recognizable."; changes: list[SwapChange] = []; new_ingredients: list[IngredientEstimate] = []; steps: list[str] = []; flavor_tradeoff: str = "A small flavor tradeoff."
class SwapResponse(BaseModel): versions: list[SwapVersion]
class RecipeRecommendation(BaseModel):
    recipe_id: str
    reason: str = "A recipe from the same ingredient orbit."
    shared_ingredients: list[str] = []
    health_angle: str = "A lighter direction to explore."
    interest_angle: str = "A fresh way to use familiar ingredients."
class RecipeRecommendationResponse(BaseModel): recommendations: list[RecipeRecommendation]
class CriticResult(BaseModel):
    accepted: bool; authenticity_score: int = Field(ge=1, le=5); reason: str; allergen_flags: list[str] = []; medical_claims: list[str] = []
