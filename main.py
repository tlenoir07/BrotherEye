import tkinter as tk
from tkinter import scrolledtext, ttk
import time
import logging
import threading
import os
import pyttsx3
import speech_recognition as sr
from modules import task_execution
from modules.openai_integration import get_chatgpt_response, reset_chat_history
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import importlib.util
import glob
import requests

# Define the bot's current version
VERSION = "1.0.0"

def check_for_updates():
    """
    Check for updates by comparing the local version with the latest version in the repository.
    """
    try:
        # GitHub API endpoint for the latest release
        repo_api_url = "https://github.com/tlenoir07/BrotherEye"  # Replace with your repo details
        response = requests.get(repo_api_url)
        response.raise_for_status()

        latest_version = response.json()["tag_name"]
        if VERSION == latest_version:
            return "You are running the latest version."
        else:
            return f"Update available: {latest_version}. Use 'apply_update' to update."
    except Exception as e:
        return f"Error checking for updates: {e}"

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

print(f"Current working directory: {os.getcwd()}")

# Set up logging
logging.basicConfig(
    filename="logs/brother_eye.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)  # Adjust speaking speed

command_history = []  # For command history dropdown
speech_enabled = False  # Speech is disabled by default

# Plugin registry
plugins = {}

# Plugin directory
PLUGIN_DIR = "plugins"

# Ensure the plugin directory exists
if not os.path.exists(PLUGIN_DIR):
    os.makedirs(PLUGIN_DIR)

def speak(text):
    """Convert text to speech."""
    if speech_enabled:
        tts_engine.say(text)
        tts_engine.runAndWait()

def load_plugins():
    """Dynamically load plugins from the plugin directory."""
    global plugins
    plugins.clear()

    plugin_files = glob.glob(os.path.join(PLUGIN_DIR, "*.py"))
    for plugin_file in plugin_files:
        plugin_name = os.path.splitext(os.path.basename(plugin_file))[0]
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "initialize"):
                plugins[plugin_name] = module
                module.initialize()
                print(f"Loaded plugin: {plugin_name}")
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")

def process_nlp_command(input_text):
    """
    Converts conversational commands into structured commands.
    """
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(input_text.lower())
    tokens = [word for word in tokens if word not in stop_words]

    if "weather" in tokens:
        return f"weather {input_text.replace('weather', '').strip()}"
    if "system" in tokens and "usage" in tokens:
        return "system"
    if "email" in tokens:
        return "send_email"
    if "calendar" in tokens and "list" in tokens:
        return "list_events"
    if "calendar" in tokens and "add" in tokens:
        return "add_event"
    if "news" in tokens:
        return f"news {input_text.replace('news', '').strip()}"
    if "schedule" in input_text:
        return "schedule"
    if "large files" in input_text:
        return "large_files"
    if "duplicate files" in input_text:
        return "duplicates"
    if "file types" in input_text:
        return "file_types"
    if "analyze code" in input_text:
        return "analyze_code"
    if "analyze self" in input_text:
        return "analyze_self"
    if "list plugins" in input_text:
        return "list_plugins"
    if "enable plugin" in input_text:
        return f"enable_plugin {input_text.replace('enable plugin', '').strip()}"
    if "disable plugin" in input_text:
        return f"disable_plugin {input_text.replace('disable plugin', '').strip()}"
    # Default to chat if not recognized
    return f"chat {input_text}"

