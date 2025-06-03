from fastapi import FastAPI, HTTPException
from typing import List

app = FastAPI()

list1 = ["Yashashvini", "Harini", "Harshitha"]

@app.get("/")
def root():
    return {"message": "Hi there!"}

@app.put("/Details/{id}/{name}")
def update_name(id: int, name: str):
    if id < 0 or id >= len(list1):
        raise HTTPException(status_code=404, detail="ID out of range")
    list1[id] = name
    return {"message": "Successfully updated", "updated_list": list1}
@app.post("/Details/{name}")
def addn_name(name:str):
   
    list1.append(name)
    return {"message":"Successfully added!"}
@app.get("/Details")
def root1():
    return {"all_names":list1}
    

