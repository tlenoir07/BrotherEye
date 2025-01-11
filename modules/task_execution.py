# task_execution.py

# task_execution.py
import hashlib
import logging
import os
import shutil
import subprocess
import webbrowser
import threading
import psutil  # For system monitoring
import requests  # For API requests
import smtplib  # For email
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime  # For calendar events

# Core Functions
def open_file(file_path):
    """
    Opens a file using the default system application.
    """
    try:
        logging.info(f"Attempting to open file: {file_path}")
        if os.path.exists(file_path):
            os.startfile(file_path)  # For Windows
            logging.info(f"File opened successfully: {file_path}")
        else:
            logging.warning(f"File not found: {file_path}")
            print(f"Error: File not found - {file_path}")
    except Exception as e:
        logging.error(f"Error while opening file: {file_path} - {e}")
        print(f"An error occurred: {e}")

def run_program(program_path):
    """
    Launches a program.
    """
    try:
        logging.info(f"Attempting to run program: {program_path}")
        subprocess.Popen(program_path, shell=True)  # Launch program
        logging.info(f"Program launched successfully: {program_path}")
    except Exception as e:
        logging.error(f"Error while running program: {program_path} - {e}")
        print(f"An error occurred: {e}")

def open_url(url):
    """
    Opens a URL in the default web browser.
    """
    try:
        logging.info(f"Attempting to open URL: {url}")
        webbrowser.open(url)  # Open URL in the default browser
        logging.info(f"URL opened successfully: {url}")
    except Exception as e:
        logging.error(f"Error while opening URL: {url} - {e}")
        print(f"An error occurred: {e}")

def run_shell_command(command):
    """
    Executes a shell command and returns the output.
    """
    try:
        logging.info(f"Running shell command: {command}")
        result = subprocess.check_output(command, shell=True, text=True)
        logging.info(f"Command output: {result.strip()}")
        print(result.strip())
    except Exception as e:
        logging.error(f"Error while executing shell command: {command} - {e}")
        print(f"An error occurred: {e}")

def search_files(directory, search_term):
    """
    Search for files in a directory (and subdirectories) by name or content.
    """
    try:
        logging.info(f"Searching for files in '{directory}' with term '{search_term}'")
        matching_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if search_term.lower() in file.lower():
                    matching_files.append(os.path.join(root, file))
        logging.info(f"Found {len(matching_files)} matching files.")
        return matching_files
    except Exception as e:
        logging.error(f"Error while searching files: {e}")
        print(f"An error occurred: {e}")
        return []

def batch_file_operation(files, destination, operation="copy"):
    """
    Perform batch operations (copy, move, delete) on a list of files.
    """
    try:
        logging.info(f"Performing '{operation}' operation on files: {files} to '{destination}'")
        for file in files:
            if operation == "copy":
                shutil.copy(file, destination)
            elif operation == "move":
                shutil.move(file, destination)
            elif operation == "delete":
                os.remove(file)
            else:
                logging.warning(f"Invalid operation: {operation}")
                print(f"Invalid operation: {operation}")
                return
        logging.info(f"Batch '{operation}' operation completed successfully.")
        print(f"Batch '{operation}' operation completed successfully.")
    except Exception as e:
        logging.error(f"Error during batch file operation: {e}")
        print(f"An error occurred: {e}")

# Task Scheduling
def schedule_task(task_function, delay):
    """
    Schedules a task to run after a delay in seconds.
    """
    try:
        logging.info(f"Scheduling task '{task_function.__name__}' to run in {delay} seconds.")
        threading.Timer(delay, task_function).start()
        print(f"Task '{task_function.__name__}' scheduled to run in {delay} seconds.")
    except Exception as e:
        logging.error(f"Error while scheduling task: {e}")
        print(f"An error occurred: {e}")

# System Monitoring
def get_system_usage():
    """
    Returns the current CPU, memory, and disk usage.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        system_usage = {
            "cpu": cpu_usage,
            "memory": memory.percent,
            "disk": disk.percent,
        }
        logging.info(f"System usage: {system_usage}")
        return system_usage
    except Exception as e:
        logging.error(f"Error while retrieving system usage: {e}")
        print(f"An error occurred: {e}")
        return None

def monitor_system(thresholds):
    """
    Monitors the system usage and provides alerts if thresholds are exceeded.
    """
    try:
        usage = get_system_usage()
        if usage:
            alerts = []
            if usage["cpu"] > thresholds.get("cpu", 100):
                alerts.append(f"CPU usage is high: {usage['cpu']}%")
            if usage["memory"] > thresholds.get("memory", 100):
                alerts.append(f"Memory usage is high: {usage['memory']}%")
            if usage["disk"] > thresholds.get("disk", 100):
                alerts.append(f"Disk usage is high: {usage['disk']}%")
            
            if alerts:
                for alert in alerts:
                    print(alert)
                    logging.warning(alert)
            else:
                print("System is operating within normal limits.")
    except Exception as e:
        logging.error(f"Error during system monitoring: {e}")
        print(f"An error occurred: {e}")

# Weather API
def get_weather(api_key, location):
    """
    Fetches weather data for a given location using the OpenWeatherMap API.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Parse weather information
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        
        weather_report = (
            f"Weather in {location.capitalize()}:\n"
            f"- Condition: {weather.capitalize()}\n"
            f"- Temperature: {temp}°C\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_speed} m/s"
        )
        logging.info(f"Fetched weather data for {location}: {weather_report}")
        return weather_report
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return f"Error: Unable to fetch weather data for {location}."

