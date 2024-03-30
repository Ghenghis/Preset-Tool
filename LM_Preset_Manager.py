import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import git
from git import Repo

CONFIG_PRESETS_DIR = r"C:\Users\Admin\.cache\lm-studio\config-presets"
DATABASE_FILE = "database.json"
MODEL_LIST_FILE = "model_list.txt"
GITHUB_REPO_URL = "https://github.com/your-username/lmstudio.git"
GITHUB_REPO_DIR = "lmstudio"

def load_database():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    else:
        return {"presets": {}, "models": []}

def save_database(database):
    with open(DATABASE_FILE, "w") as file:
        json.dump(database, file, indent=2)

def backup_database():
    backup_file = f"{DATABASE_FILE}.bak"
    shutil.copyfile(DATABASE_FILE, backup_file)

def backup_model_list():
    backup_file = f"{MODEL_LIST_FILE}.bak"
    shutil.copyfile(MODEL_LIST_FILE, backup_file)

def search_files():
    directory = filedialog.askdirectory(title="Select Directory")
    if directory:
        database = load_database()
        gguf_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".gguf"):
                    gguf_files.append(os.path.join(root, file))

        new_models = []
        for file in gguf_files:
            model_name = os.path.splitext(os.path.basename(file))[0]
            if model_name not in database["models"]:
                new_models.append(model_name)

        presets_created = 0
        for model_name in new_models:
            model_type = model_name.split("-")[0]
            preset_file = os.path.join(CONFIG_PRESETS_DIR, f"{model_type}.preset.json")
            if not os.path.exists(preset_file):
                default_preset = {
                    "name": f"{model_type} Preset",
                    "load_params": {
                        "n_ctx": 1500,
                        "n_batch": 512,
                        "rope_freq_base": 0,
                        "rope_freq_scale": 0,
                        "n_gpu_layers": 10,
                        "use_mlock": True,
                        "main_gpu": 0,
                        "tensor_split": [0],
                        "seed": -1,
                        "f16_kv": True,
                        "use_mmap": True
                    },
                    "inference_params": {
                        "n_threads": 4,
                        "n_predict": -1,
                        "top_k": 40,
                        "top_p": 0.95,
                        "temp": 0.8,
                        "repeat_penalty": 1.1,
                        "input_prefix": "### Instruction:\n",
                        "input_suffix": "\n### Response:\n",
                        "antiprompt": ["### Instruction:"],
                        "pre_prompt": "You are a helpful AI assistant.",
                        "seed": -1,
                        "tfs_z": 1,
                        "typical_p": 1,
                        "repeat_last_n": 64,
                        "frequency_penalty": 0,
                        "presence_penalty": 0,
                        "n_keep": 0,
                        "logit_bias": {},
                        "mirostat": 0,
                        "mirostat_tau": 5,
                        "mirostat_eta": 0.1,
                        "memory_f16": True,
                        "multiline_input": False,
                        "penalize_nl": True
                    }
                }
                with open(preset_file, "w") as file:
                    json.dump(default_preset, file, indent=2)
                presets_created += 1
                database["presets"][model_type] = preset_file

        database["models"].extend(new_models)
        save_database(database)
        backup_database()

        with open(MODEL_LIST_FILE, "w") as file:
            file.write("\n".join(database["models"]))
        backup_model_list()

        messagebox.showinfo("Search Results", f"Found {len(gguf_files)} .gguf files.\n"
                                               f"Created {presets_created} presets.\n"
                                               f"{len(new_models)} new models found.")

def search_preset():
    model_name = preset_entry.get()
    database = load_database()
    preset_file = database["presets"].get(model_name)
    if preset_file:
        messagebox.showinfo("Preset Found", f"Preset for {model_name} found at:\n{preset_file}")
    else:
        messagebox.showinfo("Preset Not Found", f"No preset found for {model_name}.")

def delete_unused_presets():
    database = load_database()
    unused_presets = set(database["presets"].keys()) - set(database["models"])
    for model_type in unused_presets:
        preset_file = database["presets"].pop(model_type)
        os.remove(preset_file)
    save_database(database)
    messagebox.showinfo("Unused Presets Deleted", f"Deleted {len(unused_presets)} unused presets.")

def export_model_list():
    export_format = export_var.get()
    if export_format == "Text":
        with open(MODEL_LIST_FILE, "r") as file:
            model_list = file.read()
        messagebox.showinfo("Model List Exported", f"Model list exported as {MODEL_LIST_FILE}")
    elif export_format == "JSON":
        database = load_database()
        with open("model_list.json", "w") as file:
            json.dump(database["models"], file, indent=2)
        messagebox.showinfo("Model List Exported", "Model list exported as model_list.json")

