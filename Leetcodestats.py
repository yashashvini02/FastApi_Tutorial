from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import requests
import io

app = FastAPI(title="LeetCode Rankings API")

# Fetch data from LeetScan
def fetch_user_data(username: str):
    url = f"https://leetscan.vercel.app/{username}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# Endpoint for processing Excel file
@app.post("/upload/")
async def process_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df_input = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        return {"error": f"Could not read Excel file: {e}"}

    if 'username' not in df_input.columns:
        return {"error": "Excel must contain a 'username' column."}

    results = []

    for username in df_input['username'].dropna():
        data = fetch_user_data(username)
        if data:
            results.append({
                'username': username,
                'totalSolved': data.get('totalSolved', 0),
                'easySolved': data.get('easySolved', 0),
                'mediumSolved': data.get('mediumSolved', 0),
                'hardSolved': data.get('hardSolved', 0),
            })
        else:
            results.append({
                'username': username,
                'totalSolved': 'N/A',
                'easySolved': 'N/A',
                'mediumSolved': 'N/A',
                'hardSolved': 'N/A',
            })

    df_result = pd.DataFrame(results)

    df_numeric = df_result[df_result['totalSolved'] != 'N/A'].copy()
    df_numeric['totalSolved'] = pd.to_numeric(df_numeric['totalSolved'])
    df_numeric['Rank'] = df_numeric['totalSolved'].rank(ascending=False, method='min').astype(int)

    df_final = pd.merge(df_result, df_numeric[['username', 'Rank']], on='username', how='left')
    df_final = df_final.sort_values(by='Rank', na_position='last')

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='LeetCode Rankings')
    output.seek(0)

    return StreamingResponse(output,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=leetcode_rankings.xlsx"})
