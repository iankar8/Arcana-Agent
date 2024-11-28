import tkinter as tk
from tkinter import messagebox

class ArcanaAgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Arcana Agent Framework")

        # Create input field
        self.input_label = tk.Label(root, text="Enter your query:")
        self.input_label.pack(pady=5)

        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.pack(pady=5)

        # Create submit button
        self.submit_button = tk.Button(root, text="Submit", command=self.process_input)
        self.submit_button.pack(pady=20)

        # Create output display
        self.output_text = tk.Text(root, height=10, width=60, state=tk.DISABLED)
        self.output_text.pack(pady=5)

    def process_input(self):
        query = self.input_entry.get()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a query.")
            return

        # Here you would connect to the backend to process the query
        # For now, we'll just display a placeholder message
        self.display_output(f"Processing query: {query}")

    def display_output(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = ArcanaAgentGUI(root)
    root.mainloop()