# Google Calendar API
from google_auth_oauthlib.flow import InstalledAppFlow

def get_calendar_service():
    """
    Authenticate and return the Google Calendar service object.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    credentials_path = r'C:\Users\Tyler\BrotherEye\credentials.json'  # Absolute path to credentials.json

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error accessing Google Calendar API: {e}")
        return None


def list_events():
    """
    Lists the upcoming 10 events on the user's calendar.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Unable to access calendar."

    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found."
        event_list = "Upcoming events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list += f"{start} - {event['summary']}\n"
        return event_list
    except HttpError as error:
        logging.error(f"Error fetching events: {error}")
        return "Error: Unable to retrieve events."

def add_event(summary, start_time, end_time):
    """
    Adds an event to the user's calendar.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Unable to access calendar."

    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
    except HttpError as error:
        logging.error(f"Error adding event: {error}")
        return "Error: Unable to add event."

# Email Integration
def send_email(sender, password, recipient, subject, body):
    """
    Sends an email using SMTP.
    """
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return f"Email sent successfully to {recipient}."
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"Error: Unable to send email. {e}"

# News API
def get_news(api_key, topic="general"):
    """
    Fetches the latest news headlines for a given topic.
    """
    try:
        url = f"https://newsapi.org/v2/top-headlines?category={topic}&apiKey={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("articles"):
            headlines = "Latest News:\n"
            for article in data["articles"][:5]:
                headlines += f"- {article['title']} ({article['source']['name']})\n"
            return headlines
        else:
            return "No news articles found for the specified topic."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {e}")
        return f"Error: Unable to fetch news."

def find_large_files(directory, size_limit_mb):
    """
    Finds files larger than the specified size in MB within a directory.
    """
    try:
        logging.info(f"Searching for files larger than {size_limit_mb}MB in {directory}")
        size_limit_bytes = size_limit_mb * 1024 * 1024
        large_files = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) > size_limit_bytes:
                    large_files.append(file_path)

        if large_files:
            logging.info(f"Found {len(large_files)} large files.")
        else:
            logging.info("No large files found.")
        return large_files
    except Exception as e:
        logging.error(f"Error finding large files: {e}")
        return []

def find_duplicate_files(directory):
    """
    Identifies duplicate files in a directory by comparing file hashes.
    """
    try:
        logging.info(f"Searching for duplicate files in {directory}")
        file_hashes = {}
        duplicates = []

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    if file_hash in file_hashes:
                        duplicates.append(file_path)
                    else:
                        file_hashes[file_hash] = file_path

        if duplicates:
            logging.info(f"Found {len(duplicates)} duplicate files.")
        else:
            logging.info("No duplicate files found.")
        return duplicates
    except Exception as e:
        logging.error(f"Error finding duplicate files: {e}")
        return []

def find_files_by_extension(directory, extensions):
    """
    Finds files with specific extensions in a directory.
    """
    try:
        logging.info(f"Searching for files with extensions {extensions} in {directory}")
        matching_files = []

        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    matching_files.append(os.path.join(root, file))

        if matching_files:
            logging.info(f"Found {len(matching_files)} matching files.")
        else:
            logging.info("No matching files found.")
        return matching_files
    except Exception as e:
        logging.error(f"Error finding files by extension: {e}")
        return []

import ast

def analyze_code(file_path):
    """
    Analyzes the given Python file for syntax issues and provides a detailed report.
    """
    try:
        # Read the file content
        with open(file_path, "r") as file:
            code = file.read()
        
        # Parse the code
        tree = ast.parse(code)
        
        # Analyze the syntax tree
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and not node.body:
                issues.append(f"Line {node.lineno}: 'for' loop has no body.")
            if isinstance(node, ast.While) and not node.body:
                issues.append(f"Line {node.lineno}: 'while' loop has no body.")
            if isinstance(node, ast.FunctionDef) and not node.body:
                issues.append(f"Line {node.lineno}: Function '{node.name}' has no body.")
        
        if issues:
            return "The code has the following issues:\n" + "\n".join(issues)
        else:
            return "The code has no syntax or logical structure issues."
    except FileNotFoundError:
        return f"Error: The file '{file_path}' does not exist."
    except SyntaxError as e:
        return f"Syntax Error detected: {e.msg} on line {e.lineno}"
    except Exception as e:
        return f"An error occurred during code analysis: {e}"

def analyze_self():
    """
    Analyzes the bot's main code file for issues using the analyze_code function.
    """
    try:
        return analyze_code(__file__)
    except Exception as e:
        return f"Error analyzing self: {e}"

