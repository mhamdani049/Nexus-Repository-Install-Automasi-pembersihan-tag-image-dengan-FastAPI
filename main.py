from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    "NEXUS_URL": os.getenv("NEXUS_URL", "http://localhost:8081"),
    "USERNAME": os.getenv("NEXUS_USERNAME", "admin"),
    "PASSWORD": os.getenv("NEXUS_PASSWORD", "P@ssw0rd123XYZ"),
    "KEEP_TAGS": int(os.getenv("KEEP_TAGS", 10)),
    "REQUEST_TIMEOUT": 60,  # Timeout in seconds
    "POLL_INTERVAL": 5  # Interval antara polling dalam detik
}

app = FastAPI()

class CleanupRequest(BaseModel):
    keep_tags: Optional[int] = CONFIG['KEEP_TAGS']

def get_components(repo_name):
    all_components = []
    continuation_token = None

    while True:
        try:
            url = f"{CONFIG['NEXUS_URL']}/service/rest/v1/components?repository={repo_name}"
            if continuation_token:
                url += f"&continuationToken={continuation_token}"

            response = requests.get(
                url,
                auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']),
                timeout=CONFIG['REQUEST_TIMEOUT']
            )

            response.raise_for_status()
            data = response.json()
            all_components.extend(data.get('items', []))
            continuation_token = data.get('continuationToken')
            if not continuation_token:
                break
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail=f"Request to Nexus timed out while fetching components for {repo_name}.")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch components for {repo_name}: {str(e)}")

    return all_components

def delete_component(component_id):
    try:
        response = requests.delete(
            f"{CONFIG['NEXUS_URL']}/service/rest/v1/components/{component_id}",
            auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']),
            timeout=CONFIG['REQUEST_TIMEOUT']
        )

        if response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to delete component {component_id}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail=f"Request to Nexus timed out while deleting component {component_id}.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete component {component_id}: {str(e)}")

def get_repositories():
    try:
        response = requests.get(
            f"{CONFIG['NEXUS_URL']}/service/rest/v1/repositories",
            auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']),
            timeout=CONFIG['REQUEST_TIMEOUT']
        )

        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to Nexus timed out while fetching repositories.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

def get_tasks():
    try:
        response = requests.get(
            f"{CONFIG['NEXUS_URL']}/service/rest/v1/tasks",
            auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']),
            headers={
                "accept": "application/json",
                "X-Nexus-UI": "true"
            },
            timeout=CONFIG['REQUEST_TIMEOUT']
        )
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

def run_nexus_task(task_name: str):
    print(f"Fetching tasks from Nexus to find task: {task_name}")
    tasks = get_tasks()
    task = next((t for t in tasks if t['name'] == task_name), None)
    if not task:
        msg = f"Task '{task_name}' not found"
        print(msg)
        raise HTTPException(status_code=404, detail=msg)
    task_id = task['id']

    print(f"Running task '{task_name}' with ID {task_id}...")
    try:
        run_response = requests.post(
            f"{CONFIG['NEXUS_URL']}/service/rest/v1/tasks/{task_id}/run",
            auth=(CONFIG['USERNAME'], CONFIG['PASSWORD']),
            timeout=CONFIG['REQUEST_TIMEOUT']
        )
        if run_response.status_code != 204:
            msg = f"Failed to run task '{task_name}', status code: {run_response.status_code}"
            print(msg)
            raise HTTPException(status_code=run_response.status_code, detail=msg)
        print(f"Task '{task_name}' started successfully.")
        return True
    except requests.exceptions.RequestException as e:
        msg = f"Failed to run task '{task_name}': {str(e)}"
        print(msg)
        raise HTTPException(status_code=500, detail=msg)

@app.get("/health")
def health_check():
    return {
        "status": "success",
        "message": "Service is running",
        "code": "00",
        "data": None
    }

@app.get("/repositories")
def list_repositories():
    repositories = get_repositories()
    return {
        "status": "success",
        "message": "Repositories retrieved successfully",
        "code": "00",
        "data": repositories
    }

@app.get("/repositories/{repository}/total-images")
def get_total_images(repository: str):
    try:
        components = get_components(repository)
        image_set = {component['name'].split('/')[-1] for component in components}

        return {
            "status": "success",
            "message": "Total images retrieved",
            "code": "00",
            "data": {
                "total_images": len(image_set),
                "repository": repository
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving total images: {str(e)}")

@app.post("/repositories/{repository}/cleanup-image-keep-new-tag")
def cleanup_tags(repository: str, request: CleanupRequest):
    keep_tags = request.keep_tags

    try:
        print(f"Processing repository: {repository}")
        components = get_components(repository)

        # Group images by name
        image_dict = {}
        for component in components:
            image_name = component['name'].split('/')[-1]
            image_dict.setdefault(image_name, []).append(component)

        result = {}
        for image_name, image_components in image_dict.items():
            print(f"\nProcessing image: {image_name}")

            # Sort tags by blobCreated or lastModified
            image_components.sort(key=lambda x: datetime.strptime(
                x['assets'][0].get('blobCreated', x['assets'][0]['lastModified']),
                '%Y-%m-%dT%H:%M:%S.%f%z'
            ), reverse=True)

            # Ambil digest dari tag yang ingin dipertahankan
            whitelist_digests = set()
            for comp in image_components[:keep_tags]:
                for asset in comp['assets']:
                    digest = asset.get('docker.image.manifest.digest')
                    if digest:
                        whitelist_digests.add(digest)

            # Tambahkan digest dari tag latest
            for comp in image_components:
                if comp['version'] == 'latest':
                    for asset in comp['assets']:
                        digest = asset.get('docker.image.manifest.digest')
                        if digest:
                            whitelist_digests.add(digest)

            # Filter komponen yang digest-nya tidak termasuk whitelist
            components_to_delete = []
            for comp in image_components[keep_tags:]:
                if comp['version'] == 'latest':
                    continue  # Jangan hapus tag latest
                should_delete = True
                for asset in comp['assets']:
                    digest = asset.get('docker.image.manifest.digest')
                    if digest in whitelist_digests:
                        should_delete = False
                        break
                if should_delete:
                    components_to_delete.append(comp)

            deleted_tags = []
            for comp in components_to_delete:
                delete_component(comp['id'])
                deleted_tags.append({
                    "version": comp['version'],
                    "id": comp['id'],
                    "blob_created": comp['assets'][0].get('blobCreated', 'N/A'),
                })

            result[image_name] = {
                "status": "cleaned" if deleted_tags else "skipped",
                "deleted_tags": deleted_tags,
                "total_deleted": len(deleted_tags)
            }

        print("Starting to run Nexus tasks sequentially...")
        if run_nexus_task("delete-unused-manifests-and-image-task"):
            print("First task completed, proceeding to second task.")
            run_nexus_task("compact-blob-store")
            print("Second task completed.")
        print("All tasks executed successfully.")

        return {
            "status": "success",
            "message": "Cleanup completed",
            "code": "00",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")
