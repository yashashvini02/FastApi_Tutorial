from fastapi import FastAPI, HTTPException
from typing import List
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hi there!"}
@app.get("/about/{id}")
def about(id: int, name: str = "Yashashvini"):
    return {"Name": name, "id": id}


