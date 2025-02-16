import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import json
import os
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Matplotlib 한글 폰트 설정 (Windows의 경우 "Malgun Gothic")
mpl.rc('font', family='Malgun Gothic')
mpl.rcParams['axes.unicode_minus'] = False

# -------------------------------
# SimpleDateEntry: Spinbox를 이용한 날짜 선택 위젯
# -------------------------------
class SimpleDateEntry(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        # date_pattern 등의 옵션은 무시합니다.
        kwargs.pop('date_pattern', None)
        super().__init__(master, **kwargs)
        current = datetime.date.today()
        self.year_var = tk.IntVar(value=current.year)
        self.month_var = tk.IntVar(value=current.month)
        self.day_var = tk.IntVar(value=current.day)
        self.year_spin = ttk.Spinbox(self, from_=1900, to=2100, textvariable=self.year_var, width=5)
        self.year_spin.pack(side="left")
        ttk.Label(self, text="-").pack(side="left")
        self.month_spin = ttk.Spinbox(self, from_=1, to=12, textvariable=self.month_var, width=3)
        self.month_spin.pack(side="left")
        ttk.Label(self, text="-").pack(side="left")
        self.day_spin = ttk.Spinbox(self, from_=1, to=31, textvariable=self.day_var, width=3)
        self.day_spin.pack(side="left")
    
    def get_date(self):
        try:
            return datetime.date(self.year_var.get(), self.month_var.get(), self.day_var.get())
        except Exception as e:
            messagebox.showerror("오류", f"유효하지 않은 날짜입니다: {e}")
            return datetime.date.today()

# -------------------------------
# 상수 및 파일명
# -------------------------------
MUSCLE_GROUPS = ["Chest", "Back", "Shoulder", "Biceps", "Triceps", "Quad", "Hamstring", "Glutes"]
ROUTINES_FILE = "routines.json"
WORKOUT_LOG_FILE = "workout_log.json"
NUTRITION_REST_FILE = "nutrition_rest_log.json"
SUPPLEMENTS_FILE = "supplements.json"

# -------------------------------
# 데이터 클래스 정의
# -------------------------------
class SetDetail:
    def __init__(self, set_number, weight, reps, rir):
        self.set_number = set_number
        self.weight = weight
        self.reps = reps
        self.rir = rir

    def volume(self):
        return self.weight * self.reps

    def to_dict(self):
        return {
            "set_number": self.set_number,
            "weight": self.weight,
            "reps": self.reps,
            "rir": self.rir
        }

class Exercise:
    def __init__(self, name, muscle_group=""):
        self.name = name
        self.muscle_group = muscle_group  
        self.sets = []

    def add_set(self, set_detail):
        self.sets.append(set_detail)

    def total_volume(self):
        return sum(s.volume() for s in self.sets)

    def to_dict(self):
        return {
            "name": self.name,
            "muscle_group": self.muscle_group,
            "sets": [s.to_dict() for s in self.sets]
        }

    @staticmethod
    def from_dict(data):
        ex = Exercise(data["name"], data.get("muscle_group", ""))
        for set_data in data.get("sets", []):
            s = SetDetail(set_data["set_number"], set_data["weight"], set_data["reps"], set_data["rir"])
            ex.add_set(s)
        return ex

class Routine:
    def __init__(self, name):
        self.name = name
        self.exercises = []

    def add_exercise(self, exercise):
        self.exercises.append(exercise)

    def to_dict(self):
        return {
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises]
        }

    @staticmethod
    def from_dict(data):
        routine = Routine(data["name"])
        for ex_data in data["exercises"]:
            routine.add_exercise(Exercise.from_dict(ex_data))
        return routine

# -------------------------------
# 파일 입출력 함수들
# -------------------------------
def load_routines():
    if not os.path.exists(ROUTINES_FILE):
        return []
    with open(ROUTINES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Routine.from_dict(r) for r in data]

def save_routines(routines):
    with open(ROUTINES_FILE, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in routines], f, indent=4, ensure_ascii=False)

