import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
from loguru import logger

CORRECT_PIN = "6777"
_authenticated = False

def ask_pin_gui() -> bool:
    result = {"success": False}

    def show():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # custom PIN dialog
        dialog = tk.Toplevel(root)
        dialog.title("NAVIX AI — Authentication")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.configure(bg="#0a0c10")

        tk.Label(
            dialog,
            text="🤖 NAVIX AI",
            font=("Arial", 16, "bold"),
            fg="#00d4aa",
            bg="#0a0c10"
        ).pack(pady=10)

        tk.Label(
            dialog,
            text="Enter PIN to activate",
            font=("Arial", 11),
            fg="#e2e8f0",
            bg="#0a0c10"
        ).pack()

        pin_var = tk.StringVar()
        entry = tk.Entry(
            dialog,
            textvariable=pin_var,
            show="●",
            font=("Arial", 18),
            width=10,
            justify="center",
            bg="#0f1218",
            fg="#00d4aa",
            insertbackground="#00d4aa",
            relief="flat",
            bd=5
        )
        entry.pack(pady=15)
        entry.focus()

        def check_pin(event=None):
            if pin_var.get() == CORRECT_PIN:
                result["success"] = True
                dialog.destroy()
                root.destroy()
            else:
                messagebox.showerror("Wrong PIN", "Incorrect PIN. Try again.")
                pin_var.set("")
                entry.focus()

        def cancel(event=None):
            dialog.destroy()
            root.destroy()

        entry.bind("<Return>", check_pin)
        entry.bind("<Escape>", cancel)

        tk.Button(
            dialog,
            text="Unlock",
            command=check_pin,
            bg="#00d4aa",
            fg="#0a0c10",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=20,
            pady=5
        ).pack()

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        root.mainloop()

    thread = threading.Thread(target=show, daemon=True)
    thread.start()
    thread.join(timeout=30)

    return result["success"]

def authenticate() -> bool:
    global _authenticated
    logger.info("Requesting PIN authentication")
    success = ask_pin_gui()
    if success:
        _authenticated = True
        logger.info("PIN authentication successful")
    else:
        logger.warning("PIN authentication failed or cancelled")
    return success

def is_authenticated() -> bool:
    return _authenticated

def lock():
    global _authenticated
    _authenticated = False
    logger.info("NAVIX locked")