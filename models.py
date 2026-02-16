from sqlalchemy import Column, Integer, String, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database import Base

class Recipe(Base):
    __tablename__ = 'recipes'

    # Fixed: Added the underscore to primary_key
    recipeID = Column(Integer, primary_key=True, index=True) 
    rawImage = Column(LargeBinary) 
    
    ingredientList = relationship("Ingredient", back_populates="recipe") 

class Ingredient(Base):
    __tablename__ = 'ingredients'

    # Fixed: Added the underscore to primary_key
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey('recipes.recipeID'))
    
    name = Column(String, index=True) 
    quantity = Column(Float) 
    unit = Column(String) 
    confidenceScore = Column(Float) 

    recipe = relationship("Recipe", back_populates="ingredientList")