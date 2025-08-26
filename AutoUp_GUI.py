import tkinter as tk
from tkinter import ttk, messagebox
from AutoUp_env import ftp_configs, BBS_URL_1, BBS_URL_2
import AutoUp_env

ftp_host_label = None

bg_color_default = "SystemButtonFace"
bg_color_ftp3 = "#C0B0D0"


def AutoUp_GUI(upload_results, NETWORK_DELAY):
    def refresh_table():
        for row in tree.get_children():
            tree.delete(row)

        for idx, entry in enumerate(upload_results):
            if entry["target_url"].startswith(BBS_URL_1):
                url_display = "히든타운"
            elif entry["target_url"].startswith(BBS_URL_2):
                url_display = "본좌세상"
            else:
                url_display = "기타"

            images_flag = "✅" if len(entry["images"]) > 0 else "❌"

            if entry["status"] == "success":
                status_icon = "✅"
            elif entry["status"] == "progress":
                status_icon = "🔄"
            else:
                status_icon = "❌"

            tree.insert("", "end", iid=idx, values=(
                entry["title"],
                len(entry["files"]),
                images_flag,
                status_icon,
                url_display
            ))

        if tree.get_children():
            tree.see(tree.get_children()[-1])

    def on_item_click(event):
        selected = tree.focus()
        if not selected:
            return
        idx = int(selected)
        entry = upload_results[idx]

        details_win = tk.Toplevel(root)
        details_win.title("상세 보기")

        tk.Label(details_win, text="Title:").grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(details_win, text=entry["title"]).grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Prefix:").grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(details_win, text=entry["prefix"]).grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Upload Time:").grid(row=2, column=0, sticky="w", pady=2)
        tk.Label(details_win, text=entry["upload_time"] or "-").grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Status:").grid(row=3, column=0, sticky="w", pady=2)
        tk.Label(details_win, text=entry["status"]).grid(row=3, column=1, sticky="w", pady=2)

        if entry["status"] == "failed":
            tk.Label(details_win, text="Error:", fg="red").grid(row=4, column=0, sticky="w", pady=2)
            tk.Label(details_win, text=entry["error_message"], fg="red").grid(row=4, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Target URL:").grid(row=5, column=0, sticky="w", pady=2)
        tk.Label(details_win, text=entry["target_url"]).grid(row=5, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Images:").grid(row=6, column=0, sticky="w", pady=2)
        img_text = "\n".join(entry["images"] or ["(none)"])
        tk.Label(details_win, text=img_text).grid(row=6, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Files:").grid(row=7, column=0, sticky="w", pady=2)
        file_text = "\n".join(entry["files"])
        tk.Label(details_win, text=file_text).grid(row=7, column=1, sticky="w", pady=2)

        tk.Label(details_win, text="Content:").grid(row=8, column=0, sticky="w", pady=2)
        text_box = tk.Text(details_win, height=5, width=80)
        text_box.grid(row=8, column=1, pady=2)
        text_box.insert("1.0", entry["content"])
        text_box.config(state="disabled")

        tk.Button(details_win, text="닫기", command=details_win.destroy).grid(row=9, column=1, pady=10)

    def delete_all():
        upload_results.clear()
        refresh_table()

    def auto_refresh():
        refresh_table()
        root.after(int(NETWORK_DELAY * 1000), auto_refresh)

    def set_bg_color(color):
        root.configure(bg=color)
        tree_frame.configure(bg=color)
        bottom_frame.configure(bg=color)
        control_frame.configure(bg=color)
        ftp_button_frame.configure(bg=color)
        ftp_host_label.configure(bg=color)
        delete_btn.configure(bg="yellow")

    def set_selected_ftp(name):
        AutoUp_env.selected_ftp_name = name
        ftp_host = ftp_configs[name]["host"]
        ftp_host_label.config(text=f"Server: {ftp_host}")
        if name == "FTP3":
            set_bg_color(bg_color_ftp3)
        else:
            set_bg_color(bg_color_default)

    root = tk.Tk()
    root.title("Auto Uploader V2.1")
    root.geometry("520x270")

    columns = ("Title", "File", "Img", "Stat", "Upload Club")
    tree_frame = tk.Frame(root, height=200)
    tree_frame.pack_propagate(False)
    tree_frame.pack(side="top", fill="both", padx=10, pady=(10, 0))

    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        if col == "Title":
            tree.column(col, width=290)
        elif col == "File":
            tree.column(col, width=20, anchor="center")
        elif col == "Img":
            tree.column(col, width=20, anchor="center")
        elif col == "Stat":
            tree.column(col, width=20, anchor="center")
        elif col == "Upload Club":
            tree.column(col, width=60)
    tree.bind("<Double-1>", on_item_click)

    tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    tree_scrollbar.pack(side="right", fill="y")

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side="bottom", fill="x", pady=(3, 0))

    control_frame = tk.Frame(bottom_frame)
    control_frame.pack(side="top", fill="x", padx=5)

    delete_btn = tk.Button(control_frame, text="Delete All", command=delete_all, bg="yellow")
    delete_btn.pack(side="left", padx=(5, 0))

    ftp_button_frame = tk.Frame(control_frame)
    ftp_button_frame.pack(side="right")

    ftp_name_map = {"FTP1": "90", "FTP2": "159", "FTP3": "Test"}
    button_width = 6

    for ftp_key in ftp_configs.keys():
        label = ftp_name_map.get(ftp_key, ftp_key)
        tk.Button(ftp_button_frame, text=label, width=button_width, command=lambda n=ftp_key: set_selected_ftp(n)).pack(side="left", padx=2)

    ftp_host_label = tk.Label(bottom_frame, text=f"Server: {ftp_configs[AutoUp_env.selected_ftp_name]['host']}")
    ftp_host_label.pack(side="top", pady=(1, 0))

    refresh_table()
    auto_refresh()
    root.mainloop()
