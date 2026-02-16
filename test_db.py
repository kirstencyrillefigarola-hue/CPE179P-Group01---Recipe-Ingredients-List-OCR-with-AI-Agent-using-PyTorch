import database
import models
import crud

# 1. Initialize the database and create the tables
print("Creating database tables...")
models.Base.metadata.create_all(bind=database.engine)

# 2. Open a database session
db = database.SessionLocal()

try:
    # 3. Create a dummy recipe
    print("\nAdding a dummy recipe...")
    # We use some fake byte data to simulate an uploaded image
    fake_image_bytes = b"fake_binary_image_data_for_testing" 
    new_recipe = crud.create_recipe(db=db, raw_image_data=fake_image_bytes)
    print(f"Success! Recipe created with ID: {new_recipe.recipeID}")

    # 4. Add dummy ingredients to that recipe
    print("Adding dummy ingredients...")
    crud.create_ingredient(
        db=db, recipe_id=new_recipe.recipeID, name="flour", quantity=2.0, unit="cups", confidence=0.98
    )
    crud.create_ingredient(
        db=db, recipe_id=new_recipe.recipeID, name="salt", quantity=1.0, unit="tsp", confidence=0.95
    )
    print("Ingredients added successfully.")

    # 5. Read the data back to verify the Read operations
    print("\n--- Verifying Data Retrieval ---")
    fetched_recipe = crud.get_recipe(db=db, recipe_id=new_recipe.recipeID)
    print(f"Fetched Recipe ID: {fetched_recipe.recipeID}")

    fetched_ingredients = crud.get_ingredients_by_recipe(db=db, recipe_id=new_recipe.recipeID)
    print(f"Found {len(fetched_ingredients)} ingredients:")
    for ing in fetched_ingredients:
        print(f" - {ing.quantity} {ing.unit} of {ing.name} (OCR Confidence: {ing.confidenceScore})")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # 6. Always close the database session when done
    db.close()
    print("\nTest run complete.")