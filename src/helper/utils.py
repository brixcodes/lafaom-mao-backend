from fastapi import UploadFile
import os
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from pyfcm import FCMNotification
from src.config import settings
from src.helper.schemas import AccessTokenType
from src.helper.model import TokenData
import httpx
from src.database import get_session
from sqlmodel import select
from celery import shared_task
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError 
from fastapi import UploadFile
import re



def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\.]', '_', name)



async def upload_file_to_s3(file: UploadFile, location: str = "", name: str = "", public: bool = True):
    try:
        if file.size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds limit of {settings.MAX_FILE_SIZE} bytes")

        path = location.strip("/")
        date_time_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_split = os.path.splitext(file.filename)

        if not name:
            back_name = sanitize_filename(name_split[0]) 
            name = back_name + "_s3" + name_split[1]
        else:
            back_name = sanitize_filename(name)
            name = f"{back_name}_s3{name_split[1]}"

        full_path = f"{path}/{date_time_now}_{name}" if path else f"{date_time_now}_{name}"
        extra_args = { "ContentType": file.content_type }
        if public:
            full_path = f"public/{full_path}"
        else : 
            full_path = f"private/{full_path}"
            

        s3 = get_s3_client()
        await file.seek(0)  # Ensure file pointer is at start
        s3.upload_fileobj(file.file, settings.AWS_BUCKET_NAME, full_path, ExtraArgs=extra_args)

        public_url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{full_path}"

        return (public_url if public else full_path), back_name, file.content_type

    except NoCredentialsError:
        raise RuntimeError("AWS credentials are missing or invalid")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise RuntimeError(f"Bucket {settings.AWS_BUCKET_NAME} does not exist")
        raise RuntimeError(f"S3 upload failed: {str(e)}")
    except BotoCoreError as e:
        raise RuntimeError(f"S3 error: {str(e)}")


def delete_file_from_s3(key: str) -> bool:
    """
    Delete a file from an S3 bucket.

    Args:
        key (str): The S3 key (path) of the file to delete (e.g., 'folder/20250710_183045_example.txt').

    Returns:
        bool: True if the file was deleted successfully, False if the file was not found.

    Raises:
        RuntimeError: If AWS credentials are missing or another S3 error occurs.
    """
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=key.strip("/"))
        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return False  # File doesn't exist
        raise RuntimeError(f"Failed to delete file from S3: {str(e)}")
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found")
    except BotoCoreError as e:
        raise RuntimeError(f"S3 error: {str(e)}")