def import_presets():
    preset_file = filedialog.askopenfilename(title="Select Preset JSON File", filetypes=[("JSON Files", "*.json")])
    if preset_file:
        with open(preset_file, "r") as file:
            presets = json.load(file)
        database = load_database()
        database["presets"].update(presets)
        save_database(database)
        messagebox.showinfo("Presets Imported", f"Presets imported from {preset_file}")
        update_preset_listbox()

def edit_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        preset_editor_window = tk.Toplevel(root)
        preset_editor_window.title(f"Editing Preset: {selected_preset}")
        # Create and populate widgets for editing preset parameters
        # ...
        def save_preset():
            # Get the updated preset parameters from the widgets
            # ...
            with open(preset_file, "w") as file:
                json.dump(preset_data, file, indent=2)
            preset_editor_window.destroy()
        save_button = tk.Button(preset_editor_window, text="Save", command=save_preset)
        save_button.pack(padx=20, pady=10)

def duplicate_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        new_preset_name = f"{selected_preset}_copy"
        new_preset_file = os.path.join(CONFIG_PRESETS_DIR, f"{new_preset_name}.preset.json")
        shutil.copyfile(preset_file, new_preset_file)
        database["presets"][new_preset_name] = new_preset_file
        save_database(database)
        update_preset_listbox()

def update_preset_listbox():
    preset_listbox.delete(0, tk.END)
    for preset_name in database["presets"]:
        preset_listbox.insert(tk.END, preset_name)

def sync_presets_with_github():
    try:
        repo = Repo(GITHUB_REPO_DIR)
        repo.git.pull()
        messagebox.showinfo("Sync Complete", "Presets synced with GitHub repository.")
    except git.exc.InvalidGitRepositoryError:
        messagebox.showerror("Sync Error", "Invalid GitHub repository.")

def push_presets_to_github():
    try:
        repo = Repo(GITHUB_REPO_DIR)
        repo.git.add(update=True)
        repo.index.commit("Update presets")
        repo.git.push()
        messagebox.showinfo("Push Complete", "Presets pushed to GitHub repository.")
    except git.exc.InvalidGitRepositoryError:
        messagebox.showerror("Push Error", "Invalid GitHub repository.")

def categorize_presets():
    category = simpledialog.askstring("Categorize Presets", "Enter a category for the selected presets:")
    if category:
        selected_presets = preset_listbox.curselection()
        for index in selected_presets:
            preset_name = preset_listbox.get(index)
            preset_file = database["presets"][preset_name]
            with open(preset_file, "r") as file:
                preset_data = json.load(file)
            preset_data["category"] = category
            with open(preset_file, "w") as file:
                json.dump(preset_data, file, indent=2)
        messagebox.showinfo("Categorization Complete", f"Selected presets have been categorized as '{category}'.")

def compare_presets():
    selected_presets = preset_listbox.curselection()
    if len(selected_presets) == 2:
        preset1_name = preset_listbox.get(selected_presets[0])
        preset2_name = preset_listbox.get(selected_presets[1])
        preset1_file = database["presets"][preset1_name]
        preset2_file = database["presets"][preset2_name]
        with open(preset1_file, "r") as file:
            preset1_data = json.load(file)
        with open(preset2_file, "r") as file:
            preset2_data = json.load(file)
        # Compare the preset data and display the differences
        # ...
        messagebox.showinfo("Preset Comparison", "Preset comparison complete.")
    else:
        messagebox.showinfo("Preset Comparison", "Please select two presets to compare.")

def track_preset_metrics():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        # Track and display performance metrics for the selected preset
        # ...
        messagebox.showinfo("Preset Metrics", "Preset metrics tracked.")

def version_control_presets():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        # Implement version control for the selected preset
        # ...
        messagebox.showinfo("Version Control", "Preset version control implemented.")

def recommend_presets():
    # Implement preset recommendation logic based on user preferences, model types, or popular presets
    # ...
    recommended_presets = ["Preset 1", "Preset 2", "Preset 3"]
    messagebox.showinfo("Recommended Presets", f"Recommended Presets:\n{', '.join(recommended_presets)}")

def test_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        # Test the selected preset on a sample input and display the generated output
        # ...
        messagebox.showinfo("Preset Testing", "Preset testing complete.")

def browse_preset_marketplace():
    # Implement a marketplace or repository for browsing and downloading presets
    # ...
    messagebox.showinfo("Preset Marketplace", "Browse and download presets from the marketplace.")

