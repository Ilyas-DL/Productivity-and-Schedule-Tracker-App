

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import calendar


class ProductivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Productivity & Schedule Tracker")

        # Center the window on launch
        self.root.update_idletasks()
        window_width = 1400
        window_height = 900
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)

        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.minsize(1024, 768)

        # Modern Flat Color Palette
        self.BG_APP = "#F0F2F5"
        self.BG_CARD = "#FFFFFF"
        self.BG_SIDEBAR = "#1E293B"
        self.BTN_ACCENT = "#2563EB"
        self.BTN_HOVER = "#1D4ED8"  # Darker shade for pro-buttons
        self.TEXT_MAIN = "#0F172A"
        self.TEXT_MUTED = "#94A3B8"
        self.TEXT_LIGHT = "#FFFFFF"

        # Delete Button Colors
        self.DEL_BG_HOVER = "#FEE2E2"
        self.DEL_FG_HOVER = "#DC2626"

        # 30 Curated Colors for Events & Tasks
        self.COLORS_30 = [
            "#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16", "#22C55E",
            "#10B981", "#14B8A6", "#06B6D4", "#0EA5E9", "#3B82F6", "#2563EB",
            "#4F46E5", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF", "#EC4899",
            "#F43F5E", "#E11D48", "#9F1239", "#7C2D12", "#713F12", "#3F6212",
            "#14532D", "#134E4A", "#164E63", "#1E3A8A", "#312E81", "#4C1D95"
        ]

        self.root.configure(bg=self.BG_APP)

        # Data initialization
        self.data_file = "tracker_data.json"
        self.data = {"todos": [], "events": []}
        self.load_data()

        # Calendar & App State
        self.cal_year = datetime.now().year
        self.cal_month = datetime.now().month
        self.highlighted_date = None
        self.show_today = True
        self.show_events = True
        self.current_event_color = self.BTN_ACCENT
        self.current_todo_color = self.BG_CARD

        # Drag and Drop State
        self.drag_win = None
        self.drag_start_idx = None

        # Build the User Interface
        self.build_ui()

        # Reminders check
        self.check_reminders()
        self.root.after(3600000, self.check_reminders)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as file:
                    loaded = json.load(file)
                    self.data["todos"] = loaded.get("todos", [])
                    self.data["events"] = loaded.get("events", [])
            except json.JSONDecodeError:
                pass

    def save_data(self):
        with open(self.data_file, 'w') as file:
            json.dump(self.data, file, indent=4)

    def lighten_color(self, hex_color, factor=0.85):
        """Blends a hex color with white to make it a light pastel background color."""
        if hex_color.upper() == "#FFFFFF":
            return hex_color
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def build_ui(self):
        # 1. Sidebar
        sidebar = tk.Frame(self.root, bg=self.BG_SIDEBAR, width=260)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        title_lbl = tk.Label(sidebar, text="WORKSPACE", font=("Segoe UI", 16, "bold"),
                             bg=self.BG_SIDEBAR, fg=self.TEXT_LIGHT, pady=30)
        title_lbl.pack(fill=tk.X)

        self.btn_nav_todo = tk.Button(sidebar, text="✓  To-Do List", font=("Segoe UI", 13),
                                      bg="#334155", fg=self.TEXT_LIGHT, relief="flat", bd=0,
                                      pady=15, anchor="w", padx=35, cursor="hand2",
                                      command=lambda: self.show_frame(self.todo_frame))
        self.btn_nav_todo.pack(fill=tk.X, pady=5)

        self.btn_nav_cal = tk.Button(sidebar, text="📅  Calendar", font=("Segoe UI", 13),
                                     bg=self.BG_SIDEBAR, fg=self.TEXT_LIGHT, relief="flat", bd=0,
                                     pady=15, anchor="w", padx=35, cursor="hand2",
                                     command=lambda: self.show_frame(self.calendar_frame))
        self.btn_nav_cal.pack(fill=tk.X, pady=5)

        # 2. Main Content Area
        self.main_content = tk.Frame(self.root, bg=self.BG_APP)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.main_content.grid_rowconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        self.todo_frame = tk.Frame(self.main_content, bg=self.BG_APP)
        self.calendar_frame = tk.Frame(self.main_content, bg=self.BG_APP)

        self.todo_frame.grid(row=0, column=0, sticky="nsew")
        self.calendar_frame.grid(row=0, column=0, sticky="nsew")

        self.build_todo_page()
        self.build_calendar_page()

        self.show_frame(self.todo_frame)

    def show_frame(self, frame):
        frame.tkraise()
        if frame == self.todo_frame:
            self.btn_nav_todo.configure(bg="#334155")
            self.btn_nav_cal.configure(bg=self.BG_SIDEBAR)
        else:
            self.btn_nav_todo.configure(bg=self.BG_SIDEBAR)
            self.btn_nav_cal.configure(bg="#334155")
            self.clear_calendar_highlight()

    def create_scrollable_container(self, parent):
        canvas = tk.Canvas(parent, bg=self.BG_APP, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.BG_APP)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_withtag("all")[0], width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Strict 35px padding matches the top elements exactly so borders align seamlessly
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(35, 0), pady=(0, 15))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 15), padx=(0, 35))

        return scrollable_frame

    # --- To-Do Page ---
    def build_todo_page(self):
        tk.Label(self.todo_frame, text="My Tasks", font=("Segoe UI", 26, "bold"), bg=self.BG_APP,
                 fg=self.TEXT_MAIN).pack(anchor=tk.W, padx=35, pady=(40, 15))

        # We restructure the layout slightly with a grid to guarantee the input bar matches the exact width of the cards
        todo_content = tk.Frame(self.todo_frame, bg=self.BG_APP)
        todo_content.pack(fill=tk.BOTH, expand=True)
        todo_content.columnconfigure(0, weight=1)
        todo_content.columnconfigure(1, weight=0)

        # We force an exact vertical height (42px) to guarantee inputs/buttons have matching proportions
        input_frame = tk.Frame(todo_content, bg=self.BG_APP, height=42)
        input_frame.grid(row=0, column=0, sticky="ew", padx=(35, 0), pady=(0, 15))
        input_frame.pack_propagate(False)

        # Title entry
        tk.Label(input_frame, text="Task:", font=('Segoe UI', 11, 'bold'), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(
            side=tk.LEFT, padx=(0, 8))
        self.todo_entry = tk.Entry(input_frame, font=('Segoe UI', 12), bg=self.BG_CARD, relief="flat",
                                   highlightbackground="#CBD5E1", highlightcolor=self.BTN_ACCENT, highlightthickness=1)
        self.todo_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        self.todo_entry.bind("<Return>", lambda event: self.add_todo())

        # Type entry
        tk.Label(input_frame, text="Type:", font=('Segoe UI', 11, 'bold'), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(
            side=tk.LEFT, padx=(0, 8))
        self.todo_type_entry = tk.Entry(input_frame, font=('Segoe UI', 12), bg=self.BG_CARD, relief="flat",
                                        highlightbackground="#CBD5E1", highlightcolor=self.BTN_ACCENT,
                                        highlightthickness=1, width=15)
        self.todo_type_entry.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        self.todo_type_entry.bind("<Return>", lambda event: self.add_todo())

        # Color picker
        tk.Label(input_frame, text="Color:", font=('Segoe UI', 11, 'bold'), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(
            side=tk.LEFT, padx=(0, 8))

        # Wrapped in a frame so the color block has a nice uniform outline just like the entries
        color_wrapper = tk.Frame(input_frame, highlightbackground="#CBD5E1", highlightthickness=1)
        color_wrapper.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        self.btn_todo_color = tk.Button(color_wrapper, bg=self.current_todo_color, width=4, relief="flat", bd=0,
                                        cursor="hand2",
                                        command=lambda: self.open_color_picker(self.set_todo_color))
        self.btn_todo_color.pack(fill=tk.BOTH, expand=True)

        # Add Button
        self.btn_add_task = tk.Button(input_frame, text="➕ Add Task", bg=self.BTN_ACCENT, fg=self.TEXT_LIGHT,
                                      font=('Segoe UI', 11, 'bold'), relief="flat", bd=0, cursor="hand2", padx=20,
                                      command=self.add_todo)
        self.btn_add_task.pack(side=tk.LEFT, fill=tk.Y)

        # Add hover interaction to Add button for a Pro look
        self.btn_add_task.bind("<Enter>", lambda e: e.widget.config(bg=self.BTN_HOVER))
        self.btn_add_task.bind("<Leave>", lambda e: e.widget.config(bg=self.BTN_ACCENT))

        canvas = tk.Canvas(todo_content, bg=self.BG_APP, highlightthickness=0)
        scrollbar = ttk.Scrollbar(todo_content, orient="vertical", command=canvas.yview)
        self.todo_list_frame = tk.Frame(canvas, bg=self.BG_APP)

        self.todo_list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.todo_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_withtag("all")[0], width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # The scrollable canvas gets packed strictly beneath the input frame
        canvas.grid(row=1, column=0, sticky="nsew", padx=(35, 0), pady=(0, 15))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 35), pady=(0, 15))
        todo_content.rowconfigure(1, weight=1)

        self.refresh_todo_list()

    def refresh_todo_list(self):
        for widget in self.todo_list_frame.winfo_children(): widget.destroy()

        for idx, task in enumerate(self.data["todos"]):
            # Get chosen color, default to pure white. Lighten it dynamically to keep readability.
            base_color = task.get("color", self.BG_CARD)
            light_bg = self.lighten_color(base_color)

            # Increased padding for a better spacing feel
            card = tk.Frame(self.todo_list_frame, bg=light_bg, padx=15, pady=12, highlightbackground="#E2E8F0",
                            highlightthickness=1)
            card.pack(fill=tk.X, pady=(0, 8))

            drag_handle = tk.Label(card, text="⣿", font=("Segoe UI", 16), fg="#CBD5E1", bg=light_bg, cursor="fleur")
            drag_handle.pack(side=tk.LEFT, padx=(0, 10))
            drag_handle.bind("<ButtonPress-1>", lambda e, i=idx: self.on_drag_start(e, i))
            drag_handle.bind("<B1-Motion>", self.on_drag_motion)
            drag_handle.bind("<ButtonRelease-1>", lambda e, i=idx: self.on_drag_release(e, i))

            is_done = task["done"]
            icon = "☑" if is_done else "☐"
            color = self.BTN_ACCENT if is_done else self.TEXT_MUTED
            text_color = self.TEXT_MUTED if is_done else self.TEXT_MAIN

            chk_btn = tk.Label(card, text=icon, font=("Segoe UI", 16), fg=color, bg=light_bg, cursor="hand2")
            chk_btn.pack(side=tk.LEFT, padx=(0, 10))
            chk_btn.bind("<Button-1>", lambda e, i=idx: self.toggle_todo(i))

            text_container = tk.Frame(card, bg=light_bg, cursor="hand2")
            text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
            text_container.bind("<Button-1>", lambda e, i=idx: self.toggle_todo(i))

            task_lbl = tk.Label(text_container, text=task["title"], font=("Segoe UI", 12), fg=text_color,
                                bg=light_bg, cursor="hand2")
            task_lbl.pack(side=tk.LEFT)
            task_lbl.bind("<Button-1>", lambda e, i=idx: self.toggle_todo(i))

            if is_done:
                strike_line = tk.Frame(task_lbl, bg=self.TEXT_MUTED, height=2)
                strike_line.place(relx=0, rely=0.5, relwidth=1)
                strike_line.bind("<Button-1>", lambda e, i=idx: self.toggle_todo(i))

            # Delete button logic
            del_btn = tk.Label(card, text="✕", font=("Segoe UI", 13, "bold"), fg=self.TEXT_MUTED, bg=light_bg,
                               cursor="hand2", width=3, pady=2)
            del_btn.pack(side=tk.RIGHT, padx=(5, 0))
            del_btn.bind("<Button-1>", lambda e, i=idx: self.delete_todo(i))
            del_btn.bind("<Enter>", lambda e, btn=del_btn: btn.config(bg=self.DEL_BG_HOVER, fg=self.DEL_FG_HOVER))
            del_btn.bind("<Leave>", lambda e, btn=del_btn, c=light_bg: btn.config(bg=c, fg=self.TEXT_MUTED))

            # Display the Task Type on the far right (darker text, TEXT_MAIN used)
            task_type = task.get("type", "")
            if task_type:
                type_lbl = tk.Label(card, text=task_type.upper(), font=("Segoe UI", 11, "bold"), fg=self.TEXT_MAIN,
                                    bg=light_bg)
                type_lbl.pack(side=tk.RIGHT, padx=(10, 15))
                type_lbl.bind("<Button-1>", lambda e, i=idx: self.toggle_todo(i))

    def on_drag_start(self, event, idx):
        if self.drag_win: return
        self.drag_start_idx = idx
        task = self.data["todos"][idx]

        self.drag_win = tk.Toplevel(self.root)
        self.drag_win.overrideredirect(True)
        self.drag_win.attributes('-alpha', 0.8)

        frame = tk.Frame(self.drag_win, bg=self.BTN_ACCENT, padx=15, pady=8, highlightthickness=1,
                         highlightbackground=self.BTN_ACCENT)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=task["title"], font=("Segoe UI", 12, "bold"), fg=self.TEXT_LIGHT,
                 bg=self.BTN_ACCENT).pack()

        self.drag_win.geometry(f"+{event.x_root + 15}+{event.y_root - 15}")

    def on_drag_motion(self, event):
        if self.drag_win:
            self.drag_win.geometry(f"+{event.x_root + 15}+{event.y_root - 15}")

    def on_drag_release(self, event, idx):
        if not self.drag_win: return
        self.drag_win.destroy()
        self.drag_win = None

        cards = self.todo_list_frame.winfo_children()
        new_idx = len(self.data["todos"])

        for i, card in enumerate(cards):
            card_mid_y = card.winfo_rooty() + (card.winfo_height() / 2)
            if event.y_root < card_mid_y:
                new_idx = i
                break

        if new_idx == self.drag_start_idx or new_idx == self.drag_start_idx + 1:
            return

        task = self.data["todos"].pop(self.drag_start_idx)
        if new_idx > self.drag_start_idx:
            new_idx -= 1

        self.data["todos"].insert(new_idx, task)
        self.save_data()
        self.refresh_todo_list()

    def add_todo(self):
        task_text = self.todo_entry.get().strip()
        task_type = self.todo_type_entry.get().strip()
        if task_text:
            self.data["todos"].append({
                "title": task_text,
                "type": task_type,
                "color": self.current_todo_color,
                "done": False
            })
            self.save_data()

            # Reset UI inputs
            self.todo_entry.delete(0, tk.END)
            self.todo_type_entry.delete(0, tk.END)
            self.current_todo_color = self.BG_CARD
            self.btn_todo_color.config(bg=self.current_todo_color)

            self.refresh_todo_list()

    def toggle_todo(self, idx):
        self.data["todos"][idx]["done"] = not self.data["todos"][idx]["done"]
        self.save_data()
        self.refresh_todo_list()

    def delete_todo(self, idx):
        del self.data["todos"][idx]
        self.save_data()
        self.refresh_todo_list()

    # --- Shared Color Picker ---
    def open_color_picker(self, callback):
        if hasattr(self, 'color_win') and self.color_win and self.color_win.winfo_exists():
            self.color_win.destroy()

        self.color_win = tk.Toplevel(self.root)
        self.color_win.title("Select Color")
        self.color_win.configure(bg=self.BG_CARD)
        self.color_win.resizable(False, False)

        # Focus stealing to make it feel like a dropdown popup
        self.color_win.focus_force()

        grid_frame = tk.Frame(self.color_win, bg=self.BG_CARD, padx=10, pady=10)
        grid_frame.pack()

        # Added White option explicitly to the picker as well since it acts as the default
        colors_to_show = self.COLORS_30 + ["#FFFFFF"]
        for i, color in enumerate(colors_to_show):
            row, col = divmod(i, 6)
            btn = tk.Button(grid_frame, bg=color, width=3, height=1, bd=1 if color == "#FFFFFF" else 0,
                            relief="flat" if color != "#FFFFFF" else "solid", cursor="hand2",
                            command=lambda c=color: self.select_color(c, callback))
            btn.grid(row=row, column=col, padx=3, pady=3)

        # Ensure the layout is updated before retrieving width/height
        self.color_win.update_idletasks()

        # Calculate exact center of the monitor screen
        win_width = self.color_win.winfo_reqwidth()
        win_height = self.color_win.winfo_reqheight()
        screen_width = self.color_win.winfo_screenwidth()
        screen_height = self.color_win.winfo_screenheight()

        pos_x = int((screen_width / 2) - (win_width / 2))
        pos_y = int((screen_height / 2) - (win_height / 2))

        # Position the window
        self.color_win.geometry(f"+{pos_x}+{pos_y}")

    def select_color(self, color, callback):
        callback(color)
        self.color_win.destroy()

    def set_event_color(self, color):
        self.current_event_color = color
        self.btn_color_picker.config(bg=color)

    def set_todo_color(self, color):
        self.current_todo_color = color
        self.btn_todo_color.config(bg=color)

    # --- Calendar Page ---
    def build_calendar_page(self):
        tk.Label(self.calendar_frame, text="Schedule Dashboard", font=("Segoe UI", 26, "bold"), bg=self.BG_APP,
                 fg=self.TEXT_MAIN).pack(anchor=tk.W, padx=35, pady=(40, 15))

        content_frame = tk.Frame(self.calendar_frame, bg=self.BG_APP)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=35)

        left_pane = tk.Frame(content_frame, bg=self.BG_APP, width=400)
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 25))

        right_pane = tk.Frame(content_frame, bg=self.BG_APP)
        right_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_visual_calendar(left_pane)

        tk.Label(left_pane, text="Add New Event", font=("Segoe UI", 14, "bold"), bg=self.BG_APP,
                 fg=self.TEXT_MAIN).pack(anchor=tk.W, pady=(30, 15))

        tk.Label(left_pane, text="Title:", font=('Segoe UI', 10), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(anchor=tk.W)
        self.evt_title = tk.Entry(left_pane, font=('Segoe UI', 12), relief="flat", highlightbackground="#CBD5E1",
                                  highlightthickness=1)
        self.evt_title.pack(fill=tk.X, pady=(0, 15), ipady=5)

        date_time_frame = tk.Frame(left_pane, bg=self.BG_APP)
        date_time_frame.pack(fill=tk.X, pady=(0, 15))

        d_frame = tk.Frame(date_time_frame, bg=self.BG_APP)
        d_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        tk.Label(d_frame, text="Date (DD-MM-YYYY):", font=('Segoe UI', 10), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(
            anchor=tk.W)
        self.evt_date = tk.Entry(d_frame, font=('Segoe UI', 12), relief="flat", highlightbackground="#CBD5E1",
                                 highlightthickness=1)
        self.evt_date.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.evt_date.pack(fill=tk.X, ipady=5)

        t_frame = tk.Frame(date_time_frame, bg=self.BG_APP)
        t_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))
        tk.Label(t_frame, text="Time:", font=('Segoe UI', 10), bg=self.BG_APP, fg=self.TEXT_MAIN).pack(anchor=tk.W)
        self.evt_time = tk.Entry(t_frame, font=('Segoe UI', 12), relief="flat", highlightbackground="#CBD5E1",
                                 highlightthickness=1)
        self.evt_time.insert(0, "12:00")
        self.evt_time.pack(fill=tk.X, ipady=5)

        c_frame = tk.Frame(left_pane, bg=self.BG_APP)
        c_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(c_frame, text="Event Color (Click to change):", font=('Segoe UI', 10), bg=self.BG_APP,
                 fg=self.TEXT_MAIN).pack(side=tk.LEFT)
        self.btn_color_picker = tk.Button(c_frame, bg=self.current_event_color, width=4, relief="flat", cursor="hand2",
                                          command=lambda: self.open_color_picker(self.set_event_color))
        self.btn_color_picker.pack(side=tk.LEFT, padx=(10, 0), fill=tk.Y, pady=2)

        tk.Button(left_pane, text="➕ Add Event", bg=self.BTN_ACCENT, fg=self.TEXT_LIGHT,
                  font=('Segoe UI', 11, 'bold'), relief="flat", cursor="hand2", pady=8, command=self.add_event).pack(
            fill=tk.X)

        self.calendar_list_frame = self.create_scrollable_container(right_pane)
        self.bind_background_clicks(self.calendar_frame)
        self.refresh_event_list()

    def bind_background_clicks(self, widget):
        if isinstance(widget, (tk.Frame, tk.Label, tk.Canvas, tk.Entry)):
            widget.bind("<Button-1>", lambda e: self.clear_calendar_highlight(), add="+")
        for child in widget.winfo_children():
            self.bind_background_clicks(child)

    def clear_calendar_highlight(self, event=None):
        if self.highlighted_date is not None:
            self.highlighted_date = None
            self.refresh_visual_calendar()

    def build_visual_calendar(self, parent):
        cal_container = tk.Frame(parent, bg=self.BG_CARD, padx=20, pady=20, highlightbackground="#E2E8F0",
                                 highlightthickness=1)
        cal_container.pack(fill=tk.X)

        header_frame = tk.Frame(cal_container, bg=self.BG_CARD)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Button(header_frame, text="◀", bg=self.BG_CARD, fg=self.TEXT_MAIN, relief="flat", cursor="hand2", bd=0,
                  command=self.prev_month).pack(side=tk.LEFT)
        self.month_year_lbl = tk.Label(header_frame, text="", font=("Segoe UI", 12, "bold"), bg=self.BG_CARD,
                                       fg=self.TEXT_MAIN)
        self.month_year_lbl.pack(side=tk.LEFT, expand=True)
        tk.Button(header_frame, text="▶", bg=self.BG_CARD, fg=self.TEXT_MAIN, relief="flat", cursor="hand2", bd=0,
                  command=self.next_month).pack(side=tk.RIGHT)

        days_frame = tk.Frame(cal_container, bg=self.BG_CARD)
        days_frame.pack(fill=tk.BOTH, expand=True)

        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, d in enumerate(days):
            tk.Label(days_frame, text=d, font=("Segoe UI", 9, "bold"), bg=self.BG_CARD, fg=self.TEXT_MUTED,
                     width=4).grid(row=0, column=i, pady=5)
            days_frame.grid_columnconfigure(i, weight=1, uniform="day")

        self.day_buttons = []
        for row in range(6):
            row_btns = []
            for col in range(7):
                btn = tk.Button(days_frame, text="", font=("Segoe UI", 10), width=4, height=1, relief="flat", bd=0,
                                bg=self.BG_CARD, cursor="hand2")
                btn.grid(row=row + 1, column=col, padx=2, pady=2, sticky="nsew")
                row_btns.append(btn)
            self.day_buttons.append(row_btns)

        # Togglers
        toggles_frame = tk.Frame(cal_container, bg=self.BG_CARD)
        toggles_frame.pack(fill=tk.X, pady=(20, 0))

        self.btn_events_toggle = tk.Button(toggles_frame, text="Highlight Future Events: ON",
                                           font=("Segoe UI", 10, "bold"),
                                           bg="#F1F5F9", fg=self.BTN_ACCENT, bd=0,
                                           relief="flat", cursor="hand2", pady=8,
                                           activebackground="#E2E8F0", activeforeground=self.BTN_ACCENT,
                                           command=self.toggle_events)
        self.btn_events_toggle.pack(fill=tk.X, pady=(0, 5))

        self.btn_today_toggle = tk.Button(toggles_frame, text="Current Day Highlight: ON",
                                          font=("Segoe UI", 10, "bold"),
                                          bg="#F1F5F9", fg=self.BTN_ACCENT, bd=0,
                                          relief="flat", cursor="hand2", pady=8,
                                          activebackground="#E2E8F0", activeforeground=self.BTN_ACCENT,
                                          command=self.toggle_today)
        self.btn_today_toggle.pack(fill=tk.X)

        self.refresh_visual_calendar()

    def toggle_events(self):
        self.show_events = not self.show_events
        if self.show_events:
            self.btn_events_toggle.config(
                text="Highlight Future Events: ON",
                bg="#F1F5F9", fg=self.BTN_ACCENT,
                activebackground="#E2E8F0", activeforeground=self.BTN_ACCENT
            )
        else:
            self.btn_events_toggle.config(
                text="Highlight Future Events: OFF",
                bg="#F8FAFC", fg=self.TEXT_MUTED,
                activebackground="#F1F5F9", activeforeground=self.TEXT_MAIN
            )
        self.refresh_visual_calendar()

    def toggle_today(self):
        self.show_today = not self.show_today
        if self.show_today:
            self.btn_today_toggle.config(
                text="Current Day Highlight: ON",
                bg="#F1F5F9", fg=self.BTN_ACCENT,
                activebackground="#E2E8F0", activeforeground=self.BTN_ACCENT
            )
        else:
            self.btn_today_toggle.config(
                text="Current Day Highlight: OFF",
                bg="#F8FAFC", fg=self.TEXT_MUTED,
                activebackground="#F1F5F9", activeforeground=self.TEXT_MAIN
            )
        self.refresh_visual_calendar()

    def refresh_visual_calendar(self):
        month_name = calendar.month_name[self.cal_month]
        self.month_year_lbl.config(text=f"{month_name} {self.cal_year}")
        cal_data = calendar.monthcalendar(self.cal_year, self.cal_month)

        today = datetime.now()

        event_colors_for_month = {}
        if self.show_events:
            today_date = today.date()
            for event in self.data["events"]:
                try:
                    evt_date = datetime.strptime(event["date"], "%d-%m-%Y").date()
                    if evt_date >= today_date and evt_date.year == self.cal_year and evt_date.month == self.cal_month:
                        if evt_date.day not in event_colors_for_month:
                            event_colors_for_month[evt_date.day] = event.get("color", self.BTN_ACCENT)
                except ValueError:
                    pass

        for row in range(6):
            for col in range(7):
                btn = self.day_buttons[row][col]
                if row < len(cal_data) and cal_data[row][col] != 0:
                    day = cal_data[row][col]
                    btn.config(text=str(day), state="normal", command=lambda d=day: self.select_date(d))

                    is_highlighted = (self.highlighted_date == (self.cal_year, self.cal_month, day))
                    has_future_event = (self.show_events and day in event_colors_for_month)
                    is_today = (
                                self.show_today and self.cal_year == today.year and self.cal_month == today.month and day == today.day)

                    if is_highlighted:
                        if has_future_event:
                            btn.config(bg=event_colors_for_month[day], fg=self.TEXT_LIGHT, font=("Segoe UI", 10))
                        else:
                            btn.config(bg=self.BTN_ACCENT, fg=self.TEXT_LIGHT, font=("Segoe UI", 10))
                    elif has_future_event:
                        btn.config(bg=event_colors_for_month[day], fg=self.TEXT_LIGHT, font=("Segoe UI", 10))
                    elif is_today:
                        btn.config(bg="#E2E8F0", fg=self.TEXT_MAIN, font=("Segoe UI", 10))
                    else:
                        btn.config(bg=self.BG_CARD, fg=self.TEXT_MAIN, font=("Segoe UI", 10))
                else:
                    btn.config(text="", state="disabled", bg=self.BG_CARD)

    def prev_month(self):
        self.clear_calendar_highlight()
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        self.refresh_visual_calendar()

    def next_month(self):
        self.clear_calendar_highlight()
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        self.refresh_visual_calendar()

    def select_date(self, day):
        self.clear_calendar_highlight()
        date_str = f"{day:02d}-{self.cal_month:02d}-{self.cal_year}"
        self.evt_date.delete(0, tk.END)
        self.evt_date.insert(0, date_str)

    def focus_calendar_on_date(self, date_str):
        try:
            dt = datetime.strptime(date_str, "%d-%m-%Y")
            self.cal_year = dt.year
            self.cal_month = dt.month
            self.highlighted_date = (dt.year, dt.month, dt.day)
            self.refresh_visual_calendar()
        except ValueError:
            pass

    def refresh_event_list(self):
        for widget in self.calendar_list_frame.winfo_children(): widget.destroy()

        for idx, event in enumerate(self.data["events"]):
            base_color = event.get("color", self.BTN_ACCENT)
            light_bg = self.lighten_color(base_color)

            # Match exactly the font, size, and shape of the todo list cards
            card = tk.Frame(self.calendar_list_frame, bg=light_bg, padx=15, pady=12, highlightbackground="#E2E8F0",
                            highlightthickness=1, cursor="hand2")
            card.pack(fill=tk.X, pady=(0, 8))

            lbl_title = tk.Label(card, text=event["title"], font=("Segoe UI", 12), bg=light_bg, fg=self.TEXT_MAIN,
                                 cursor="hand2")
            lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.W)

            del_btn = tk.Label(card, text="✕", font=("Segoe UI", 13, "bold"), fg=self.TEXT_MUTED, bg=light_bg,
                               cursor="hand2", width=3, pady=2)
            del_btn.pack(side=tk.RIGHT, padx=(5, 0))
            del_btn.bind("<Button-1>", lambda e, i=idx: self.delete_event(i))
            del_btn.bind("<Enter>", lambda e, btn=del_btn: btn.config(bg=self.DEL_BG_HOVER, fg=self.DEL_FG_HOVER))
            del_btn.bind("<Leave>", lambda e, btn=del_btn, c=light_bg: btn.config(bg=c, fg=self.TEXT_MUTED))

            date_str = event["date"]
            time_str = event.get("time", "")
            display_str = f"{date_str} {time_str}".strip()

            lbl_date_time = tk.Label(card, text=display_str, font=("Segoe UI", 11, "bold"), fg=self.TEXT_MAIN, bg=light_bg, cursor="hand2")
            lbl_date_time.pack(side=tk.RIGHT, padx=(10, 15))

            def click_handler(e, d=event["date"]):
                self.focus_calendar_on_date(d)

            card.bind("<Button-1>", click_handler)
            lbl_title.bind("<Button-1>", click_handler)
            lbl_date_time.bind("<Button-1>", click_handler)

    def sort_events(self):
        def get_datetime(evt):
            try:
                d = datetime.strptime(evt["date"], "%d-%m-%Y")
                t_str = evt.get("time", "00:00")
                t_str = t_str if t_str else "00:00"
                t = datetime.strptime(t_str, "%H:%M").time()
                return datetime.combine(d, t)
            except ValueError:
                return datetime.max

        self.data["events"].sort(key=get_datetime)

    def add_event(self):
        title = self.evt_title.get().strip()
        date_str = self.evt_date.get().strip()
        time_str = self.evt_time.get().strip()

        if not title: return

        try:
            datetime.strptime(date_str, "%d-%m-%Y")
            if time_str: datetime.strptime(time_str, "%H:%M")

            self.data["events"].append({
                "title": title,
                "date": date_str,
                "time": time_str,
                "reminded": False,
                "color": self.current_event_color
            })
            self.sort_events()
            self.save_data()

            self.evt_title.delete(0, tk.END)
            self.evt_time.delete(0, tk.END)
            self.evt_time.insert(0, "12:00")

            self.current_event_color = self.BTN_ACCENT
            self.btn_color_picker.config(bg=self.current_event_color)

            self.focus_calendar_on_date(date_str)
            self.refresh_event_list()
        except ValueError:
            messagebox.showwarning("Format Error", "Date must be DD-MM-YYYY and Time must be HH:MM.")

    def delete_event(self, idx):
        del self.data["events"][idx]
        self.save_data()
        self.clear_calendar_highlight()
        self.refresh_event_list()

    def check_reminders(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        reminders = []

        for event in self.data["events"]:
            try:
                event_date = datetime.strptime(event["date"], "%d-%m-%Y").date()
                if event_date == tomorrow and not event.get("reminded", False):
                    time_display = f" at {event['time']}" if event.get("time") else ""
                    reminders.append(f"• {event['title']}{time_display}")
                    event["reminded"] = True
            except ValueError:
                continue

        if reminders:
            self.save_data()
            alert_text = "Scheduled for tomorrow:\n\n" + "\n".join(reminders)
            messagebox.showinfo("Event Reminder", alert_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductivityApp(root)
    root.mainloop()