"""Lightweight deterministic extraction for common recipe constraints.

This parser supports the UI and validator only. The baseline retrieval query remains
the user's original natural language text and its ranking algorithm is unchanged.
"""
import re
from backend.schemas import ParsedRequirements

INGREDIENT_ALIASES = {
    "chicken": ["chicken"], "beef": ["beef"], "pork": ["pork"], "fish": ["fish"],
    "rice": ["rice"], "pasta": ["pasta", "spaghetti", "macaroni"],
    "potato": ["potato", "potatoes"], "tomato": ["tomato", "tomatoes"],
    "spinach": ["spinach"], "cheese": ["cheese", "cheddar", "mozzarella", "parmesan"],
    "egg": ["egg", "eggs"], "carrot": ["carrot", "carrots"],
    "onion": ["onion", "onions"], "garlic": ["garlic"],
    "mushroom": ["mushroom", "mushrooms"], "tofu": ["tofu"], "broccoli": ["broccoli"],
    "avocado": ["avocado", "avocados"], "lemon": ["lemon", "lemons"],
    "salmon": ["salmon"], "tuna": ["tuna"], "shrimp": ["shrimp", "prawn", "prawns"],
    "noodle": ["noodle", "noodles"], "bean": ["bean", "beans"],
    "lentil": ["lentil", "lentils"], "quinoa": ["quinoa"],
    "cucumber": ["cucumber", "cucumbers"], "zucchini": ["zucchini", "courgette", "courgettes"],
    "eggplant": ["eggplant", "aubergine", "aubergines"], "corn": ["corn"],
    "pepper": ["pepper", "peppers"], "basil": ["basil"],
    "oregano": ["oregano"], "ginger": ["ginger"], "soy sauce": ["soy sauce", "soya sauce"],
    "butter": ["butter"], "milk": ["milk"], "cream": ["cream"],
    "lettuce": ["lettuce"], "cabbage": ["cabbage"], "peas": ["peas", "pea"],
    "cauliflower": ["cauliflower"], "sweet potato": ["sweet potato", "sweet potatoes"],
    "bell pepper": ["bell pepper", "capsicum"], "chili": ["chili", "chilli"],
    "coriander": ["coriander", "cilantro"], "parsley": ["parsley"], "mint": ["mint"],
    "coconut milk": ["coconut milk"], "cream cheese": ["cream cheese"],
    "ground beef": ["ground beef", "minced beef"], "turkey": ["turkey"],
    "chicken stock": ["chicken stock", "chicken broth"], "beef stock": ["beef stock", "beef broth"],
    "fish sauce": ["fish sauce"], "egg noodles": ["egg noodles", "egg noodle"],
    "chickpea": ["chickpea", "chickpeas", "garbanzo beans"],
    "black bean": ["black bean", "black beans"], "kidney bean": ["kidney bean", "kidney beans"],
    "lentil": ["lentil", "lentils"], "apple": ["apple", "apples"], "banana": ["banana", "bananas"],
    "strawberry": ["strawberry", "strawberries"], "peanut": ["peanut", "peanuts"],
    "almond": ["almond", "almonds"], "walnut": ["walnut", "walnuts"],
    "sesame oil": ["sesame oil"], "vinegar": ["vinegar"], "honey": ["honey"],
    "soybean": ["soybean", "edamame"], "toor dal": ["toor dal", "pigeon pea"],
    "yogurt": ["yogurt", "yoghurt"], "bread": ["bread"], "oats": ["oats", "oatmeal"],
}

def _has_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))

def parse_requirements(query: str) -> ParsedRequirements:
    q = query.lower()
    m = re.search(r"(?:under|less than|within|at most|maximum|max)\s*(\d+)\s*(?:minutes?|mins?)", q)
    if not m:
        m = re.search(r"\b(\d+)\s*(?:minute|minutes|min|mins)\b", q)
    minutes = int(m.group(1)) if m else (30 if any(x in q for x in ("quick", "fast", "rapid")) else None)

    sm = re.search(r"\b(?:for|serves?|servings?)\s+(\d+)\s*(?:people|person|persons)?\b", q)
    if not sm:
        word_numbers = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        sm = re.search(r"\b(?:for|serves?|servings?)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:people|person|persons)?\b", q)

    diets = []
    for phrase, key in [("vegetarian", "vegetarian"), ("vegan", "vegan"), ("gluten free", "gluten-free"), ("gluten-free", "gluten-free"), ("dairy free", "dairy-free"), ("dairy-free", "dairy-free"), ("high protein", "high-protein"), ("high-protein", "high-protein"), ("low carb", "low-carb"), ("low-carb", "low-carb"), ("keto", "keto")]:
        if phrase in q and key not in diets:
            diets.append(key)

    # Resolve overlapping phrases by preferring the longest matching ingredient
    # phrase at the same text span (e.g. "bell pepper" over "pepper", and
    # "chicken stock" over "chicken"). This prevents one phrase becoming two
    # separate mandatory ingredients.
    ingredient_matches = []
    for canonical, aliases in INGREDIENT_ALIASES.items():
        for alias in aliases:
            for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", q):
                ingredient_matches.append((match.start(), match.end(), canonical, alias))
    ingredient_matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected_matches = []
    for candidate_match in ingredient_matches:
        start, end, canonical, alias = candidate_match
        overlapping = [i for i, item in enumerate(selected_matches) if start < item[1] and item[0] < end]
        if not overlapping:
            selected_matches.append(candidate_match)
        elif all((end - start) > (selected_matches[i][1] - selected_matches[i][0]) for i in overlapping):
            for i in reversed(overlapping):
                selected_matches.pop(i)
            selected_matches.append(candidate_match)
    ingredients = []
    for _, _, canonical, _ in sorted(selected_matches, key=lambda item: item[0]):
        if canonical not in ingredients:
            ingredients.append(canonical)
    meal = next((x for x in ["breakfast", "lunch", "dinner", "snack", "dessert", "appetizer", "soup", "salad"] if x in q), None)
    cuisine = next((x for x in ["asian", "italian", "mexican", "chinese", "thai", "indian", "japanese", "mediterranean", "french"] if x in q), None)
    servings = None
    if sm:
        token = sm.group(1)
        servings = int(token) if token.isdigit() else {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}[token]

    return ParsedRequirements(raw_query=query, max_cooking_minutes=minutes, required_ingredients=ingredients, dietary_preferences=diets, meal_type=meal, servings=servings, cuisine_style=cuisine)
