import requests
import base64
import os
import aiohttp
import asyncio
import platform
from concurrent.futures import ThreadPoolExecutor

year = 2020
def get_token():
    ZOOM_ACCOUNT_ID=''
    ZOOM_CLIENT_ID=''
    ZOOM_CLIENT_SECRET=''
    url = f'https://api.zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}'
    zoom_combined = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
    encoded = base64.b64encode(zoom_combined.encode("utf-8") )
    print(encoded.decode("utf-8"))
    headers = {"Authorization": f"Basic {encoded.decode("utf-8")}"}
    response = requests.post(url, headers=headers)
    print(response.text)
    token = response.json().get('access_token')
    return token
async def get_recordings(token, year):
    url = "https://api.zoom.us/v2/users/me/recordings"
    headers = {"Authorization": f"Bearer {token}"}
# Define the year you want to search for recordings 

    for month in range(1, 13):  # Loop through months 1 to 12
        # Calculate the start and end dates for each month
        start_date = f"{year}-{month:02d}-01"  # Format month as 2-digit
        next_month = month % 12 + 1 if month != 12 else 1  # Handle December
        end_date = f"{year}-{next_month:02d}-30"  # Start of the next month

        # Make the API request for each month's recordings
        params = {
            "from": start_date,
            "to": end_date
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            recordings_data = response.json()
            print(f"Recordings for {start_date} to {end_date}:")
            
            for meeting in recordings_data.get('meetings', []):
                print(meeting)
                recording_files = meeting.get('recording_files', [])
                count_mp3 = 1
                count_mp4 = 1
                tasks = []  # List to hold asynchronous download tasks

                for file in recording_files:
                    
                    download_url = file.get('download_url', 'N/A')
                    print(f"Meeting ID: {meeting['id']} - Download URL: {download_url}")
                    file_type = file.get('file_type')
                    task = download_video_async(meeting.get('topic'), token, download_url, count_mp3, count_mp4, file_type)
                    tasks.append(task)
                    if file_type == 'M4A':
                        count_mp3 += 1
                    if file_type == 'MP4':
                        count_mp4 += 1
                # Run all download tasks asynchronously
                await asyncio.gather(*tasks)

                
        else:
            print(f"Failed for {start_date} to {end_date} - Status code: {response.status_code}")

async def delete_recordings(token, year):
    url = "https://api.zoom.us/v2/users/me/recordings"
    headers = {"Authorization": f"Bearer {token}"}
# Define the year you want to search for recordings
    async with aiohttp.ClientSession(headers=headers) as session:
        for month in range(1, 13):
            start_date = f"{year}-{month:02d}-01"
            next_month = month % 12 + 1 if month != 12 else 1
            end_date = f"{year}-{next_month:02d}-30"

            params = {
                "from": start_date,
                "to": end_date
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    recordings_data = await response.json()
                    print(f"Recordings for {start_date} to {end_date}:")
                    
                    for meeting in recordings_data.get('meetings', []):
                        print(meeting)
                        encoded_uuid = meeting.get('uuid')
                        delete_url = f"https://api.zoom.us/v2/meetings/{encoded_uuid}/recordings"
                        async with session.delete(delete_url) as delete_response:
                            if delete_response.status == 204:
                                print(f"Recording deleted: {delete_url}")
                            else:
                                print(f"Failed to delete recording: {delete_url} - Status code: {delete_response.status}")
                else:
                    print(f"Failed for {start_date} to {end_date} - Status code: {response.status}")


async def download_video_async(topic, token, download_url, count_mp3, count_mp4, file_type, year):
    try:
        user_agent = f"Mozilla/5.0 (Windows NT {platform.release()}; {platform.machine()}; rv:85.0) Gecko/20100101 Firefox/85.0"
        count=0
        headers = {
            'User-Agent': user_agent,
            "Authorization": f"Bearer {token}"}
        topic = topic.replace('/', ' ')
        file_path = ''
        print(file_type)
        if file_type == 'M4A':
            count = count_mp3
            directory = f'D:/Archive/Zoom/Audio/{year}/'
            file_extension = '.mp3'
        elif file_type == 'MP4':
            count = count_mp4
            directory = 'D:/Archive/Zoom/Video/{year}/'
            file_extension = '.mp4'
        else:
            return None

        while True:
            if count > 1:
                file_path = f'{directory}{topic}-{count}{file_extension}'
            else:
                file_path = f'{directory}{topic}{file_extension}'

            if not os.path.exists(file_path):
                break

            count += 1

        def blocking_download():
                response = requests.get(download_url, headers=headers)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                        print("File Saved to " + file_path)
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, blocking_download)
    except Exception as e:
        print(topic + "Faild To Download" + str(e))
        pass
async def main(token):
    await delete_recordings(token, year)
asyncio.run(main(get_token()))
