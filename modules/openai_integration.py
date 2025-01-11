import openai
from config import OPENAI_API_KEY

# Initialize the OpenAI Client
client = openai.Client(api_key=OPENAI_API_KEY)

# Maintain conversation history for context
conversation_history = []

def get_chatgpt_response(prompt):
    """
    Sends a prompt to ChatGPT using the OpenAI Client object with context and returns the response.
    """
    try:
        # Append the user's prompt to the conversation history
        conversation_history.append({"role": "user", "content": prompt})

        # Call ChatGPT API with conversation history
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            temperature=0.7,
        )

        # Extract the assistant's response
        assistant_response = response.choices[0].message.content.strip()

        # Append the assistant's response to the conversation history
        conversation_history.append({"role": "assistant", "content": assistant_response})

        return assistant_response
    except openai.error.InvalidRequestError as e:  # For invalid input
        return f"Error: Invalid request - {e}"
    except openai.error.AuthenticationError as e:  # For invalid API key
        return f"Error: Authentication failed - {e}"
    except openai.error.RateLimitError as e:  # For rate limit issues
        return f"Error: Rate limit exceeded - {e}"
    except Exception as e:  # Generic catch-all for unexpected errors
        return f"Error: An unexpected error occurred - {e}"

def reset_chat_history():
    """
    Clears the conversation history to reset the context.
    """
    global conversation_history
    conversation_history = []
    print("ChatGPT conversation history reset.")