def get_public_file_url(key: str):
    return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def generate_presigned_url(key: str, expires_in: int = 3600):
    try:
        s3 = get_s3_client()
        return s3.generate_presigned_url(
            "get_object",
            {"Bucket": settings.AWS_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
        
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return None 
        raise RuntimeError(f"Could not generate presigned URL: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Could not generate presigned URL: {str(e)}")

async def upload_file(file: UploadFile, location: str = "", name: str = ""):
    if settings.STORAGE_LOCATION == "local":
        return await upload_file_local(file, location, name)
    else:
        return await upload_file_to_s3(file, location, name, public=True)


async def upload_private_file(file: UploadFile, location: str = "", name: str = ""):
    if settings.STORAGE_LOCATION == "local":
        return await upload_file_local(file, location, name)
    else:
        return await upload_file_to_s3(file, location, name, public=False)

def delete_file(file_path: str):
    if settings.STORAGE_LOCATION == "local":
        return delete_file_local(file_path)
    else:
        return delete_file_from_s3(file_path)


async def upload_file_local(file: UploadFile, location: str = "", name: str = ""):
    """
    This function is used to upload a file to the server. The file is saved
    in the src/static directory. If a location is provided, the file is saved
    in that location. If a name is provided, the file is saved with that name.
    Otherwise, the file is saved with the same name as the original file.

    Args:
        file (UploadFile): The file to be uploaded
        location (str): The location where the file should be saved
        name (str): The name with which the file should be saved

    Returns:
        A tuple containing the path of the saved file, the name of the saved
        file, and the content type of the file
    """
    try:
        path_save = "src/static/uploads"
        path_save = path_save + location

        if not os.path.exists(path_save):
            os.makedirs(path_save)

        path = "static/uploads" + location

        date_time_now = datetime.now().strftime("%H%M%S%f")
        name_split = os.path.splitext(file.filename)
        if name == "":
            name = file.filename
            back_name = name_split[0]
        else:
            back_name = name
            name = f"{name}{name_split[1]}"

        path = f"{path}/{date_time_now}_{name}"
        path_save = f"{path_save}/{date_time_now}_{name}"
        contents = await file.read()
        with open(path_save, "wb") as f:
            f.write(contents)

        return path, back_name, file.content_type

    except Exception as e:
        print(e)
        return None, None, None


async def upload_private_file_local(file: UploadFile, location: str = "", name: str = ""):
    """
    This function is used to upload a file to the server. The file is saved
    in the src/static directory. If a location is provided, the file is saved
    in that location. If a name is provided, the file is saved with that name.
    Otherwise, the file is saved with the same name as the original file.

    Args:
        file (UploadFile): The file to be uploaded
        location (str): The location where the file should be saved
        name (str): The name with which the file should be saved

    Returns:
        A tuple containing the path of the saved file, the name of the saved
        file, and the content type of the file
    """
    try:
        path_save = "src/uploads"
        path_save = path_save + location

        if not os.path.exists(path_save):
            os.makedirs(path_save)

        path = "uploads" + location

        date_time_now = datetime.now().strftime("%H%M%S%f")
        name_split = os.path.splitext(file.filename)
        if name == "":
            name = file.filename
            back_name = name_split[0]
        else:
            back_name = name
            name = f"{name}{name_split[1]}"

        path = f"{path}/{date_time_now}_{name}"
        path_save = f"{path_save}/{date_time_now}_{name}"
        with open(path_save, "wb") as f:
            f.write(file.file.read())

        return path, back_name, file.content_type

    except Exception as e:
        print(e)
        return None, None, None


def delete_file_local(file_path: str):
    """Delete a file from the static folder."""
    try:
        # Construct the full path to the image
        full_path = os.path.join("src", file_path)

        # Check if the file exists
        if os.path.exists(full_path):
            os.remove(full_path)
            return {"message": "File deleted successfully", "success": True}
        else:
            return {"message": "File not found", "success": False}

    except Exception as e:
        print(e)
        return {"message": "Exception has occur", "success": False}


push_service = FCMNotification(
        service_account_file="src/laakam.json",
        credentials=None,
        project_id="laakam-487e5"
    )

env = Environment(loader=FileSystemLoader('src/templates'))

class NotificationHelper :
    @staticmethod
    @shared_task  
    def send_in_app_notification(notify_data : dict):
        """
        Send an in app notification to a user, given the notification data.

        Args:
        data (Notification): The notification data.

        Returns:
        None
        """
        
        NotificationHelper.send_push_notification(data=notify_data)


    @staticmethod
    @shared_task  
    def send_push_notification(notify_data : dict):
        """
            Send an in app notification to a user, given the notification data.

            Args:
            data (Notification): The notification data.

            Returns:
            None
        """
        
        #data = {
        #    "channel": "notify-" + notify_data["user_id"],   
        #    "content" :  {
        #        "type":"notification",
        #        "data": notify_data
        #    }
        #}
        
        #NotificationHelper.send_ws_message(data=data)
        
        print(notify_data)
        response = push_service.notify( 
                fcm_token=notify_data["device_id"],
                notification_title=notify_data["title"],
                notification_body=notify_data["message"],
                notification_image=notify_data["image"],
                data_payload=notify_data["action"]
            )
        


    @staticmethod   
    @shared_task       
    def send_whatsapp_message(data = dict): 
        
        token =   get_access_token(AccessTokenType.WHATSAPP)
        headers = {
                "Content-Type": "application/json",
                'Accept': 'application/json',
                "Authorization": f"Bearer {token}"
            }
        
        url = f"{settings.TOUPESU_WHATSAPP_URL}/api/v1/post-message"

        with httpx.Client() as client:
            response =  client.post(url, json= data, headers=headers)  
            
            if response.status_code == 200 :
                response_json =  response.json()
                print(response_json)
            elif response.status_code == 401 :
                print("Unauthorized")
                
            else :
                print(response.status_code)
                print(response.text)    


    @staticmethod  
    @shared_task      
    def send_smtp_email(data : dict):
    
        """
        Send an email using SMTP.

        This function sends an email to the given address using an SMTP server.
        The email body can be either a plain text string or an HTML string
        rendered from a template.

        Args:
        to_email (str): The email address to send the email to.
        subject (str): The email subject.
        body (str): The email body (optional).
        template_name (str): The name of the template to use for the email body (optional).
        context (dict): The context to pass to the template (optional).

        Returns:
        None
        """
        message = MIMEMultipart()
        message["From"] = settings.EMAILS_FROM_EMAIL
        message["To"] = data["to_email"]
        message["Subject"] =  data["subject"]

        if data["template_name"] :
            template = env.get_template(data["lang"] + "/" + data["template_name"])
            body = template.render(data["context"])

        message.attach(MIMEText(body, "html" if data["template_name"] else "plain"))     
            
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
                
                print('email send ' + data["to_email"] )
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")    


    @staticmethod  
    @shared_task
    def send_mailgun_email(data: dict):
        """
        Send an email using Mailgun API.

        This function sends an email to the given address using the Mailgun API.
        The email body can be either a plain text string or an HTML string
        rendered from a template.

        Args:
        data (dict): A dictionary containing:
            - to_email (str): The email address to send the email to.
            - subject (str): The email subject.
            - body (str): The email body (optional).
            - template_name (str): The name of the template to use for the email body (optional).
            - context (dict): The context to pass to the template (optional).

        Returns:
        None
        """
        # Prepare the body
        body = data.get("body", "")
    
        if data.get("template_name") :
            template = env.get_template(data["lang"] + "/"  + data["template_name"])
            body = template.render(data["context"])
            
        url = f"https://{settings.MAILGUN_ENDPOINT}/v3/{settings.MAILGUN_DOMAIN}/messages"

        # Email payload
        payload = {
            "from": settings.EMAILS_FROM_EMAIL,
            "to": data["to_email"],
            "subject": data["subject"],
            "text": body if not data.get("template_name") else None,
            "html": body if data.get("template_name") else None,
        }
        
    
        
        try:
            with httpx.Client() as client:
                response =   client.post(url, data=payload,auth=("api", settings.MAILGUN_SECRET))
            
                if response.status_code == 200:
                    
                    print(f"Email sent successfully to {data['to_email']} with Mailgun API")
                else:
                    print(f"Failed to send email: {response.status_code} - {response.text} with Mailgun API")


        except httpx.HTTPError as e:
            print(f"An error occurred while sending the email: {e}")
