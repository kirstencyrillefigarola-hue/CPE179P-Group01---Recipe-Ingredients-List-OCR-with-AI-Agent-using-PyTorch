from sqlalchemy.orm import Session
import models

# --- CREATE OPERATIONS ---

def create_recipe(db: Session, raw_image_data: bytes):
    """Saves a new recipe image to the database."""
    db_recipe = models.Recipe(rawImage=raw_image_data)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

def create_ingredient(db: Session, recipe_id: int, name: str, quantity: float, unit: str, confidence: float):
    """Saves an extracted ingredient linked to a specific recipe."""
    db_ingredient = models.Ingredient(
        recipe_id=recipe_id,
        name=name,
        quantity=quantity,
        unit=unit,
        confidenceScore=confidence
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

# --- READ OPERATIONS ---

def get_recipe(db: Session, recipe_id: int):
    """Fetches a recipe and its ingredients by ID."""
    return db.query(models.Recipe).filter(models.Recipe.recipeID == recipe_id).first()

def get_ingredients_by_recipe(db: Session, recipe_id: int):
    """Fetches all ingredients for a specific recipe."""
    return db.query(models.Ingredient).filter(models.Ingredient.recipe_id == recipe_id).all()