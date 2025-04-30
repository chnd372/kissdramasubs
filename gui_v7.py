import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import threading
import datetime
import os
import platform

LOG_FILE = "kisskh_gui_log.txt"
DEFAULT_SCRIPT = "cli_v8.py"

script_path = DEFAULT_SCRIPT
if not os.path.exists(script_path):
    script_path = filedialog.askopenfilename(title="Select Python Script", filetypes=[("Python files", "*.py")])

def log(message):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")

def run_downloader():
    args = ["python", script_path]

    if start_id.get():
        args.append(start_id.get())
    if end_id.get():
        args.extend(["--end-id", end_id.get()])
    if ep.get():
        args.extend(["--ep", ep.get()])
    if threads.get():
        args.extend(["--threads", threads.get()])
    if langs.get():
        clean_langs = langs.get().replace(".", ",").replace(" ", "").replace("|", ",")
        args.extend(["--langs", clean_langs])
    if meta_skip.get():
        args.append("--meta-skip")
    if csv_option.get():
        args.extend(["--csv", csv_option.get()])

    log("Running: " + " ".join(args))

    
    def target():
        try:
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo
            )
            completed = False
            for line in process.stdout:
                log(line.strip())
                output_text.insert(tk.END, line)
                output_text.see(tk.END)
                if "All Subtitles Download Completed" in line:
                    completed = True
            process.wait()
            log("Download completed.")
            if completed:
                messagebox.showinfo("Success", "All subtitles downloaded and saved successfully!")
        except Exception as e:
            log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    threading.Thread(target=target).start()

def new_script():
    global script_path
    start_id.set("")
    end_id.set("")
    ep.set("")
    threads.set("6")
    langs.set("")
    csv_option.set("keep")
    meta_skip.set(False)
    output_text.delete("1.0", tk.END)

    script_path = DEFAULT_SCRIPT if os.path.exists(DEFAULT_SCRIPT) else filedialog.askopenfilename(title="Select Python Script", filetypes=[("Python files", "*.py")])
    script_label.config(text=f"Using Script: {os.path.basename(script_path)}")
    log("[INFO] New script session started")

def clear_log_file():
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
        output_text.insert(tk.END, "[INFO] Log file cleared.\n")

root = tk.Tk()
root.title("KissKH Subtitle Downloader GUI")
root.geometry("860x720")
root.configure(bg="#f7f7f7")

start_id = tk.StringVar()
end_id = tk.StringVar()
ep = tk.StringVar()
threads = tk.StringVar(value="6")
langs = tk.StringVar()
csv_option = tk.StringVar(value="keep")
meta_skip = tk.BooleanVar()

frame = tk.LabelFrame(root, text="Downloader Options", bg="#f7f7f7", padx=10, pady=10)
frame.pack(padx=15, pady=10, fill="x")

script_label = tk.Label(frame, text=f"Using Script: {os.path.basename(script_path)}", bg="#f7f7f7", fg="#333", font=("Segoe UI", 9, "italic"))
script_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

labels = ["Start Drama ID:", "End Drama ID:", "Episodes (e.g. 1,2,3):", "Languages (e.g. en,hi):", "Threads:"]
vars = [start_id, end_id, ep, langs, threads]

for i, (text, var) in enumerate(zip(labels, vars), start=1):
    tk.Label(frame, text=text, bg="#f7f7f7").grid(row=i, column=0, sticky="w", pady=2)
    tk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, pady=2, sticky="w")

meta_skip_chk = tk.Checkbutton(frame, text="Use existing metadata (meta-skip)", variable=meta_skip, bg="#f7f7f7")
meta_skip_chk.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

csv_label = tk.Label(frame, text="CSV File Option:", bg="#f7f7f7")
csv_label.grid(row=7, column=0, sticky="w")
csv_menu = ttk.Combobox(frame, textvariable=csv_option, values=["keep", "delete"], state="readonly", width=27)
csv_menu.grid(row=7, column=1, sticky="w")

run_btn = tk.Button(frame, text="Run Downloader", command=run_downloader, bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"))
run_btn.grid(row=8, column=0, pady=10, sticky="w")

reset_btn = tk.Button(frame, text="New Script", command=new_script, bg="#6c757d", fg="white", font=("Segoe UI", 10, "bold"))
reset_btn.grid(row=8, column=1, pady=10, sticky="w")

clear_log_btn = tk.Button(frame, text="Clear Log File", command=clear_log_file, bg="#dc3545", fg="white", font=("Segoe UI", 10, "bold"))
clear_log_btn.grid(row=8, column=2, pady=10, sticky="w")

output_frame = tk.LabelFrame(root, text="Output Log", bg="#f7f7f7")
output_frame.pack(padx=15, pady=5, fill="both", expand=True)

output_text = tk.Text(output_frame, wrap="word", bg="white", fg="black")
output_text.pack(padx=5, pady=5, fill="both", expand=True)

root.mainloop()
