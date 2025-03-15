import json
from tkinter import Tk, Frame, Label, Button, Entry, Checkbutton, IntVar, Scrollbar, OptionMenu, StringVar, Toplevel, messagebox, Menu, filedialog
from tkinter import ttk
from calendar import month_name, day_name, monthrange
from datetime import datetime, timedelta
from calendar import Calendar

ADD_EVENT_TEXT = "Add To-Do Event"

class CalendarApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Simple Calendar App")
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self.events = self.load_events()  # To-Do 이벤트 저장
        self.selected_day = None  # 선택된 날짜를 저장할 속성 추가
        self.popup = None  # 팝업 창 참조를 저장할 속성 추가
        self.current_date = None  # 현재 날짜를 저장할 속성 추가
        self.clipboard = None  # 클립보드 기능을 위한 속성 추가
        self.undo_stack = []  # Undo 스택 추가
        self.redo_stack = []  # Redo 스택 추가

        self.create_widgets()
        self.display_calendar()

    def create_widgets(self):
        self.menu_bar = Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # File 메뉴
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Export Events", command=self.export_events)  # Export Events 추가
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit 메뉴
        self.edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Delete All Events", command=self.delete_all_events)

        # 단축키 바인딩
        self.master.bind_all("<Control-z>", lambda event: self.undo())
        self.master.bind_all("<Control-y>", lambda event: self.redo())
        self.master.bind_all("<Control-x>", lambda event: self.cut())
        self.master.bind_all("<Control-c>", lambda event: self.copy())
        self.master.bind_all("<Control-v>", lambda event: self.paste())

        # View 메뉴
        self.view_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Show Calendar", command=self.display_calendar)
        self.view_menu.add_command(label="Show All Events", command=self.show_all_events)

        # Help 메뉴
        self.help_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Manual", command=self.show_manual)

        self.frame = Frame(self.master)
        self.frame.pack(pady=10)

        self.nav_frame = Frame(self.frame)
        self.nav_frame.grid(row=0, column=1, pady=5)

        self.prev_button = Button(self.nav_frame, text="◀", command=self.prev_month, font=("Helvetica", 12, "bold"))
        self.prev_button.pack(side="left", padx=5)

        self.label = Label(self.nav_frame, text="", font=("Helvetica", 16, "bold"))
        self.label.pack(side="left", padx=10)

        self.next_button = Button(self.nav_frame, text="▷", command=self.next_month, font=("Helvetica", 12, "bold"))
        self.next_button.pack(side="left", padx=5)

        # 중앙에 달력을 배치하기 위한 프레임
        self.calendar_container = Frame(self.frame)
        self.calendar_container.grid(row=1, column=0, pady=10, padx=20, sticky="n")

        self.calendar_frame = Frame(self.calendar_container)
        self.calendar_frame.pack(pady=10, padx=20)

        self.event_frame = Frame(self.frame)
        self.event_frame.grid(row=2, column=0, pady=10, sticky="w")

        self.add_event_button = Button(self.event_frame, text=ADD_EVENT_TEXT, command=self.open_add_event_window)
        self.add_event_button.pack(side="left", padx=5)

        self.show_all_events_button = Button(self.event_frame, text="Show All Events", command=self.show_all_events)
        self.show_all_events_button.pack(side="left", padx=5)

        self.completion_label = Label(self.event_frame, text="", font=("Helvetica", 12))
        self.completion_label.pack(side="left", padx=10)

        self.event_list_frame = Frame(self.frame, width=600)  # 가로 크기 조정
        self.event_list_frame.grid(row=1, column=1, rowspan=3, pady=10, padx=20, sticky="nsew")

        self.tree = ttk.Treeview(self.event_list_frame, columns=("Date", "Name", "Priority", "Repeat", "Completed"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Repeat", text="Repeat")
        self.tree.heading("Completed", text="Completed")
        self.tree.column("Date", width=100)  # 열 너비 조정
        self.tree.column("Name", width=150)  # 열 너비 조정
        self.tree.column("Priority", width=100)  # 열 너비 조정
        self.tree.column("Repeat", width=100)  # 열 너비 조정
        self.tree.column("Completed", width=100)  # 열 너비 조정
        self.tree.pack(side="left", fill="both", expand=True)

        self.scrollbar = Scrollbar(self.event_list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_treeview_double_click)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)  # 창 닫기 이벤트 처리

    def display_calendar(self):
        self.label.config(text=f"{month_name[self.current_month]} {self.current_year}")
        self.clear_calendar()

        # 요일 표시
        for i, day in enumerate(day_name):
            day_label = Label(self.calendar_frame, text=day[:3], font=("Helvetica", 10, "bold"))
            day_label.grid(row=0, column=i, padx=5, pady=5)

        cal = Calendar()
        row = 1
        col = 0
        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day != 0:
                btn = Button(self.calendar_frame, text=str(day), font=("Helvetica", 10), width=4, height=2,
                             command=lambda d=day: self.show_event(d))
                if day == datetime.now().day and self.current_month == datetime.now().month and self.current_year == datetime.now().year:
                    btn.config(bg="lightblue")  # 현재 날짜 강조
                btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def clear_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.display_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.display_calendar()

    def show_event(self, day):
        self.selected_day = day  # 선택된 날짜 설정
        date = f"{day}/{self.current_month}/{self.current_year}"
        self.current_date = date
        self.update_event_list()

    def open_add_event_window(self):
        if self.selected_day is None:
            return

        self.add_event_window = Toplevel(self.master)
        self.add_event_window.title(ADD_EVENT_TEXT)

        Label(self.add_event_window, text="Event Name:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10)
        self.event_name_entry = Entry(self.add_event_window, font=("Helvetica", 12))
        self.event_name_entry.grid(row=0, column=1, padx=10, pady=10)

        self.priority_var = IntVar()
        Checkbutton(self.add_event_window, text="High Priority", variable=self.priority_var).grid(row=1, column=0, columnspan=2, pady=10)

        Label(self.add_event_window, text="Repeat:", font=("Helvetica", 12)).grid(row=2, column=0, padx=10, pady=10)
        self.repeat_var = StringVar(self.add_event_window)
        self.repeat_var.set("None")
        self.repeat_menu = OptionMenu(self.add_event_window, self.repeat_var, "None", "Daily", "Weekly", "Monthly")
        self.repeat_menu.grid(row=2, column=1, padx=10, pady=10)

        Button(self.add_event_window, text=ADD_EVENT_TEXT, command=self.add_event).grid(row=3, column=0, columnspan=2, pady=10)

    def add_event(self):
        event_name = self.event_name_entry.get()
        priority = self.priority_var.get()
        repeat = self.repeat_var.get()

        if event_name:
            date = f"{self.selected_day}/{self.current_month}/{self.current_year}"
            self.add_event_to_date(event_name, priority, repeat, date)

            if repeat == "Daily":
                self.add_daily_events(event_name, priority)
            elif repeat == "Weekly":
                self.add_weekly_events(event_name, priority)
            elif repeat == "Monthly":
                self.add_monthly_events(event_name, priority)

            self.add_event_window.destroy()
            self.update_event_list()
        else:
            messagebox.showwarning("Warning", "Event name cannot be empty.")

    def add_event_to_date(self, event_name, priority, repeat, date):
        if date not in self.events:
            self.events[date] = []
        self.events[date].append({
            "name": event_name,
            "priority": priority,
            "repeat": repeat,
            "completed": False
        })

    def add_daily_events(self, event_name, priority):
        end_day = monthrange(self.current_year, self.current_month)[1]
        for day in range(self.selected_day + 1, end_day + 1):
            date = f"{day}/{self.current_month}/{self.current_year}"
            self.add_event_to_date(event_name, priority, "Daily", date)

    def add_weekly_events(self, event_name, priority):
        start_date = datetime(self.current_year, self.current_month, self.selected_day)
        while start_date.month == self.current_month:
            start_date += timedelta(weeks=1)
            if start_date.month == self.current_month:
                date = f"{start_date.day}/{start_date.month}/{start_date.year}"
                self.add_event_to_date(event_name, priority, "Weekly", date)

    def add_monthly_events(self, event_name, priority):
        for month in range(self.current_month + 1, 13):
            date = f"{self.selected_day}/{month}/{self.current_year}"
            self.add_event_to_date(event_name, priority, "Monthly", date)

    def delete_event(self, date, event):
        if date in self.events:
            self.events[date].remove(event)
            if not self.events[date]:
                del self.events[date]
            self.update_event_list()

    def delete_all_events(self):
        self.events.clear()
        self.update_event_list()

    def toggle_event_completion(self, event, var):
        event["completed"] = bool(var.get())
        self.update_event_list()

    def update_event_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_events = 0
        completed_events = 0

        if self.current_date and self.current_date in self.events:
            for event in self.events[self.current_date]:
                total_events += 1
                priority = event.get("priority", "Normal")  # 기본값 설정
                repeat = event.get("repeat", "None")  # 기본값 설정
                completed = "Yes" if event["completed"] else "No"

                self.tree.insert("", "end", values=(self.current_date, event["name"], priority, repeat, completed))

                if event["completed"]:
                    completed_events += 1

        if total_events > 0:
            completion_percentage = (completed_events / total_events) * 100
        else:
            completion_percentage = 0

        self.completion_label.config(text=f"Completion: {completed_events}/{total_events} ({completion_percentage:.1f}%)")

    def show_all_events(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for date, events in self.events.items():
            for event in events:
                completed = "Yes" if event["completed"] else "No"
                priority = event.get("priority", "Normal")  # 기본값 설정
                repeat = event.get("repeat", "None")  # 기본값 설정
                self.tree.insert("", "end", values=(date, event["name"], priority, repeat, completed))

    def on_treeview_double_click(self, tree_event):
        if self.popup is not None and self.popup.winfo_exists():
            return  # 팝업 창이 이미 열려 있는 경우 아무 작업도 하지 않음

        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        date, event_name, priority, repeat, completed = values

        # 이벤트 객체를 찾기 위해 self.events에서 검색
        event_obj = None
        for event in self.events[date]:
            if event["name"] == event_name and str(event.get("priority", "Normal")) == priority and str(event.get("repeat", "None")) == repeat:
                event_obj = event
                break

        if event_obj is None:
            return

        def update_event():
            event_obj["completed"] = bool(var.get())
            self.update_event_list()
            self.popup.destroy()
            self.popup = None  # 팝업 창 참조 제거

        def delete_event():
            self.delete_event(date, event_obj)
            self.popup.destroy()
            self.popup = None  # 팝업 창 참조 제거

        self.popup = Toplevel(self.master)
        self.popup.title("Update Event")

        Label(self.popup, text="Event Name:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10)
        event_name_entry = Entry(self.popup, font=("Helvetica", 12))
        event_name_entry.grid(row=0, column=1, padx=10, pady=10)
        event_name_entry.insert(0, event_name)
        event_name_entry.config(state="readonly")

        var = IntVar(value=1 if completed == "Yes" else 0)
        Checkbutton(self.popup, text="Completed", variable=var).grid(row=1, column=0, columnspan=2, pady=10)

        Button(self.popup, text="Delete", command=delete_event).grid(row=2, column=0, pady=10)
        Button(self.popup, text="Update", command=update_event).grid(row=2, column=1, pady=10)

        # 팝업 창이 닫힐 때 호출되는 이벤트 핸들러 추가
        self.popup.protocol("WM_DELETE_WINDOW", self.on_popup_close)

    def on_popup_close(self):
        self.popup.destroy()
        self.popup = None  # 팝업 창 참조 제거

    def load_events(self):
        try:
            with open("events.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_events(self):
        with open("events.json", "w") as file:
            json.dump(self.events, file)

    def on_closing(self):
        self.save_events()
        self.master.destroy()

    def new_file(self):
        response = messagebox.askyesnocancel("Save Changes", "Do you want to save changes before creating a new file?")
        if response:  # Yes
            self.save_file()
            self.events.clear()
            self.current_month = datetime.now().month
            self.current_year = datetime.now().year
            self.display_calendar()
            self.update_event_list()
        elif response is False:  # No
            self.events.clear()
            self.current_month = datetime.now().month
            self.current_year = datetime.now().year
            self.display_calendar()
            self.update_event_list()
        # Cancel의 경우 아무 작업도 하지 않음

    def open_file(self):
        response = messagebox.askyesnocancel("Save Changes", "Do you want to save changes before opening a new file?")
        if response:  # Yes
            self.save_file()
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if file_path:
                with open(file_path, "r") as file:
                    self.events = json.load(file)
                self.update_event_list()
        elif response is False:  # No
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if file_path:
                with open(file_path, "r") as file:
                    self.events = json.load(file)
                self.update_event_list()
        # Cancel의 경우 아무 작업도 하지 않음

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                json.dump(self.events, file)

    def export_events(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                for date, events in self.events.items():
                    for event in events:
                        file.write(f"Date: {date} Name: {event['name']} Priority: {event.get('priority', 'Normal')} Repeat: {event.get('repeat', 'None')} Completed: {'Yes' if event['completed'] else 'No'}\n")

    def undo(self):
        if self.undo_stack:
            last_action = self.undo_stack.pop()
            if last_action["action"] == "delete":
                self.events[last_action["date"]].append(last_action["event"])
            elif last_action["action"] == "add":
                self.events[last_action["date"]].remove(last_action["event"])
            self.redo_stack.append(last_action)
            self.update_event_list()

    def redo(self):
        if self.redo_stack:
            last_action = self.redo_stack.pop()
            if last_action["action"] == "delete":
                self.events[last_action["date"]].remove(last_action["event"])
            elif last_action["action"] == "add":
                self.events[last_action["date"]].append(last_action["event"])
            self.undo_stack.append(last_action)
            self.update_event_list()

    def cut(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.clipboard = item["values"][1]  # 이벤트 이름을 클립보드에 저장
            date = item["values"][0]
            event = next(event for event in self.events[date] if event["name"] == self.clipboard)
            self.undo_stack.append({"action": "delete", "date": date, "event": event})
            self.events[date].remove(event)
            self.update_event_list()

    def copy(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.clipboard = item["values"][1]  # 이벤트 이름을 클립보드에 저장

    def paste(self):
        if self.clipboard:
            date = self.current_date
            if date:
                event = {"name": self.clipboard, "priority": "Normal", "repeat": "None", "completed": False}
                self.undo_stack.append({"action": "add", "date": date, "event": event})
                self.add_event_to_date(self.clipboard, "Normal", "None", date)
                self.update_event_list()

    def show_about(self):
        messagebox.showinfo("About", "Simple Calendar App\nVersion 1.0")

    def show_manual(self):
        def display_manual(language):
            if language == "English":
                manual_text = (
                    "Simple Calendar App Manual\n\n"
                    "Basic Operation and Usage:\n"
                    "This application allows users to add, edit, and delete To-Do events in a calendar. "
                    "Select a date on the calendar to add an event, or manage events from the event list.\n\n"
                    
                    "File Menu:\n"
                    " - New: Create a new file. Prompts to save changes if there are any.\n"
                    " - Open: Open an existing file. Prompts to save changes if there are any.\n"
                    " - Save: Save the current event data to a file.\n"
                    " - Export Events: Export the current event list to a text file.\n"
                    " - Exit: Exit the application.\n\n"
                    
                    "Edit Menu:\n"
                    " - Undo (Ctrl+Z): Undo the last action.\n"
                    " - Redo (Ctrl+Y): Redo the last undone action.\n"
                    " - Cut (Ctrl+X): Cut the selected event and save it to the clipboard.\n"
                    " - Copy (Ctrl+C): Copy the selected event to the clipboard.\n"
                    " - Paste (Ctrl+V): Paste the event from the clipboard to the currently selected date.\n"
                    " - Delete All Events: Delete all events.\n\n"
                    
                    "View Menu:\n"
                    " - Show Calendar: Display the calendar.\n"
                    " - Show All Events: Display all events.\n\n"
                    
                    "Help Menu:\n"
                    " - About: Display information about the program.\n"
                    " - Manual: Display this manual.\n\n"
                    
                    "Screen Layout:\n"
                    " - Top Menu Bar: Includes File, Edit, View, and Help menus.\n"
                    " - Calendar: Displays the dates of the current month. Click on a date to add an event.\n"
                    " - Add To-Do Event Button: Opens a window to add a new event to the selected date.\n"
                    " - Show All Events Button: Displays all events.\n"
                    " - Event List: Displays events by date. Double-click an event to edit it.\n\n"
                    
                    "Calendar Features:\n"
                    " - Previous/Next Buttons: Navigate to the previous or next month.\n"
                    " - Highlight Current Date: The current date is highlighted with a blue background.\n"
                    " - Date Click: Click on a date to add an event.\n\n"
                    
                    "Add To-Do Event Button Features:\n"
                    " - Opens a window to add a new event to the selected date.\n"
                    " - Allows input of event name, priority, and repeat settings.\n\n"
                    
                    "Show All Events Button Features:\n"
                    " - Displays all events in the event list.\n\n"
                    
                    "Event List Features:\n"
                    " - Displays events by date.\n"
                    " - Double-click an event to edit it.\n"
                    " - Select an event to cut, copy, or delete it.\n"
                )
            else:
                manual_text = (
                    "파이썬 캘린더 앱 매뉴얼\n\n"
                    "기본 동작 및 사용 방법:\n"
                    "이 애플리케이션은 사용자가 캘린더에 To-Do 이벤트를 추가, 수정 및 삭제할 수 있도록 합니다. "
                    "캘린더에서 날짜를 선택하여 이벤트를 추가하거나 이벤트 목록에서 이벤트를 관리할 수 있습니다.\n\n"
                    
                    "파일 메뉴:\n"
                    " - 새로 만들기: 새 파일을 만듭니다. 변경 사항이 있는 경우 저장할지 묻습니다.\n"
                    " - 열기: 기존 파일을 엽니다. 변경 사항이 있는 경우 저장할지 묻습니다.\n"
                    " - 저장: 현재 이벤트 데이터를 파일에 저장합니다.\n"
                    " - 이벤트 내보내기: 현재 이벤트 목록을 텍스트 파일로 내보냅니다.\n"
                    " - 종료: 애플리케이션을 종료합니다.\n\n"
                    
                    "편집 메뉴:\n"
                    " - 실행 취소 (Ctrl+Z): 마지막 작업을 실행 취소합니다.\n"
                    " - 다시 실행 (Ctrl+Y): 마지막 실행 취소 작업을 다시 실행합니다.\n"
                    " - 잘라내기 (Ctrl+X): 선택한 이벤트를 잘라내어 클립보드에 저장합니다.\n"
                    " - 복사 (Ctrl+C): 선택한 이벤트를 클립보드에 복사합니다.\n"
                    " - 붙여넣기 (Ctrl+V): 클립보드에서 현재 선택된 날짜로 이벤트를 붙여넣습니다.\n"
                    " - 모든 이벤트 삭제: 모든 이벤트를 삭제합니다.\n\n"
                    
                    "보기 메뉴:\n"
                    " - 캘린더 보기: 캘린더를 표시합니다.\n"
                    " - 모든 이벤트 보기: 모든 이벤트를 표시합니다.\n\n"
                    
                    "도움말 메뉴:\n"
                    " - 정보: 프로그램에 대한 정보를 표시합니다.\n"
                    " - 매뉴얼: 이 매뉴얼을 표시합니다.\n\n"
                    
                    "화면 구성:\n"
                    " - 상단 메뉴 바: 파일, 편집, 보기 및 도움말 메뉴를 포함합니다.\n"
                    " - 캘린더: 현재 월의 날짜를 표시합니다. 날짜를 클릭하여 이벤트를 추가할 수 있습니다.\n"
                    " - To-Do 이벤트 추가 버튼: 선택한 날짜에 새 이벤트를 추가할 수 있는 창을 엽니다.\n"
                    " - 모든 이벤트 보기 버튼: 모든 이벤트를 표시합니다.\n"
                    " - 이벤트 목록: 날짜별로 이벤트를 표시합니다. 이벤트를 더블 클릭하여 수정할 수 있습니다.\n\n"
                    
                    "캘린더 기능:\n"
                    " - 이전/다음 버튼: 이전 또는 다음 달로 이동합니다.\n"
                    " - 현재 날짜 강조: 현재 날짜는 파란색 배경으로 강조됩니다.\n"
                    " - 날짜 클릭: 날짜를 클릭하여 이벤트를 추가할 수 있습니다.\n\n"
                    
                    "To-Do 이벤트 추가 버튼 기능:\n"
                    " - 선택한 날짜에 새 이벤트를 추가할 수 있는 창을 엽니다.\n"
                    " - 이벤트 이름, 우선순위 및 반복 설정을 입력할 수 있습니다.\n\n"
                    
                    "모든 이벤트 보기 버튼 기능:\n"
                    " - 이벤트 목록에 모든 이벤트를 표시합니다.\n\n"
                    
                    "이벤트 목록 기능:\n"
                    " - 날짜별로 이벤트를 표시합니다.\n"
                    " - 이벤트를 더블 클릭하여 수정할 수 있습니다.\n"
                    " - 이벤트를 선택하여 잘라내기, 복사 또는 삭제할 수 있습니다.\n"
                )
            messagebox.showinfo("Manual", manual_text)

        manual_window = Toplevel(self.master)
        manual_window.title("Select Language")

        Label(manual_window, text="Select the language for the manual:", font=("Helvetica", 12)).pack(pady=10)

        Button(manual_window, text="English", command=lambda: display_manual("English")).pack(pady=5)
        Button(manual_window, text="한국어", command=lambda: display_manual("Korean")).pack(pady=5)

if __name__ == "__main__":
    root = Tk()
    app = CalendarApp(root)
    root.mainloop()