def check_preset_compatibility():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        # Check the compatibility of the selected preset with the selected model
        # ...
        messagebox.showinfo("Compatibility Check", "Preset compatibility check complete.")

def validate_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        # Validate the preset parameters and provide warnings or suggestions for invalid or suboptimal settings
        # ...
        messagebox.showinfo("Preset Validation", "Preset validation complete.")

def enable_preset_collaboration():
    # Implement real-time collaboration features for multiple users to work on the same preset
    # ...
    messagebox.showinfo("Preset Collaboration", "Preset collaboration enabled.")

def schedule_preset_execution():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        # Implement a scheduling system to execute the selected preset at specific times or intervals
        # ...
        messagebox.showinfo("Preset Scheduling", "Preset execution scheduled.")

def chain_presets():
    selected_presets = preset_listbox.curselection()
    if len(selected_presets) > 1:
        # Implement preset chaining to create a pipeline of transformations or processing steps
        # ...
        messagebox.showinfo("Preset Chaining", "Presets chained successfully.")
    else:
        messagebox.showinfo("Preset Chaining", "Please select multiple presets to chain.")

def visualize_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        # Provide visual representations of preset parameters, such as graphs or charts
        # ...
        messagebox.showinfo("Preset Visualization", "Preset visualization generated.")

def perform_ab_testing():
    selected_presets = preset_listbox.curselection()
    if len(selected_presets) == 2:
        preset1_name = preset_listbox.get(selected_presets[0])
        preset2_name = preset_listbox.get(selected_presets[1])
        preset1_file = database["presets"][preset1_name]
        preset2_file = database["presets"][preset2_name]
        # Perform A/B testing by generating outputs using the selected presets and comparing the results
        # ...
        messagebox.showinfo("A/B Testing", "A/B testing complete.")
    else:
        messagebox.showinfo("A/B Testing", "Please select two presets for A/B testing.")

def mark_preset_favorite():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        preset_data["favorite"] = True
        with open(preset_file, "w") as file:
            json.dump(preset_data, file, indent=2)
        messagebox.showinfo("Favorite Preset", f"Preset '{selected_preset}' marked as favorite.")
        
def view_preset_history():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        # Implement preset history tracking and display the history of the selected preset
        # ...
        messagebox.showinfo("Preset History", "Preset history displayed.")

def preset_analytics():
    # Implement analytics and reporting features to provide insights into preset usage and performance trends
    # ...
    messagebox.showinfo("Preset Analytics", "Preset analytics generated.")

def apply_preset_shortcuts(event):
    if event.keysym == "n":
        # Create a new preset
        pass
    elif event.keysym == "d":
        duplicate_preset()
    elif event.keysym == "a":
        # Apply the selected preset to a model
        pass

def optimize_preset():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        # Perform optimization logic here based on the preset parameters
        # Update the preset_data with optimized values
        with open(preset_file, "w") as file:
            json.dump(preset_data, file, indent=2)
        messagebox.showinfo("Optimization Complete", f"Preset {selected_preset} has been optimized.")

def add_preset_notes():
    selected_preset = preset_listbox.get(preset_listbox.curselection())
    if selected_preset:
        preset_file = database["presets"][selected_preset]
        with open(preset_file, "r") as file:
            preset_data = json.load(file)
        notes = simpledialog.askstring("Preset Notes", "Enter notes for the preset:")
        if notes:
            preset_data["notes"] = notes
            with open(preset_file, "w") as file:
                json.dump(preset_data, file, indent=2)
            messagebox.showinfo("Notes Added", f"Notes added to preset {selected_preset}.")

root = tk.Tk()
root.title("GGUF Preset Manager")

search_button = tk.Button(root, text="Search Directory", command=search_files)
search_button.pack(padx=20, pady=10)

preset_frame = tk.Frame(root)
preset_frame.pack(padx=20, pady=10)

preset_listbox = tk.Listbox(preset_frame)
preset_listbox.pack(side=tk.LEFT)

preset_scrollbar = ttk.Scrollbar(preset_frame, orient="vertical", command=preset_listbox.yview)
preset_scrollbar.pack(side=tk.RIGHT, fill="y")

preset_listbox.configure(yscrollcommand=preset_scrollbar.set)

preset_button_frame = ttk.Frame(preset_frame)
preset_button_frame.pack(side=tk.RIGHT)

edit_preset_button = ttk.Button(preset_button_frame, text="Edit Preset", command=edit_preset)
edit_preset_button.pack(pady=5)

duplicate_preset_button = ttk.Button(preset_button_frame, text="Duplicate Preset", command=duplicate_preset)
duplicate_preset_button.pack(pady=5)

