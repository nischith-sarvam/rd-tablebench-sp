import aiofiles
import asyncio
from azure.storage.filedatalake.aio import (
    DataLakeDirectoryClient,
    FileSystemClient,
)
from azure.storage.filedatalake import ContentSettings
import base64
import json
import mimetypes
import os
import requests
import time
from urllib.parse import urlparse

'''
This script is to uplad a file from local system to Blob Storage that will help in API testing.
Change the file name in the botttom of the PDF and run when you need to
You need to input URL too.
'''
import dotenv
dotenv.load_dotenv()

async def main():
    input_folder = "data/tester"
    output_folder = "data/sarvam-parse-large-htmls"
    await parse_pdfs(input_folder=input_folder,
                     output_folder=output_folder,
                     parse_mode="small", # Choose between small "small" and "large" mode for parse
                     multipage=False) # Set this to if your pdf has multiple pages

class SarvamJobHandler:
    BASE_URL = "https://api.sarvam.ai/parse"

    def __init__(self):
        """
        Initializes the SarvamJobHandler with the given subscription key.
        Args:
            subscription_key (str): API subscription key.
        """
        self.subscription_key = os.getenv('SARVAM_SUBSCRIPTION_KEY')
        print(f"using subscription key: {self.subscription_key}")
        if not self.subscription_key:
            raise EnvironmentError("Environment variable 'SUBSCRIPTION_KEY' is not set.")

    def initialise_job(self):
        """
        Initializes a new job by sending a POST request.
        Returns:
            dict: Response data containing job details.
        """
        INIT_URL = f"{self.BASE_URL}/job/init"
        headers = {
            'API-Subscription-Key': self.subscription_key
        }
        try:
            response = requests.request("POST", INIT_URL, headers=headers)
            response_data = response.json()
            #print(f"response data: {response_data}")
        except Exception as e:
           print(f"Error occurred while trying to initialize job: {e}")
           exit()
        
        return response_data

    def start_job(self, job_id, file_details, parse_mode="large",):
        """
        Starts a job with the given parameters by sending a POST request.
        Args:
            job_id (str): ID of the job.
            file_details list[dict]: Dictionary with local file path and corresponding start_page and end_page.
        
        Returns:
            dict: Response data from the server.
        """
        START_JOB_URL = f"{self.BASE_URL}/job"
        headers = {
            'API-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }

        payload = {
            "job_id": job_id,
            "job_parameters": {
                "file_intervals": file_details,
                "receiver_email": "",
                "sarvam_mode": parse_mode
            }
        }

        try:
            print("trying to get job")
            response = requests.request("POST", START_JOB_URL, headers=headers, json=payload)
            response_data = response.json()
            print("Job started successfully:", json.dumps(response_data, indent=2))
        except Exception as e:
            print(f"Error occurred while trying to start job: {e}")
            response_data = {}
        
        return response_data

    def get_job_status(self, job_id, polling_interval=45):
        """
        Periodically checks the status of a job until it is completed.
        Args:
            job_id (str): ID of the job to check.
            polling_interval (int): Interval between status checks (default is 5 seconds).
        
        Returns:
            dict: Final response data when the job is completed.
        """
        headers = {
            'API-Subscription-Key': self.subscription_key
        }

        while True:
            url = f"{self.BASE_URL}/job/{job_id}/status"
            try:
                response = requests.request("GET", url, headers=headers)
                response_data = response.json()
                
                job_state = response_data.get('job_state')
                #print("Response:", json.dumps(response_data, indent=2))
                print(f"Current Job State: {job_state}")
                
                if job_state == 'Completed':
                    print("Job has been completed.")
                    return response_data
                elif job_state == 'Failed':
                    print(f"Job failed")
                    return response_data

            except Exception as e:
                print(f"Error occurred while checking job status: {e}")
            
            time.sleep(polling_interval)

class SarvamClient:
    def __init__(self, url: str):
        # Extract components from the provided URL
        self.account_url, self.file_system_name, self.directory_name, self.sas_token = (
            self._extract_url_components(url)
        )
        self.lock = asyncio.Lock()

    def update_url(self, url: str):
        self.account_url, self.file_system_name, self.directory_name, self.sas_token = (
            self._extract_url_components(url)
        )

    def _extract_url_components(self, url: str):
        """
        Extracts the components from the Azure Data Lake URL.
        """
        # Parse the URL
        parsed_url = urlparse(url)

        # Construct the account URL and replace blob with dfs for the Data Lake URL
        account_url = f"{parsed_url.scheme}://{parsed_url.netloc}".replace(
            ".blob.", ".dfs."
        )

        # Split the path to get the file system and directory
        path_components = parsed_url.path.strip("/").split("/")
        file_system_name = path_components[0]
        directory_name = "/".join(path_components[1:])
        sas_token = parsed_url.query
        return account_url, file_system_name, directory_name, sas_token

    async def upload_files(self, local_file_paths, overwrite=True):
        """
        Upload multiple files to the directory extracted from the URL.
        """
        async with DataLakeDirectoryClient(
            account_url=f"{self.account_url}?{self.sas_token}",
            file_system_name=self.file_system_name,
            directory_name=self.directory_name,
            credential=None,
        ) as directory_client:
            tasks = []
            for local_file_path in local_file_paths:
                file_name = local_file_path.split("/")[
                    -1
                ]  # Use the file name from the local path
                tasks.append(
                    self._upload_file(
                        directory_client, local_file_path, file_name, overwrite
                    )
                )

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _upload_file(
        self, directory_client, local_file_path, file_name, overwrite=True
    ):
        """
        Helper method to upload a single file.
        """
        try:
            async with aiofiles.open(local_file_path, mode="rb") as file_data:
                mime_type, _ = mimetypes.guess_type(local_file_path)
                if mime_type is None:
                    mime_type = "audio/wav"
                file_client = directory_client.get_file_client(file_name)
                await file_client.upload_data(
                    file_data,
                    overwrite=overwrite,
                    content_settings=ContentSettings(content_type=mime_type),
                )
                print(f"File '{file_name}' uploaded successfully!")
        except Exception as e:
            print(f"Failed to upload '{file_name}': {e}")

    async def list_files(self):
        """
        Return a list of file names (not full paths) in the directory extracted from the URL, protected with a lock.
        """
        file_names = []
        async with FileSystemClient(
            account_url=f"{self.account_url}?{self.sas_token}",
            file_system_name=self.file_system_name,
            credential=None,
        ) as file_system_client:
            async for path in file_system_client.get_paths(self.directory_name):
                file_name = path.name.split("/")[
                    -1
                ]  # Extract the last part of the path (file name)
                async with self.lock:  # Acquire lock before modifying file_names
                    file_names.append(file_name)
        return file_names

    async def download_files(self, file_names, destination_dir):
        """
        Download files from the directory extracted from the URL to a local directory.
        """
        os.makedirs(destination_dir, exist_ok=True)
        destination_dir.rsplit("/")[-1]
        async with DataLakeDirectoryClient(
            account_url=f"{self.account_url}?{self.sas_token}",
            file_system_name=self.file_system_name,
            directory_name=self.directory_name,
            credential=None,
        ) as directory_client:
            tasks = []
            for file_name in file_names:
                tasks.append(
                    self._download_file(directory_client, file_name, destination_dir)
                )

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_file(self, directory_client, file_name, destination_dir):
        """
        Helper method to download a single file.
        """
        try:
            file_client = directory_client.get_file_client(file_name)
            download_path = f"{destination_dir}/{file_name}"
            async with aiofiles.open(download_path, mode="wb") as file_data:
                stream = await file_client.download_file()
                data = await stream.readall()
                await file_data.write(data)
            print(f"File '{file_name}' downloaded successfully to '{download_path}'!")
        except Exception as e:
            print(f"Failed to download '{file_name}': {e}")

    async def delete_files(self, file_names):
        """
        Delete files from the directory extracted from the URL.
        """
        async with DataLakeDirectoryClient(
            account_url=f"{self.account_url}?{self.sas_token}",
            file_system_name=self.file_system_name,
            directory_name=self.directory_name,
            credential=None,
        ) as directory_client:
            tasks = []
            for file_name in file_names:
                tasks.append(self._delete_file(directory_client, file_name))

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _delete_file(self, directory_client, file_name):
        """
        Helper method to delete a single file.
        """
        try:
            file_client = directory_client.get_file_client(file_name)
            await file_client.delete_file()
            print(f"File '{file_name}' deleted successfully!")
        except Exception as e:
            print(f"Failed to delete '{file_name}': {e}")


def get_file_details(pdf_file_path: str):
    import PyPDF2
    """
    Open pdf file and create file details dictionary

    Returns:
        list: A list of dictionaries, each containing file details.
    """
    file_paths = []
    file_details = []

    # extract file name from path
    file_name = pdf_file_path.split("/")[-1]
    #open pdf file to get number of pages using pypdf
    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        if num_pages > 0:
            try:
                start_page = 1
                end_page = num_pages

                file_paths.append(pdf_file_path)
                file_details.append({
                    "file_name": file_name.split("/")[-1],
                    "page_intervals": [
                        {
                            "start_page": start_page,
                            "end_page": end_page
                        }
                    ]
                })
            except ValueError:
                print("Invalid input! Please enter numeric values for start and end pages.")
    
    return file_paths, file_details

def convert_to_html(input_dir: str, output_dir: str, current_filename: str, multipage: bool = False):

    os.makedirs(output_dir, exist_ok=True)

    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('.json'):
            # Extract the number from the filename (e.g., 0-1 from 0-1.json)
            file_number = filename.split('.')[0]
            
            with open(os.path.join(input_dir, filename), 'r') as json_file:
                data = json.load(json_file)
            
            html_content = base64.b64decode(data['output']).decode('utf-8')
            if multipage:
                output_filename = f'{current_filename}_{file_number.split("-")[1]}.html'
            else:
                output_filename = f'{current_filename}.html'
            
            # Write HTML file
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as html_file:
                html_file.write(html_content)

    print(f"Converted {len(os.listdir(input_dir))} JSON files to HTML in {output_dir}")
    return

async def parse_pdfs(input_folder: str, output_folder: str, parse_mode: str = "large", multipage: bool = False):

    folder_path = input_folder
    # temp storage path for data
    temp_storage_path = f"./temp_storage_{parse_mode}"
    os.makedirs(temp_storage_path, exist_ok=True)
    # for each pdf file in the folder, run the job
    for file in os.listdir(folder_path):
        if file.endswith('.pdf'):
            # get file name without extension
            # filename can have multiple . , just remove the last split
            file_name = '.'.join(file.split('.')[:-1])
            # Initialise job
            sarvam_handler = SarvamJobHandler()
            job_data = sarvam_handler.initialise_job()

            job_id = job_data.get('job_id')
            print(f"Extracted job id: {job_id}")
            if job_id is None:
                exit()
            
            # pass path of pdf file
            local_file_paths, file_details = get_file_details(os.path.join(folder_path, file))
            # Upload files to storage
            client = SarvamClient(job_data.get('input_storage_path'))
            await client.upload_files(
                local_file_paths,
                overwrite=True,
            )
            print(await client.list_files())

            # Start the job
            sarvam_handler.start_job(job_id, file_details, parse_mode)

            # Check job status
            final_status = sarvam_handler.get_job_status(job_id)
            print("Final Job Status:", json.dumps(final_status, indent=2))

            if final_status.get('job_state') == 'Completed':
                # Download the jsons
                client.update_url(url=job_data.get('output_storage_path'))
                files = await client.list_files()
                await client.download_files(file_names=files, destination_dir=f"{temp_storage_path}/data_{file_name}")

                # Convert downloaded files to HTML
                input_dir = f'{temp_storage_path}/data_{file_name}'
                convert_to_html(input_dir, output_folder, file_name, multipage)
# Run the example
asyncio.run(main())