def load_workout_logs():
    if not os.path.exists(WORKOUT_LOG_FILE):
        return []
    with open(WORKOUT_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_workout_log(log):
    logs = load_workout_logs()
    logs.append(log)
    with open(WORKOUT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

def load_nutrition_rest_logs():
    if not os.path.exists(NUTRITION_REST_FILE):
        return []
    with open(NUTRITION_REST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_nutrition_rest_log(record):
    records = load_nutrition_rest_logs()
    records = [rec for rec in records if rec.get("date") != record.get("date")]
    records.append(record)
    with open(NUTRITION_REST_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

def load_supplements():
    if not os.path.exists(SUPPLEMENTS_FILE):
        return []
    with open(SUPPLEMENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_supplements(sup_list):
    with open(SUPPLEMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(sup_list, f, indent=4, ensure_ascii=False)

# -------------------------------
# 타이머 GUI (Tkinter Toplevel)
# -------------------------------
class TimerWindow(tk.Toplevel):
    def __init__(self, parent, seconds):
        super().__init__(parent)
        self.title("타이머")
        self.seconds = seconds
        self.label = ttk.Label(self, text=f"남은 시간: {self.seconds}초", font=("Arial", 16))
        self.label.pack(padx=20, pady=20)
        self.update_timer()

    def update_timer(self):
        if self.seconds > 0:
            self.label.config(text=f"남은 시간: {self.seconds}초")
            self.seconds -= 1
            self.after(1000, self.update_timer)
        else:
            self.label.config(text="타이머 종료!")
            self.after(2000, self.destroy)

# -------------------------------
# Combined Routine & Session 탭
# -------------------------------
class CombinedRoutineSessionFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # 좌측: 루틴 목록 및 생성/삭제 버튼
        self.left_frame = ttk.Frame(self)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ttk.Label(self.left_frame, text="루틴 목록").pack(pady=5)
        self.routine_listbox = tk.Listbox(self.left_frame, height=15)
        self.routine_listbox.pack(fill="both", expand=True)
        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(pady=5)
        self.btn_create = ttk.Button(btn_frame, text="새 루틴 생성", command=self.open_create_routine_window)
        self.btn_create.pack(side="left", padx=5)
        self.btn_delete = ttk.Button(btn_frame, text="루틴 삭제", command=self.delete_routine)
        self.btn_delete.pack(side="left", padx=5)

        # 우측: 운동 날짜 설정 및 세션 시작 (SimpleDateEntry 사용)
        self.right_frame = ttk.Frame(self)
        self.right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        date_frame = ttk.Frame(self.right_frame)
        date_frame.pack(pady=5)
        ttk.Label(date_frame, text="운동 날짜:").pack(side="left", padx=5)
        self.session_date_entry = SimpleDateEntry(date_frame)
        self.session_date_entry.pack(side="left", padx=5)

        ttk.Label(self.right_frame, text="선택된 루틴:").pack(pady=5)
        self.selected_routine_label = ttk.Label(self.right_frame, text="없음", font=("Arial", 14))
        self.selected_routine_label.pack(pady=5)
        self.btn_start_session = ttk.Button(self.right_frame, text="운동 세션 시작", command=self.start_workout_session)
        self.btn_start_session.pack(pady=10)
        self.routine_listbox.bind("<<ListboxSelect>>", self.on_routine_select)

        self.update_routine_list()

    def update_routine_list(self):
        self.routine_listbox.delete(0, tk.END)
        self.routines = load_routines()
        for r in self.routines:
            self.routine_listbox.insert(tk.END, r.name)
        self.selected_routine_label.config(text="없음")

    def on_routine_select(self, event):
        selection = self.routine_listbox.curselection()
        if selection:
            index = selection[0]
            routine = self.routines[index]
            self.selected_routine_label.config(text=routine.name)
        else:
            self.selected_routine_label.config(text="없음")

    def open_create_routine_window(self):
        CreateRoutineWindow(self)

    def delete_routine(self):
        selection = self.routine_listbox.curselection()
        if not selection:
            messagebox.showerror("오류", "삭제할 루틴을 선택하세요.")
            return
        index = selection[0]
        routine = self.routines[index]
        if messagebox.askyesno("확인", f"루틴 '{routine.name}'을(를) 삭제하시겠습니까?"):
            self.routines.pop(index)
            save_routines(self.routines)
            messagebox.showinfo("삭제", "루틴이 삭제되었습니다.")
            self.update_routine_list()

    def start_workout_session(self):
        selection = self.routine_listbox.curselection()
        if not selection:
            messagebox.showerror("오류", "루틴을 선택하세요.")
            return
        index = selection[0]
        routine = self.routines[index]
        session_date = self.session_date_entry.get_date().isoformat()
        WorkoutSessionWindow(self, routine, session_date)

# -------------------------------
# 루틴 생성 창
# -------------------------------
class CreateRoutineWindow(tk.Toplevel):
    def __init__(self, parent_frame):
        super().__init__(parent_frame)
        self.title("새 루틴 생성")
        self.geometry("500x400")
        self.parent_frame = parent_frame

        ttk.Label(self, text="루틴 이름:").pack(pady=5)
        self.routine_name_entry = ttk.Entry(self, width=30)
        self.routine_name_entry.pack(pady=5)

        ttk.Label(self, text="추가된 운동 목록:").pack(pady=5)
        self.exercise_listbox = tk.Listbox(self, height=10)
        self.exercise_listbox.pack(fill="both", expand=True, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        btn_add_ex = ttk.Button(btn_frame, text="운동 추가", command=self.open_create_exercise_window)
        btn_add_ex.pack(side="left", padx=5)
        btn_save = ttk.Button(btn_frame, text="루틴 저장", command=self.save_routine)
        btn_save.pack(side="left", padx=5)

        self.exercises = []

    def open_create_exercise_window(self):
        CreateExerciseWindow(self)

    def add_exercise(self, exercise):
        self.exercises.append(exercise)
        self.exercise_listbox.insert(tk.END, f"{len(self.exercises)}. {exercise.name} ({exercise.muscle_group})")

    def save_routine(self):
        name = self.routine_name_entry.get().strip()
        if not name:
            messagebox.showerror("오류", "루틴 이름을 입력하세요.")
            return
        if not self.exercises:
            messagebox.showerror("오류", "운동을 최소 한 개 이상 추가하세요.")
            return
        routine = Routine(name)
        for ex in self.exercises:
            routine.add_exercise(ex)
        routines = load_routines()
        routines.append(routine)
        save_routines(routines)
        messagebox.showinfo("저장", "루틴이 저장되었습니다.")
        self.destroy()
        self.parent_frame.update_routine_list()

# -------------------------------
# 운동 생성 창
# -------------------------------
class CreateExerciseWindow(tk.Toplevel):
    def __init__(self, routine_window):
        super().__init__(routine_window)
        self.title("새 운동 추가")
        self.geometry("400x200")
        self.routine_window = routine_window

        ttk.Label(self, text="운동 이름:").pack(pady=5)
        self.exercise_name_entry = ttk.Entry(self, width=30)
        self.exercise_name_entry.pack(pady=5)

        ttk.Label(self, text="주동근 선택:").pack(pady=5)
        self.muscle_var = tk.StringVar()
        self.muscle_var.set(MUSCLE_GROUPS[0])
        self.muscle_menu = ttk.OptionMenu(self, self.muscle_var, MUSCLE_GROUPS[0], *MUSCLE_GROUPS)
        self.muscle_menu.pack(pady=5)

        btn_save_ex = ttk.Button(self, text="운동 저장", command=self.save_exercise)
        btn_save_ex.pack(pady=10)

    def save_exercise(self):
        name = self.exercise_name_entry.get().strip()
        if not name:
            messagebox.showerror("오류", "운동 이름을 입력하세요.")
            return
        muscle_group = self.muscle_var.get()
        exercise = Exercise(name, muscle_group)
        self.routine_window.add_exercise(exercise)
        messagebox.showinfo("저장", "운동이 추가되었습니다.")
        self.destroy()

# -------------------------------
# 운동 세션 창
# -------------------------------
class WorkoutSessionWindow(tk.Toplevel):
    def __init__(self, parent_frame, routine, session_date):
        super().__init__(parent_frame)
        self.title("운동 세션")
        self.geometry("600x700")
        self.routine = routine
        self.session_date = session_date  # yyyy-mm-dd
        self.current_exercise_index = 0
        self.session_log = {
            "date": self.session_date,
            "routine_name": routine.name,
            "muscle_volumes": {mg: 0 for mg in MUSCLE_GROUPS},
            "sets_count": {mg: 0 for mg in MUSCLE_GROUPS},
            "exercises": []
        }
        self.current_exercise_sets = []

        self.build_widgets()
        self.display_current_exercise()

    def build_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5)
        ttk.Label(top_frame, text=f"운동 날짜: {self.session_date}").pack()

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(expand=True, fill="both", pady=10)

        # 운동 정보
        self.exercise_info_label = ttk.Label(self.content_frame, text="", font=("Arial", 14))
        self.exercise_info_label.pack(pady=5)

        # 타이머 시간 입력 (각 운동별)
        timer_frame = ttk.Frame(self.content_frame)
        timer_frame.pack(pady=5)
        ttk.Label(timer_frame, text="타이머 시간 (초):").pack(side="left", padx=5)
        self.exercise_timer_entry = ttk.Entry(timer_frame, width=8)
        self.exercise_timer_entry.pack(side="left")
        
        # 세트 입력 영역
        input_frame = ttk.Frame(self.content_frame)
        input_frame.pack(pady=5)
        ttk.Label(input_frame, text="무게(kg):").grid(row=0, column=0, padx=5, pady=2)
        self.weight_entry = ttk.Entry(input_frame, width=8)
        self.weight_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(input_frame, text="Reps:").grid(row=0, column=2, padx=5, pady=2)
        self.reps_entry = ttk.Entry(input_frame, width=8)
        self.reps_entry.grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(input_frame, text="RIR:").grid(row=0, column=4, padx=5, pady=2)
        self.rir_entry = ttk.Entry(input_frame, width=8)
        self.rir_entry.grid(row=0, column=5, padx=5, pady=2)

        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(pady=5)
        btn_add_set = ttk.Button(btn_frame, text="세트 추가", command=self.add_set)
        btn_add_set.pack(side="left", padx=5)
        btn_manual_timer = ttk.Button(btn_frame, text="타이머 실행", command=lambda: self.run_timer(self.get_timer_time()))
        btn_manual_timer.pack(side="left", padx=5)

        # 추가된 세트 내역 리스트박스
        ttk.Label(self.content_frame, text="추가된 세트:").pack(pady=5)
        self.sets_listbox = tk.Listbox(self.content_frame, height=6)
        self.sets_listbox.pack(fill="x", padx=10, pady=5)

        # 다음 운동 버튼
        self.next_btn = ttk.Button(self.content_frame, text="다음 운동", command=self.next_exercise)
        self.next_btn.pack(pady=10)

        # 이전 기록 표시 (텍스트 위젯)
        ttk.Label(self.content_frame, text="이전 기록:").pack(pady=5)
        self.previous_record_text = tk.Text(self.content_frame, height=5, width=50)
        self.previous_record_text.pack(pady=5)
        self.previous_record_text.config(state="disabled")

    def get_timer_time(self):
        try:
            t = int(self.exercise_timer_entry.get())
            return t
        except ValueError:
            return 60

    def get_previous_timer_time(self, exercise_name):
        logs = load_workout_logs()
        try:
            current_date = datetime.datetime.strptime(self.session_date, "%Y-%m-%d").date()
        except Exception:
            current_date = datetime.date.today()
        for log in reversed(logs):
            log_date = datetime.datetime.strptime(log["date"], "%Y-%m-%d").date()
            if log["routine_name"] == self.routine.name and log_date < current_date:
                for ex in log.get("exercises", []):
                    if ex["name"] == exercise_name and "timer_time" in ex:
                        return ex["timer_time"]
        return "60"

    def display_current_exercise(self):
        if self.current_exercise_index < len(self.routine.exercises):
            exercise = self.routine.exercises[self.current_exercise_index]
            info = f"운동: {exercise.name}"
            if exercise.muscle_group:
                info += f" ({exercise.muscle_group})"
            self.exercise_info_label.config(text=info)
            self.sets_listbox.delete(0, tk.END)
            self.current_exercise_sets = []
            self.weight_entry.delete(0, tk.END)
            self.reps_entry.delete(0, tk.END)
            self.rir_entry.delete(0, tk.END)
            # 이전 기록 표시
            prev_record = self.get_previous_exercise_record(exercise.name)
            self.previous_record_text.config(state="normal")
            self.previous_record_text.delete("1.0", tk.END)
            if prev_record:
                self.previous_record_text.insert(tk.END, prev_record)
            else:
                self.previous_record_text.insert(tk.END, "이전 기록 없음")
            self.previous_record_text.config(state="disabled")
            # 타이머 기본값 설정
            prev_timer = self.get_previous_timer_time(exercise.name)
            self.exercise_timer_entry.delete(0, tk.END)
            self.exercise_timer_entry.insert(0, str(prev_timer))
        else:
            self.finish_session()

    def get_previous_exercise_record(self, exercise_name):
        logs = load_workout_logs()
        try:
            current_date = datetime.datetime.strptime(self.session_date, "%Y-%m-%d").date()
        except Exception:
            current_date = datetime.date.today()
        record_text = ""
        for log in reversed(logs):
            log_date = datetime.datetime.strptime(log["date"], "%Y-%m-%d").date()
            if log["routine_name"] == self.routine.name and log_date < current_date:
                for ex in log.get("exercises", []):
                    if ex["name"] == exercise_name:
                        for s in ex.get("sets", []):
                            record_text += f"set{s['set_number']}: {s['weight']}kg x {s['reps']}reps, RIR {s['rir']}\n"
                        break
                if record_text:
                    break
        return record_text

    def add_set(self):
        try:
            weight = float(self.weight_entry.get())
            reps = int(self.reps_entry.get())
            rir = int(self.rir_entry.get())
        except ValueError:
            messagebox.showerror("오류", "올바른 숫자를 입력하세요.")
            return
        set_number = len(self.current_exercise_sets) + 1
        new_set = SetDetail(set_number, weight, reps, rir)
        self.current_exercise_sets.append(new_set)
        self.sets_listbox.insert(tk.END, f"Set {set_number}: {weight}kg x {reps}회, RIR {rir}")
        exercise = self.routine.exercises[self.current_exercise_index]
        muscle = exercise.muscle_group
        self.session_log["muscle_volumes"][muscle] += weight * reps
        self.session_log["sets_count"][muscle] += 1
        self.weight_entry.delete(0, tk.END)
        self.reps_entry.delete(0, tk.END)
        self.rir_entry.delete(0, tk.END)
        self.run_timer(self.get_timer_time())

    def run_timer(self, seconds=None):
        if seconds is None:
            seconds = simpledialog.askinteger("타이머", "타이머 시간을 초 단위로 입력하세요:", minvalue=1)
        if seconds:
            TimerWindow(self, seconds)

    def next_exercise(self):
        if not self.current_exercise_sets:
            if not messagebox.askyesno("확인", "현재 운동에 입력한 세트가 없습니다. 다음 운동으로 넘어가시겠습니까?"):
                return
        if self.current_exercise_sets:
            exercise = self.routine.exercises[self.current_exercise_index]
            ex_record = {
                "name": exercise.name,
                "muscle_group": exercise.muscle_group,
                "sets": [s.to_dict() for s in self.current_exercise_sets],
                "timer_time": self.exercise_timer_entry.get()
            }
            self.session_log["exercises"].append(ex_record)
        self.current_exercise_index += 1
        if self.current_exercise_index < len(self.routine.exercises):
            self.display_current_exercise()
        else:
            self.finish_session()

    def finish_session(self):
        self.session_log["date"] = self.session_date
        save_workout_log(self.session_log)
        messagebox.showinfo("기록 저장", "운동 기록이 저장되었습니다.")
        self.compare_with_previous()
        self.destroy()

    def compare_with_previous(self):
        logs = load_workout_logs()
        routine_name = self.session_log["routine_name"]
        current_date = self.session_log["date"]
        previous_log = None
        for l in logs[::-1]:
            if l["routine_name"] == routine_name and l["date"] < current_date:
                previous_log = l
                break
        info = ""
        if previous_log:
            info += "=== 지난 세션과 비교 ===\n"
            current_volumes = self.session_log["muscle_volumes"]
            prev_volumes = previous_log["muscle_volumes"]
            for mg in MUSCLE_GROUPS:
                current = current_volumes.get(mg, 0)
                if current == 0:
                    continue
                prev = prev_volumes.get(mg, 0)
                diff = current - prev
                info += f"{mg}: 현재 볼륨 = {current}, 이전 볼륨 = {prev}, 차이 = {diff}\n"
        else:
            info += "비교할 이전 세션이 없습니다."
        messagebox.showinfo("비교 결과", info)

# -------------------------------
# 운동 기록 탭
# -------------------------------
class WorkoutRecordsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        graph_frame = ttk.LabelFrame(self, text="부위별 운동 기록 그래프")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        select_frame = ttk.Frame(graph_frame)
        select_frame.pack(pady=5)
        ttk.Label(select_frame, text="부위 선택:").pack(side="left", padx=5)
        self.muscle_var = tk.StringVar()
        self.muscle_var.set(MUSCLE_GROUPS[0])
        self.muscle_combo = ttk.Combobox(select_frame, textvariable=self.muscle_var, state="readonly", values=MUSCLE_GROUPS)
        self.muscle_combo.pack(side="left", padx=5)
        btn_plot = ttk.Button(select_frame, text="그래프 업데이트", command=self.plot_muscle_data)
        btn_plot.pack(side="left", padx=5)

        self.figure = plt.Figure(figsize=(6,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        summary_frame = ttk.LabelFrame(self, text="주간 요약")
        summary_frame.pack(fill="both", expand=True, padx=10, pady=5)
        btn_refresh = ttk.Button(summary_frame, text="주간 요약 새로고침", command=self.show_weekly_summary)
        btn_refresh.pack(pady=5)
        self.summary_text = tk.Text(summary_frame, height=8, width=80)
        self.summary_text.pack(pady=5)
        
        btn_clear = ttk.Button(self, text="모든 운동 기록 초기화", command=self.clear_workout_logs)
        btn_clear.pack(pady=5)

    def plot_muscle_data(self):
        muscle = self.muscle_var.get()
        logs = load_workout_logs()
        data = []
        for log in logs:
            date = log["date"]
            vol = log["muscle_volumes"].get(muscle, 0)
            if vol == 0:
                continue
            sets = log["sets_count"].get(muscle, 0)
            data.append((date, sets, vol))
        data.sort(key=lambda x: x[0])
        data = data[-10:]
        if not data:
            messagebox.showinfo("정보", f"{muscle}에 대한 기록이 없습니다.")
            return
        dates = [d[0] for d in data]
        sets_list = [d[1] for d in data]
        vol_list = [d[2] for d in data]
        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        ax1.plot(dates, sets_list, marker='o', label="Sets", color="blue")
        ax1.set_title(f"{muscle} - Sets (최근 10회)")
        ax1.set_ylabel("세트 수")
        ax1.tick_params(axis='x', rotation=45)
        ax2.plot(dates, vol_list, marker='s', label="Volume", color="red")
        ax2.set_title(f"{muscle} - Volume (최근 10회)")
        ax2.set_xlabel("날짜")
        ax2.set_ylabel("볼륨")
        ax2.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

    def show_weekly_summary(self):
        logs = load_workout_logs()
        weekly_summary = {}
        for log in logs:
            log_date = datetime.datetime.strptime(log["date"], "%Y-%m-%d").date()
            monday = log_date - datetime.timedelta(days=log_date.weekday())
            sunday = monday + datetime.timedelta(days=6)
            key = f"{monday} ~ {sunday}"
            if key not in weekly_summary:
                weekly_summary[key] = {mg: {"sets": 0, "volume": 0} for mg in MUSCLE_GROUPS}
            for mg in MUSCLE_GROUPS:
                weekly_summary[key][mg]["sets"] += log["sets_count"].get(mg, 0)
                weekly_summary[key][mg]["volume"] += log["muscle_volumes"].get(mg, 0)
        self.summary_text.delete("1.0", tk.END)
        for week_key in sorted(weekly_summary.keys()):
            self.summary_text.insert(tk.END, f"--- {week_key} ---\n")
            for mg in MUSCLE_GROUPS:
                s = weekly_summary[week_key][mg]["sets"]
                v = weekly_summary[week_key][mg]["volume"]
                self.summary_text.insert(tk.END, f"{mg}: 세트 수 = {s}, 볼륨 = {v}\n")
            self.summary_text.insert(tk.END, "\n")

    def clear_workout_logs(self):
        if messagebox.askyesno("확인", "정말 모든 운동 기록을 초기화 하시겠습니까?"):
            with open(WORKOUT_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4, ensure_ascii=False)
            messagebox.showinfo("완료", "모든 운동 기록이 초기화되었습니다.")
            self.plot_muscle_data()
            self.show_weekly_summary()

# -------------------------------
# 영양/휴식 기록 탭
# -------------------------------
class NutritionRestRecordFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5, padx=10, anchor="w")
        ttk.Label(top_frame, text="날짜:").grid(row=0, column=0, padx=5, pady=2)
        self.date_entry = SimpleDateEntry(top_frame, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=0, column=1, padx=5, pady=2)

        nutrition_frame = ttk.LabelFrame(self, text="영양 정보")
        nutrition_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(nutrition_frame, text="총 칼로리:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.calorie_entry = ttk.Entry(nutrition_frame, width=10)
        self.calorie_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(nutrition_frame, text="탄수화물(g):").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        self.carb_entry = ttk.Entry(nutrition_frame, width=10)
        self.carb_entry.grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(nutrition_frame, text="단백질(g):").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.protein_entry = ttk.Entry(nutrition_frame, width=10)
        self.protein_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(nutrition_frame, text="지방(g):").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        self.fat_entry = ttk.Entry(nutrition_frame, width=10)
        self.fat_entry.grid(row=1, column=3, padx=5, pady=2)

        weight_frame = ttk.Frame(self)
        weight_frame.pack(pady=5, padx=10, anchor="w")
        ttk.Label(weight_frame, text="공복 몸무게 (kg):").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.fasting_weight_entry = ttk.Entry(weight_frame, width=10)
        self.fasting_weight_entry.grid(row=0, column=1, padx=5, pady=2)

        sleep_frame = ttk.Frame(self)
        sleep_frame.pack(pady=5, padx=10, anchor="w")
        ttk.Label(sleep_frame, text="총 수면 시간 (시간):").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.sleep_entry = ttk.Entry(sleep_frame, width=10)
        self.sleep_entry.grid(row=0, column=1, padx=5, pady=2)

        supp_frame = ttk.LabelFrame(self, text="영양제 체크리스트")
        supp_frame.pack(fill="x", padx=10, pady=5)
        self.supplement_vars = {}
        self.supplement_ui_frame = ttk.Frame(supp_frame)
        self.supplement_ui_frame.pack(pady=5, padx=5, anchor="w")
        add_sup_frame = ttk.Frame(supp_frame)
        add_sup_frame.pack(pady=5, padx=5, anchor="w")
        ttk.Label(add_sup_frame, text="영양제 추가:").pack(side="left", padx=5)
        self.new_supp_entry = ttk.Entry(add_sup_frame, width=15)
        self.new_supp_entry.pack(side="left", padx=5)
        btn_add_sup = ttk.Button(add_sup_frame, text="추가", command=self.add_supplement)
        btn_add_sup.pack(side="left", padx=5)
        btn_del_sup = ttk.Button(add_sup_frame, text="선택 삭제", command=self.delete_selected_supplement)
        btn_del_sup.pack(side="left", padx=5)
        self.supplement_list = load_supplements()
        self.refresh_supplement_ui()

        caffeine_frame = ttk.LabelFrame(self, text="카페인 기록")
        caffeine_frame.pack(fill="x", padx=10, pady=5)
        self.caffeine_var = tk.BooleanVar()
        self.caffeine_check = ttk.Checkbutton(caffeine_frame, text="카페인 섭취", variable=self.caffeine_var, command=self.toggle_caffeine)
        self.caffeine_check.grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(caffeine_frame, text="운동 전 몇 시간?:").grid(row=0, column=1, padx=5, pady=2, sticky="e")
        self.caffeine_time_entry = ttk.Entry(caffeine_frame, width=10)
        self.caffeine_time_entry.grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(caffeine_frame, text="섭취한 mg:").grid(row=0, column=3, padx=5, pady=2, sticky="e")
        self.caffeine_mg_entry = ttk.Entry(caffeine_frame, width=10)
        self.caffeine_mg_entry.grid(row=0, column=4, padx=5, pady=2)
        self.caffeine_time_entry.config(state="disabled")
        self.caffeine_mg_entry.config(state="disabled")

        btn_save = ttk.Button(self, text="기록 저장", command=self.save_record)
        btn_save.pack(pady=10)

        output_frame = ttk.LabelFrame(self, text="기록 불러오기")
        output_frame.pack(fill="both", padx=10, pady=5, expand=True)
        self.record_text = tk.Text(output_frame, height=10)
        self.record_text.pack(fill="both", padx=5, pady=5)
        btn_load = ttk.Button(output_frame, text="기록 불러오기", command=self.load_records)
        btn_load.pack(pady=5)

    def refresh_supplement_ui(self):
        for widget in self.supplement_ui_frame.winfo_children():
            widget.destroy()
        self.supplement_vars = {}
        for sup in self.supplement_list:
            frame = ttk.Frame(self.supplement_ui_frame)
            frame.pack(anchor="w", pady=2)
            var = tk.BooleanVar()
            self.supplement_vars[sup] = var
            chk = ttk.Checkbutton(frame, text=sup, variable=var)
            chk.pack(side="left")
            btn_del = ttk.Button(frame, text="삭제", command=lambda s=sup: self.delete_supplement(s))
            btn_del.pack(side="left", padx=5)

    def add_supplement(self):
        sup_name = self.new_supp_entry.get().strip()
        if sup_name:
            if sup_name in self.supplement_list:
                messagebox.showinfo("정보", "이미 추가된 영양제입니다.")
            else:
                self.supplement_list.append(sup_name)
                save_supplements(self.supplement_list)
                self.refresh_supplement_ui()
                self.new_supp_entry.delete(0, tk.END)
        else:
            messagebox.showerror("오류", "영양제 이름을 입력하세요.")

    def delete_supplement(self, sup_name):
        if messagebox.askyesno("삭제 확인", f"'{sup_name}' 영양제를 삭제하시겠습니까?"):
            if sup_name in self.supplement_list:
                self.supplement_list.remove(sup_name)
                save_supplements(self.supplement_list)
                self.refresh_supplement_ui()

    def delete_selected_supplement(self):
        sup_name = self.new_supp_entry.get().strip()
        if sup_name in self.supplement_list:
            self.delete_supplement(sup_name)
            self.new_supp_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("정보", "삭제할 영양제가 목록에 없습니다.")

    def toggle_caffeine(self):
        if self.caffeine_var.get():
            self.caffeine_time_entry.config(state="normal")
            self.caffeine_mg_entry.config(state="normal")
        else:
            self.caffeine_time_entry.config(state="disabled")
            self.caffeine_mg_entry.config(state="disabled")

    def save_record(self):
        record = {
            "date": self.date_entry.get(),
            "calories": self.calorie_entry.get(),
            "carbs": self.carb_entry.get(),
            "protein": self.protein_entry.get(),
            "fat": self.fat_entry.get(),
            "fasting_weight": self.fasting_weight_entry.get(),
            "sleep": self.sleep_entry.get(),
            "supplements": {name: var.get() for name, var in self.supplement_vars.items()},
            "caffeine": {}
        }
        if self.caffeine_var.get():
            record["caffeine"] = {
                "time_before_exercise": self.caffeine_time_entry.get(),
                "mg": self.caffeine_mg_entry.get()
            }
        save_nutrition_rest_log(record)
        messagebox.showinfo("저장", "영양/휴식 기록이 저장되었습니다.")

    def load_records(self):
        records = load_nutrition_rest_logs()
        self.record_text.delete("1.0", tk.END)
        for rec in records:
            self.record_text.insert(tk.END, f"날짜: {rec.get('date','')}\n")
            self.record_text.insert(tk.END, f"칼로리: {rec.get('calories','')}, 탄수화물: {rec.get('carbs','')}g, 단백질: {rec.get('protein','')}g, 지방: {rec.get('fat','')}g\n")
            self.record_text.insert(tk.END, f"공복 몸무게: {rec.get('fasting_weight','')}kg, 수면: {rec.get('sleep','')}시간\n")
            supp = rec.get("supplements", {})
            self.record_text.insert(tk.END, "영양제: " + ", ".join([f"{name}({'먹음' if val else '안먹음'})" for name, val in supp.items()]) + "\n")
            caffeine = rec.get("caffeine", {})
            if caffeine:
                self.record_text.insert(tk.END, f"카페인: 운동 {caffeine.get('time_before_exercise','')}시간 전, {caffeine.get('mg','')}mg\n")
            self.record_text.insert(tk.END, "-------------------------\n")

# -------------------------------
# 메인 애플리케이션 클래스
# -------------------------------
class BodybuildingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("보디빌딩 운동 기록 앱")
        self.geometry("1100x800")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.combined_frame = CombinedRoutineSessionFrame(self.notebook)
        self.records_frame = WorkoutRecordsFrame(self.notebook)
        self.nutrition_rest_frame = NutritionRestRecordFrame(self.notebook)

        self.notebook.add(self.combined_frame, text="루틴/세션")
        self.notebook.add(self.records_frame, text="운동 기록")
        self.notebook.add(self.nutrition_rest_frame, text="영양/휴식 기록")

# -------------------------------
# 메인 실행
# -------------------------------
if __name__ == "__main__":
    app = BodybuildingApp()
    app.mainloop()
