import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

CONFIG_PRESETS_DIR = r"C:\Users\Admin\.cache\lm-studio\config-presets"
DATABASE_FILE = "database.json"
MODEL_LIST_FILE = "model_list.txt"

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

root = tk.Tk()
root.title("GGUF Preset Manager")

search_button = tk.Button(root, text="Search Directory", command=search_files)
search_button.pack(padx=20, pady=10)

preset_frame = tk.Frame(root)
preset_frame.pack(padx=20, pady=10)
preset_label = tk.Label(preset_frame, text="Search Preset:")
preset_label.pack(side=tk.LEFT)
preset_entry = tk.Entry(preset_frame)
preset_entry.pack(side=tk.LEFT)
preset_search_button = tk.Button(preset_frame, text="Search", command=search_preset)
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

root.mainloop()