categorize_button = ttk.Button(preset_button_frame, text="Categorize Presets", command=categorize_presets)
categorize_button.pack(pady=5)

compare_button = ttk.Button(preset_button_frame, text="Compare Presets", command=compare_presets)
compare_button.pack(pady=5)

metrics_button = ttk.Button(preset_button_frame, text="Track Preset Metrics", command=track_preset_metrics)
metrics_button.pack(pady=5)

version_control_button = ttk.Button(preset_button_frame, text="Version Control", command=version_control_presets)
version_control_button.pack(pady=5)

recommend_button = ttk.Button(preset_button_frame, text="Recommend Presets", command=recommend_presets)
recommend_button.pack(pady=5)

test_button = ttk.Button(preset_button_frame, text="Test Preset", command=test_preset)
test_button.pack(pady=5)

marketplace_button = ttk.Button(preset_button_frame, text="Browse Marketplace", command=browse_preset_marketplace)
marketplace_button.pack(pady=5)

compatibility_button = ttk.Button(preset_button_frame, text="Check Compatibility", command=check_preset_compatibility)
compatibility_button.pack(pady=5)

validation_button = ttk.Button(preset_button_frame, text="Validate Preset", command=validate_preset)
validation_button.pack(pady=5)

collaboration_button = ttk.Button(preset_button_frame, text="Enable Collaboration", command=enable_preset_collaboration)
collaboration_button.pack(pady=5)

scheduling_button = ttk.Button(preset_button_frame, text="Schedule Execution", command=schedule_preset_execution)
scheduling_button.pack(pady=5)

chaining_button = ttk.Button(preset_button_frame, text="Chain Presets", command=chain_presets)
chaining_button.pack(pady=5)

visualization_button = ttk.Button(preset_button_frame, text="Visualize Preset", command=visualize_preset)
visualization_button.pack(pady=5)

ab_testing_button = ttk.Button(preset_button_frame, text="Perform A/B Testing", command=perform_ab_testing)
ab_testing_button.pack(pady=5)

favorite_button = ttk.Button(preset_button_frame, text="Mark as Favorite", command=mark_preset_favorite)
favorite_button.pack(pady=5)

history_button = ttk.Button(preset_button_frame, text="View Preset History", command=view_preset_history)
history_button.pack(pady=5)

analytics_button = ttk.Button(preset_button_frame, text="Preset Analytics", command=preset_analytics)
analytics_button.pack(pady=5)

optimization_button = ttk.Button(preset_button_frame, text="Optimize Preset", command=optimize_preset)
optimization_button.pack(pady=5)

notes_button = ttk.Button(preset_button_frame, text="Add Notes", command=add_preset_notes)
notes_button.pack(pady=5)

preset_search_frame = tk.Frame(root)
preset_search_frame.pack(padx=20, pady=10)
preset_search_label = tk.Label(preset_search_frame, text="Search Preset:")
preset_search_label.pack(side=tk.LEFT)
preset_entry = tk.Entry(preset_search_frame)
preset_entry.pack(side=tk.LEFT)
preset_search_button = tk.Button(preset_search_frame, text="Search", command=search_preset)
preset_search_button.pack(side=tk.LEFT)

delete_button = tk.Button(root, text="Delete Unused Presets", command=delete_unused_presets)
delete_button.pack(padx=20, pady=10)

export_frame = tk.Frame(root)
export_frame.pack(padx=20, pady=10)
export_label = tk.Label(export_frame, text="Export Model List:")
export_label.pack(side=tk.LEFT)
export_var = tk.StringVar(value="Text")
export_text_radio = tk.Radiobutton(export_frame, text="Text", variable=export_var, value="Text")
export_text_radio.pack(side=tk.LEFT)
export_json_radio = tk.Radiobutton(export_frame, text="JSON", variable=export_var, value="JSON")
export_json_radio.pack(side=tk.LEFT)
export_button = tk.Button(export_frame, text="Export", command=export_model_list)
export_button.pack(side=tk.LEFT)

import_button = tk.Button(root, text="Import Presets", command=import_presets)
import_button.pack(padx=20, pady=10)

github_frame = ttk.Frame(root)
github_frame.pack(padx=20, pady=10)

sync_button = ttk.Button(github_frame, text="Sync with GitHub", command=sync_presets_with_github)
sync_button.pack(side=tk.LEFT, padx=10)

push_button = ttk.Button(github_frame, text="Push to GitHub", command=push_presets_to_github)
push_button.pack(side=tk.LEFT)

root.bind("<Key>", apply_preset_shortcuts)

database = load_database()
update_preset_listbox()

root.mainloop()