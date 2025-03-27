import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext, StringVar
import subprocess
import os
import pyperclip
import re
import time

# Function to run the selected programming language
def run_code():
    code = editor.get("1.0", "end-1c").strip()
    selected_lang = lang_choice.get()

    if not code:
        output_window.insert("end", "⚠️ No code to execute!\n", "stderr")
        return

    temp_files = []
    file_map = {
        "Python": ("temp_script.py", ["python", "temp_script.py"]),
        "C": ("temp_script.c", ["gcc", "temp_script.c", "-o", "temp_script.exe" if os.name == "nt" else "temp_script"]),
        "C++": ("temp_script.cpp", ["g++", "temp_script.cpp", "-o", "temp_script.exe" if os.name == "nt" else "temp_script"]),
    }

    # ** Improved Language Detection **
    detected_lang = None

    if re.search(r"\bpublic\s+class\s+\w+", code):
        detected_lang = "Java"
    elif re.search(r"^\s*#include\s*<\w+>", code, re.MULTILINE):
        detected_lang = "C++" if re.search(r"\bstd::|cout|cin\b", code) else "C"
    elif re.search(r"^\s*import\s+\w+|^\s*def\s+\w+\(|^\s*class\s+\w+\(", code, re.MULTILINE):
        detected_lang = "Python"

    if detected_lang and detected_lang != selected_lang:
        output_window.insert("end", f"⚠️ Warning: Detected {detected_lang} code, but {selected_lang} is selected!\n", "stderr")
        return

    # ** Handle Java Separately **
    if selected_lang == "Java":
        match = re.search(r"public\s+class\s+(\w+)", code)
        if not match:
            output_window.insert("end", "⚠️ Error: Java code must have a `public class` declaration!\n", "stderr")
            return
        class_name = match.group(1)
        if not re.search(r"public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s*\w*\)", code):
            output_window.insert("end", "⚠️ Error: Java code must contain a `main` method to execute!\n", "stderr")
            return
        filename = f"{class_name}.java"
        temp_files.append(filename)
    else:
        if selected_lang not in file_map:
            output_window.insert("end", "⚠️ Unsupported Language\n", "stderr")
            return
        filename, command = file_map[selected_lang]
        temp_files.append(filename)

    # Write Code to File
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception as e:
        output_window.insert("end", f"⚠️ Error writing file: {str(e)}\n", "stderr")
        return

    try:
        # ** Compilation for C, C++, Java **
        if selected_lang in ["C", "C++"]:
            compile_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if compile_process.returncode != 0:
                output_window.insert("end", f"⚠️ Compilation Error:\n{compile_process.stderr}\n", "stderr")
                return
            run_command = ["temp_script.exe" if os.name == "nt" else "./temp_script"]
        elif selected_lang == "Java":
            compile_process = subprocess.run(["javac", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if compile_process.returncode != 0:
                output_window.insert("end", f"⚠️ Compilation Error:\n{compile_process.stderr}\n", "stderr")
                return
            run_command = ["java", "-cp", ".", class_name]
        else:
            run_command = command  # Python runs directly

        # ** Execute the Compiled Code **
        start_time = time.time()
        run_process = subprocess.Popen(run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Non-blocking read to prevent UI freeze
        output, error = run_process.communicate(timeout=10)  
        elapsed_time = time.time() - start_time

        # ** Display Output **
        output_window.delete("1.0", "end")
        if output:
            output_window.insert("end", output, "stdout")
        if error:
            output_window.insert("end", f"⚠️ Error:\n{error}\n", "stderr")
        output_window.insert("end", f"\nExecution Time: {elapsed_time:.2f} seconds........\n")

    except subprocess.TimeoutExpired:
        run_process.kill()
        output_window.insert("end", "⚠️ Error: Execution Timed Out (10s limit)\n", "stderr")
    except FileNotFoundError as e:
        output_window.insert("end", f"⚠️ Error: {str(e)} - Missing Compiler/Interpreter?\n", "stderr")
    except Exception as e:
        output_window.insert("end", f"⚠️ Error: {str(e)}\n", "stderr")
    finally:
    # Clean up temporary files
       for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                    output_window.insert("end", f"⚠️ Warning: Could not delete {temp_file}: {str(e)}\n", "stderr")

    # Remove compiled Java class file
    if selected_lang == "Java":
        class_file = f"{class_name}.class"
        try:
            if os.path.exists(class_file):
                os.remove(class_file)
        except Exception as e:
            output_window.insert("end", f"⚠️ Warning: Could not delete {class_file}: {str(e)}\n", "stderr")



# Function to save a file
def save_file():
    lang = lang_choice.get()
    extensions = {"Python": ".py", "C": ".c", "C++": ".cpp", "Java": ".java"}
    file_extension = extensions.get(lang, ".txt")
    filename = filedialog.asksaveasfilename(defaultextension=file_extension, filetypes=[(f"{lang} Files", f"*{file_extension}"), ("All Files", "*.*")])
    if filename:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(editor.get("1.0", "end-1c"))
            
# Function to debug code
def debug_code():
    run_code()

# Default theme
theme = "darkly"

# Define syntax highlighting and output window colors for themes
syntax_colors = {
    "darkly": {  # Dark mode colors
        "keyword": "cyan",
        "function": "light green",
        "comment": "gray",
        "string": "orange",
        "default": "white",
        "output_bg": "#222222",   # Dark output window
        "output_fg": "#00FF00",   # Green text
        "error_fg": "#FF5555"     # Red errors
    },
    "litera": {  # Light mode colors
        "keyword": "blue",
        "function": "dark green",
        "comment": "gray",
        "string": "brown",
        "default": "black",
        "output_bg": "#EEEEEE",   # Light output window
        "output_fg": "#006600",   # Dark green text
        "error_fg": "#990000"     # Dark red errors
    }
}

# Function to apply syntax highlighting
def highlight_syntax(event=None):
    editor.tag_remove("keyword", "1.0", "end")
    editor.tag_remove("function", "1.0", "end")
    editor.tag_remove("comment", "1.0", "end")
    editor.tag_remove("string", "1.0", "end")
    colors = syntax_colors[theme]
    
    # Define regex patterns for highlighting
    keyword_pattern = r"\b(class|def|return|if|else|for|while|break|continue|try|catch|import|public|private|static|void|int|double|string|boolean)\b"
    function_pattern = r"\b[A-Za-z_][A-Za-z0-9_]*(?=\()"
    comment_pattern = r"//.*|#.*"
    string_pattern = r"(['\"])(?:(?=(\\?))\2.)*?\1"


    # Apply highlighting
    apply_highlighting(keyword_pattern, "keyword", colors["keyword"])
    apply_highlighting(function_pattern, "function", colors["function"])
    apply_highlighting(comment_pattern, "comment", colors["comment"])
    apply_highlighting(string_pattern, "string", colors["string"])

# Function to apply regex-based highlighting
def apply_highlighting(pattern, tag_name, color):
    editor.tag_config(tag_name, foreground=color)
    for match in re.finditer(pattern, editor.get("1.0", "end-1c")):
        start, end = f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars"
        editor.tag_add(tag_name, start, end)

def toggle_theme():
    global theme
    theme = "litera" if theme == "darkly" else "darkly"
    root.style.theme_use(theme)
    theme_button.config(text="☀️ Light" if theme == "litera" else "🌙 Dark")
    editor.config(fg=syntax_colors[theme]["default"])  # Change text color
    colors = syntax_colors[theme]
    editor.config(fg=colors["default"])  # Change text color
    highlight_syntax()  # Update syntax colors on theme change
    # Update output window colors
    output_window.config(bg=colors["output_bg"], fg=colors["output_fg"])
    output_window.tag_config("stdout", foreground=colors["output_fg"])
    output_window.tag_config("stderr", foreground=colors["error_fg"])

# Function to share code
def share_code():
    pyperclip.copy(editor.get("1.0", "end-1c"))
    messagebox.showinfo("Copied!", "Code copied to clipboard!")

# Function to handle shortcuts
def bind_shortcuts():
    editor.bind("<Control-a>", lambda e: select_all())
    editor.bind("<Control-s>", lambda e: save_file())
    editor.bind("<F5>", lambda e: run_code())

def select_all(event=None):
    editor.tag_add("sel", "1.0", "end-1c")
    return "break"

def auto_save():
    with open("autosave.txt", "w", encoding="utf-8") as f:
        f.write(editor.get("1.0", "end-1c"))
    root.after(10000, auto_save)  # Repeat every 10 seconds

# Create GUI window
root = ttk.Window(themename="darkly")
root.title("Multi-Language Offline Compiler")
root.geometry("900x700")

# Top button frame
top_button_frame = ttk.Frame(root)
top_button_frame.pack(fill="x", pady=5)

# Language selection dropdown
lang_choice = StringVar(value="Python")
languages = ["Python", "C", "C++", "Java"]
lang_menu = ttk.Combobox(top_button_frame, textvariable=lang_choice, values=languages, state="readonly", width=10)
lang_menu.pack(side="left", padx=5)

ttk.Button(top_button_frame, text="▶ Run", command=run_code, bootstyle=SUCCESS, width=10).pack(side="left", padx=5)
ttk.Button(top_button_frame, text="💾 Save", command=save_file, bootstyle=PRIMARY, width=10).pack(side="left", padx=5)
ttk.Button(top_button_frame, text="🐞 Debug", command=debug_code, bootstyle=WARNING, width=10).pack(side="left", padx=5)
ttk.Button(top_button_frame, text="📤 Share", command=share_code, bootstyle=INFO, width=10).pack(side="left", padx=5)

theme_button = ttk.Button(top_button_frame, text="🌙 Dark", command=toggle_theme, bootstyle=SECONDARY, width=10)
theme_button.pack(side="left", padx=15)

# Code editor
editor = scrolledtext.ScrolledText(root, font=("Consolas", 12), wrap="word", height=15, fg=syntax_colors[theme]["default"])
editor.pack(padx=10, pady=5, fill="both", expand=True)
editor.bind("<KeyRelease>", highlight_syntax)

# Output window
output_window = scrolledtext.ScrolledText(root, font=("Consolas", 12), wrap="word", height=10)
output_window.pack(padx=10, pady=5, fill="both", expand=True)
output_window.tag_config("stdout", foreground="lightgreen")
output_window.tag_config("stderr", foreground="red")

auto_save()
bind_shortcuts()
root.mainloop()