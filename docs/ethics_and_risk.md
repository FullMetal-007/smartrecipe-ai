# Ethics, safety and responsible use

## Position

SmartRecipe AI is a convenience prototype, not a medical nutrition service or certified allergen checker. It should communicate uncertainty, avoid unsupported health claims, and keep users in control of food choices.

## Principle 1: Privacy and data governance

The app processes free-text requests that may reveal dietary practices, health goals, household routines, or allergy concerns. By default, the app does not require an account. Experiment logs are local JSONL files and should not contain API credentials. When Gemini is enabled, a compact request and candidate metadata are sent to the configured external provider; users should not enter identifying or highly sensitive details. `.env`, `.ai_cache`, and `logs/` are excluded from Git.

### Concrete lifecycle risks and controls

1. **Input collection:** a user includes a medical condition or personal detail in a request. **Control:** explain that requests are sent to an external model when AI is enabled, avoid requesting identity data, and use only the minimum query/candidate fields needed.
2. **Storage and development:** raw requests remain in local experiment logs or cache. **Control:** keep logs local and ignored by Git, provide a documented deletion step, and use synthetic test requests in demonstrations.
3. **Sharing and deployment:** a developer accidentally commits `.env` or uploads logs. **Control:** `.gitignore` excludes secrets and logs; review `git status` before pushing; rotate any exposed key immediately.

## Principle 2: Safety, accuracy and accountability

Recipe suggestions can be wrong, incomplete, or unsuitable. Dataset nutrition and cooking-time fields may be missing or inconsistent. AI generated steps are labelled as suggestions and are not represented as original source instructions.

### Concrete lifecycle risks and controls

1. **Ingredient matching:** a recipe title says “egg” but the source ingredient list omits egg. **Control:** only the dataset ingredient list satisfies a required ingredient; strict gate rejects the candidate.
2. **Diet/allergy claims:** text matching misses a hidden allergen or cross-contamination risk. **Control:** do not claim allergy-safe or medically suitable results; show a warning that text checks are not certification and require users to verify packaging and source information.
3. **Cooking guidance:** generated instructions omit a safe internal temperature or infer a method unsupported by the data. **Control:** constrain prompts to supplied recipe facts, validate recipe identity, include a 74°C reminder for raw poultry, and label all steps as AI suggestions.
4. **Conflicting requirements:** user asks for chicken and a vegan meal. **Control:** the deterministic constraint gate reports no valid recipe rather than suppressing one requirement or inventing a dish.

## Accountability

The baseline dataset is the source of truth for recipe name, ingredients, time, rating and nutrition when present. The AI provider is responsible only for its generated ranking rationale and cooking guidance. The application developer remains responsible for validation rules, logging, warnings, and not overstating the system's reliability. The live trace and experiment log make failures inspectable.

## Remaining limitations

- Ingredient parsing covers a curated set of common ingredients and can miss uncommon terms or interpret ambiguous words incorrectly.
- Dietary checks are text-based and cannot certify vegan, vegetarian, gluten-free, dairy-free, or allergy safety.
- Dataset recipe times, nutrition, and ratings are not independently verified.
- AI ranking and generated instructions may be inconsistent, and API access introduces external dependency and cost.
- The baseline candidate pool can fail to retrieve a suitable recipe even when one exists elsewhere in the full dataset.