def handle_file_analysis(action, argument, output_box):
    """
    Handles file analysis commands in a separate thread.
    """
    try:
        if action == "large_files":
            directory, size_limit_mb = map(str.strip, argument.split(",", 1))
            size_limit_mb = int(size_limit_mb)
            large_files = task_execution.find_large_files(directory, size_limit_mb)
            result = "\n".join(large_files) if large_files else "No large files found."
        elif action == "duplicates":
            directory = argument.strip()
            duplicates = task_execution.find_duplicate_files(directory)
            result = "\n".join(duplicates) if duplicates else "No duplicate files found."
        elif action == "file_types":
            directory, extensions = map(str.strip, argument.split(",", 1))
            extensions = extensions.split(";")
            matching_files = task_execution.find_files_by_extension(directory, extensions)
            result = "\n".join(matching_files) if matching_files else "No matching files found."
        else:
            result = f"Unknown file analysis command: {action}"

        output_box.insert(tk.END, f"> {action} {argument}\n{result}\n\n")
        output_box.see(tk.END)
    except Exception as e:
        result = f"An error occurred during file analysis: {e}"
        output_box.insert(tk.END, f"> {action} {argument}\n{result}\n\n")
        output_box.see(tk.END)

def handle_command_gui(command, output_box, log_box):
    """
    Handles commands from the GUI and displays results in the output box.
    """
    try:
        parts = command.split(" ", 1)
        action = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else None
        result = ""

        if action == "help":
            # Display the list of available commands
            result = (
                "Available Commands:\n"
                "1. hello - Greets the user.\n"
                "2. reset_chat - Resets the ChatGPT conversation history.\n"
                "3. open <file_path> - Opens the specified file.\n"
                "4. run <program_path> - Runs the specified program.\n"
                "5. browse <url> - Opens the specified URL in a browser.\n"
                "6. shell <command> - Executes a shell command.\n"
                "7. system - Shows system resource usage (CPU, Memory, Disk).\n"
                "8. monitor cpu=<value>,memory=<value>,disk=<value> - Monitors system thresholds.\n"
                "9. schedule <command>,<delay_in_seconds> - Schedules a command to run after a delay.\n"
                "10. weather <location> - Fetches weather data for a location.\n"
                "11. list_events - Lists upcoming calendar events.\n"
                "12. add_event <summary>,<start_time>,<end_time> - Adds an event to the calendar.\n"
                "13. send_email <sender>,<password>,<recipient>,<subject>,<body> - Sends an email.\n"
                "14. news <topic> - Fetches the latest news for a topic.\n"
                "15. large_files <directory>,<size_limit_mb> - Finds large files exceeding the size limit.\n"
                "16. duplicates <directory> - Finds duplicate files in a directory.\n"
                "17. file_types <directory>,<extensions> - Finds files with specific extensions.\n"
                "18. analyze_code <file_path> - Analyzes the syntax of a specified file.\n"
                "19. analyze_self - Analyzes the current bot's code.\n"
                "20. list_plugins - Lists all loaded plugins.\n"
                "21. enable_plugin <plugin_name> - Enables a specific plugin.\n"
                "22. disable_plugin <plugin_name> - Disables a specific plugin.\n"
                "23. help - Displays this list of commands.\n"
            )
        elif action == "hello":
            result = "Hello! How can I assist you today?"
        elif action == "open":
            if argument:
                task_execution.open_file(argument)
                result = f"Opening file: {argument}"
            else:
                result = "Error: No file path provided."
        elif action == "run":
            if argument:
                task_execution.run_program(argument)
                result = f"Running program: {argument}"
            else:
                result = "Error: No program path provided."
        elif action == "browse":
            if argument:
                task_execution.open_url(argument)
                result = f"Opening URL: {argument}"
            else:
                result = "Error: No URL provided."
        elif action == "shell":
            if argument:
                result = task_execution.run_shell_command(argument)
            else:
                result = "Error: No shell command provided."
        elif action == "chat":
            if argument:
                result = get_chatgpt_response(argument)
            else:
                result = "Error: No input provided for ChatGPT."
        elif action == "reset_chat":
            reset_chat_history()
            result = "ChatGPT conversation history reset."
        elif action == "weather":
            if argument:
                api_key = "3f10a90318c80b17731f3b0c6ea29abb"  # OpenWeatherMap API key
                result = task_execution.get_weather(api_key, argument)
            else:
                result = "Error: Please provide a location for the weather report."
        elif action == "list_plugins":
            result = "Installed Plugins:\n" + "\n".join(plugins.keys())
        elif action == "enable_plugin":
            plugin_name = argument.strip()
            if plugin_name in plugins:
                plugins[plugin_name].initialize()
                result = f"Plugin '{plugin_name}' enabled."
            else:
                result = f"Plugin '{plugin_name}' not found."
        elif action == "disable_plugin":
            plugin_name = argument.strip()
            if plugin_name in plugins:
                plugins.pop(plugin_name, None)
                result = f"Plugin '{plugin_name}' disabled."
            else:
                result = f"Plugin '{plugin_name}' not found."
           # Other actions here...
        elif action == "check_updates":
            result = check_for_updates()
        else:
            result = f"Unknown command: {command}"

        output_box.insert(tk.END, f"> {command}\n{result}\n\n")
        output_box.see(tk.END)
        log_box.insert(tk.END, f"SUCCESS: Executed {action} command.\n")
        log_box.see(tk.END)
        speak(result)
        command_history.append(command)
    except Exception as e:
        output_box.insert(tk.END, f"An error occurred: {e}\n")
        output_box.see(tk.END)
        log_box.insert(tk.END, f"ERROR: {e}\n")
        log_box.see(tk.END)
        speak("An error occurred while processing your command.")

