from backend.schemas import RecipeEnrichment, RecipeEnrichmentResponse

def make_item(recipe_id, recipe_name, difficulty="Easy"):
    return RecipeEnrichment(
        recipe_id=recipe_id,
        recipe_name=recipe_name,
        short_description="A simple home cooked dish.",
        difficulty_estimate=difficulty,
        cooking_steps=[
            "Prepare the listed ingredients.",
            "Cook the ingredients using a suitable method for this dish.",
            "Check that the food is cooked through and serve.",
        ],
        additional_ingredients=[],
        missing_ingredients=[],
        practical_tip="Prepare the ingredients before you begin.",
        warnings=[],
    )

def test_enrichment_schema_has_no_selection_field():
    schema = RecipeEnrichmentResponse.model_json_schema()
    assert "recipes" in schema["properties"]
    assert "selected_recipe_id" not in schema["properties"]

def test_difficulty_is_text_estimate():
    item = make_item("r1", "Egg salad")
    assert item.difficulty_estimate == "Easy"
    assert len(item.cooking_steps) == 3

def test_enrichment_response_preserves_items():
    response = RecipeEnrichmentResponse(recipes=[
        make_item("r1", "A"),
        make_item("r2", "B", "Unknown"),
    ])
    assert [r.recipe_id for r in response.recipes] == ["r1", "r2"]

def test_ranking_and_enrichment_prompts_are_separate_and_versioned():
    from pathlib import Path
    root = Path(__file__).resolve().parent
    assert (root / "backend" / "prompts" / "ai_ranking_v1.txt").is_file()
    assert (root / "backend" / "prompts" / "enrichment_v1.txt").is_file()
    assert (root / "backend" / "prompts" / "correction_v1.txt").is_file()
