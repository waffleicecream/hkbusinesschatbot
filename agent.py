import os
import csv
import json
import pickle
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

class ConversationMemory:
    """Manages conversation history with semantic summarization"""

    def __init__(self, max_recent_messages=4):
        self.full_history = []  # Complete history
        self.summaries = []  # Summarized older conversations
        self.max_recent_messages = max_recent_messages

    def add_message(self, role, content):
        """Add a message to history"""
        self.full_history.append({"role": role, "content": content})

    def get_context_for_api(self):
        """Get optimized context for API call"""
        # If history is short, return all
        if len(self.full_history) <= self.max_recent_messages:
            return self.full_history

        # Split into old and recent
        recent = self.full_history[-self.max_recent_messages:]

        # If we have summaries, include them
        context = []
        if self.summaries:
            context.append({
                "role": "user",
                "content": f"Previous conversation summary:\n{self.summaries[-1]}"
            })
            context.append({
                "role": "assistant",
                "content": "I remember our previous conversation."
            })

        # Add recent messages
        context.extend(recent)
        return context

    def summarize_old_conversations(self, csv_data, system_prompt):
        """Summarize older conversations to reduce token usage"""
        if len(self.full_history) <= self.max_recent_messages + 2:
            return

        # Get messages to summarize (exclude recent ones)
        to_summarize = self.full_history[2:-self.max_recent_messages]  # Skip initial context

        if len(to_summarize) < 2:
            return

        # Build conversation text
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:200]}..."
            if len(msg['content']) > 200 else f"{msg['role'].upper()}: {msg['content']}"
            for msg in to_summarize
        ])

        # Ask Claude to summarize
        try:
            summary_response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation into key points and findings. Be concise:\n\n{conv_text}"
                }]
            )

            summary = summary_response.content[0].text
            self.summaries.append(summary)

            # Remove summarized messages, keep first 2 (context) and recent ones
            self.full_history = self.full_history[:2] + self.full_history[-self.max_recent_messages:]

        except Exception as e:
            print(f"Note: Could not summarize conversation: {e}")

    def clear(self):
        """Clear all history"""
        self.full_history = []
        self.summaries = []

    def save(self, filepath="conversation_memory.pkl"):
        """Save conversation memory to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'full_history': self.full_history,
                'summaries': self.summaries
            }, f)

    def load(self, filepath="conversation_memory.pkl"):
        """Load conversation memory from file"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.full_history = data['full_history']
                self.summaries = data['summaries']
            return True
        except FileNotFoundError:
            return False

def load_csv_data(csv_path):
    """Load and format CSV data as a string"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Format as a readable table
    formatted_data = "\n".join([",".join(row) for row in rows])
    return formatted_data

def load_prompt(prompt_path):
    """Load system prompt from file"""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def estimate_tokens(text):
    """Rough estimation: 1 token ≈ 4 characters"""
    return len(text) // 4

def chat_with_claude(message, csv_data, system_prompt, memory):
    """Send message to Claude with optimized context"""
    # Initialize with CSV data on first message
    if len(memory.full_history) == 0:
        full_context = f"{system_prompt}\n\n## Business Report Data:\n\n{csv_data}\n\nRemember this data for our conversation. Answer the user's questions based on this information."
        memory.add_message("user", full_context)
        memory.add_message("assistant", "I understand. I have the Ecocutlery business report data loaded. I'm ready to answer your questions about product performance, sales, and metrics.")

    # Add current user message
    memory.add_message("user", message)

    # Summarize old conversations if history is getting long
    if len(memory.full_history) > 12:
        memory.summarize_old_conversations(csv_data, system_prompt)

    # Get optimized context
    context = memory.get_context_for_api()

    # Make API call
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2000,
        messages=context
    )

    response_text = response.content[0].text

    # Add assistant response to history
    memory.add_message("assistant", response_text)

    return response_text

if __name__ == "__main__":
    # Load CSV data and prompt
    csv_data = load_csv_data("Business report.csv")
    system_prompt = load_prompt("prompt.txt")

    # Initialize conversation memory
    memory = ConversationMemory(max_recent_messages=4)

    # Try to load previous conversation
    if memory.load():
        print("Previous conversation loaded!")

    print("Business Analytics Chatbot Ready!")
    print("Ask questions about your Ecocutlery product performance.")
    print("Commands: 'quit', 'clear', 'save', 'stats'\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            # Auto-save on exit
            memory.save()
            print("Conversation saved. Goodbye!")
            break

        if user_input.lower() == 'clear':
            memory.clear()
            print("\nConversation history cleared!\n")
            continue

        if user_input.lower() == 'save':
            memory.save()
            print("\nConversation saved!\n")
            continue

        if user_input.lower() == 'stats':
            total_msgs = len(memory.full_history)
            summaries = len(memory.summaries)
            estimated_tokens = sum(estimate_tokens(msg['content']) for msg in memory.get_context_for_api())
            print(f"\n📊 Stats:")
            print(f"  Total messages: {total_msgs}")
            print(f"  Summaries created: {summaries}")
            print(f"  Estimated tokens in current context: ~{estimated_tokens}\n")
            continue

        try:
            response = chat_with_claude(user_input, csv_data, system_prompt, memory)
            print(f"\nClaude: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")