def listen_for_voice_command(output_box, log_box):
    """Listen for a voice command and process it."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening for your command.")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            output_box.insert(tk.END, f"> Voice Input: {command}\n")
            handle_command_gui(command, output_box, log_box)
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
            output_box.insert(tk.END, "> Voice Input: Sorry, I didn't understand that.\n")
        except sr.RequestError as e:
            speak("Error with the speech recognition service.")
            output_box.insert(tk.END, f"> Voice Input Error: {e}\n")
        except Exception as e:
            speak("An error occurred while processing your voice command.")
            output_box.insert(tk.END, f"An error occurred: {e}\n")

def main_gui():
    """
    Launch the GUI for Brother Eye.
    """
    global speech_enabled

    root = tk.Tk()
    root.title("Brother Eye GUI")

    command_label = tk.Label(root, text="Enter Command:")
    command_label.pack(pady=5)
    command_entry = tk.Entry(root, width=50)
    command_entry.pack(pady=5)

    output_label = tk.Label(root, text="Output:")
    output_label.pack(pady=5)
    output_box = scrolledtext.ScrolledText(root, width=60, height=20, wrap=tk.WORD)
    output_box.pack(pady=5)

    log_label = tk.Label(root, text="Logs:")
    log_label.pack(pady=5)
    log_box = scrolledtext.ScrolledText(root, width=60, height=10, wrap=tk.WORD)
    log_box.pack(pady=5)

    command_history_dropdown = ttk.Combobox(root, values=command_history, width=47)
    command_history_dropdown.pack(pady=5)

    def on_submit():
        command = command_entry.get().strip()
        if command:
            handle_command_gui(command, output_box, log_box)
            command_entry.delete(0, tk.END)
            command_history_dropdown['values'] = command_history

    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=10)

    def on_voice_command():
        threading.Thread(target=listen_for_voice_command, args=(output_box, log_box)).start()

    voice_button = tk.Button(root, text="Voice Command", command=on_voice_command)
    voice_button.pack(pady=10)

    def toggle_speech():
        global speech_enabled
        speech_enabled = not speech_enabled
        speak_button.config(text=f"Speech: {'ON' if speech_enabled else 'OFF'}")

    speak_button = tk.Button(root, text="Speech: OFF", command=toggle_speech)
    speak_button.pack(pady=10)

    def reload_plugins():
        load_plugins()
        output_box.insert(tk.END, "Plugins reloaded.\n")
        log_box.insert(tk.END, "INFO: Plugins reloaded.\n")
        output_box.see(tk.END)
        log_box.see(tk.END)

    reload_plugins_button = tk.Button(root, text="Reload Plugins", command=reload_plugins)
    reload_plugins_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    load_plugins()
    main_gui()
