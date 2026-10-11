from backend.input_processor import parse_requirements

def test_plural_eggs_are_detected():
    result = parse_requirements("I have eggs, spinach and tomatoes. Suggest a quick dinner for two under 30 minutes.")
    assert "egg" in result.required_ingredients
    assert "spinach" in result.required_ingredients
    assert "tomato" in result.required_ingredients
    assert result.max_cooking_minutes == 30
    assert result.servings == 2
    assert result.meal_type == "dinner"

def test_chicken_and_cuisine_are_detected():
    result = parse_requirements("I have chicken and rice and want an Indian dinner under 40 minutes.")
    assert "chicken" in result.required_ingredients
    assert "rice" in result.required_ingredients
    assert result.cuisine_style == "indian"
    assert result.max_cooking_minutes == 40

def test_dietary_preferences_are_detected():
    result = parse_requirements("Make a vegetarian high protein meal for four.")
    assert "vegetarian" in result.dietary_preferences
    assert "high-protein" in result.dietary_preferences
    assert result.servings == 4

def test_overlapping_compound_ingredients_are_not_double_counted():
    result = parse_requirements("I have bell pepper, ground beef, cream cheese and chicken stock.")
    assert result.required_ingredients == ["bell pepper", "ground beef", "cream cheese", "chicken stock"]

def test_easy_preference_does_not_invent_a_hard_time_limit():
    result = parse_requirements("I have chicken and eggs and want something easy to prepare.")
    assert result.max_cooking_minutes is None
    assert "chicken" in result.required_ingredients
    assert "egg" in result.required_ingredients
