from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import requests
import io
import time
import re

app = FastAPI(title="LeetCode Rankings API")

# Extract username from LeetCode profile URL
def extract_username(url: str):
    match = re.search(r'leetcode\.com/([^/]+)/?', url.strip())
    return match.group(1) if match else None

# Fetch data from LeetScan API with retries
def fetch_user_data(username: str, retries=3, delay=1.0):
    url = f"https://leetscan.vercel.app/{username}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        time.sleep(delay)
    return None

@app.post("/upload/")
async def process_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df_input = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        return {"error": f"Could not read Excel file: {e}"}

    if 'profile_url' not in df_input.columns:
        return {"error": "Excel must contain a 'profile_url' column."}

    results = []
    failed_users = []

    for url in df_input['profile_url'].dropna().unique():
        username = extract_username(str(url))
        if not username:
            failed_users.append(url)
            continue

        data = fetch_user_data(username)
        if data:
            results.append({
                'username': username,
                'profile_url': url,
                'totalSolved': data.get('totalSolved', 0),
                'easySolved': data.get('easySolved', 0),
                'mediumSolved': data.get('mediumSolved', 0),
                'hardSolved': data.get('hardSolved', 0),
            })
        else:
            results.append({
                'username': username,
                'profile_url': url,
                'totalSolved': 'N/A',
                'easySolved': 'N/A',
                'mediumSolved': 'N/A',
                'hardSolved': 'N/A',
            })
            failed_users.append(url)

    df_result = pd.DataFrame(results)

    df_numeric = df_result[df_result['totalSolved'] != 'N/A'].copy()
    df_numeric['totalSolved'] = pd.to_numeric(df_numeric['totalSolved'], errors='coerce')
    df_numeric['Rank'] = df_numeric['totalSolved'].rank(ascending=False, method='min').astype('Int64')

    df_final = pd.merge(df_result, df_numeric[['username', 'Rank']], on='username', how='left')
    df_final = df_final.sort_values(by='Rank', na_position='last')

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='LeetCode Rankings')
        if failed_users:
            pd.DataFrame({'Failed URLs': failed_users}).to_excel(writer, index=False, sheet_name='Failures')
    output.seek(0)

    return StreamingResponse(output,
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=leetcode_rankings.xlsx"})
