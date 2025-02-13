import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import json
import os
import datetime

# -------------------------------
# 상수 및 파일명
# -------------------------------
MUSCLE_GROUPS = ["Chest", "Back", "Shoulder", "Biceps", "Triceps", "Quad", "Hamstring", "Glutes"]
ROUTINES_FILE = "routines.json"
WORKOUT_LOG_FILE = "workout_log.json"

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
        # muscle_group는 주동근(운동 부위)로, 루틴 생성 시 입력받거나 이후 운동 세션 시 다시 확인할 수 있음
        self.muscle_group = muscle_group  
        self.sets = []  # 운동 세션에서 입력할 세트 데이터가 저장됨

    def add_set(self, set_detail):
        self.sets.append(set_detail)

    def total_volume(self):
        return sum(s.volume() for s in self.sets)

    def to_dict(self):
        return {
            "name": self.name,
            "muscle_group": self.muscle_group,
            # 루틴 생성 시에는 세트 기록이 없으므로 비워둡니다.
            "sets": [s.to_dict() for s in self.sets]  
        }

    @staticmethod
    def from_dict(data):
        ex = Exercise(data["name"], data.get("muscle_group", ""))
        # 저장된 루틴은 세트 정보가 없을 수 있음.
        for set_data in data.get("sets", []):
            s = SetDetail(set_data["set_number"], set_data["weight"], set_data["reps"], set_data["rir"])
            ex.add_set(s)
        return ex

class Routine:
    def __init__(self, name):
        self.name = name
        self.exercises = []  # 각 운동은 이름과 (선택적) 주동근만 포함

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
        routines = [Routine.from_dict(r) for r in data]
        return routines

def save_routines(routines):
    with open(ROUTINES_FILE, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in routines], f, indent=4, ensure_ascii=False)

def load_workout_logs():
    if not os.path.exists(WORKOUT_LOG_FILE):
        return []
    with open(WORKOUT_LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
        return logs

def save_workout_log(log):
    logs = load_workout_logs()
    logs.append(log)
    with open(WORKOUT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

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
# 메인 애플리케이션 클래스
# -------------------------------
class BodybuildingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("보디빌딩 운동 기록 앱")
        self.geometry("800x600")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.routine_management_frame = RoutineManagementFrame(self.notebook)
        self.workout_session_frame = WorkoutSessionFrame(self.notebook)
        self.weekly_summary_frame = WeeklySummaryFrame(self.notebook)

        self.notebook.add(self.routine_management_frame, text="루틴 관리")
        self.notebook.add(self.workout_session_frame, text="운동 세션")
        self.notebook.add(self.weekly_summary_frame, text="주간 요약")

        self.update_routine_list()

    def update_routine_list(self):
        routines = load_routines()
        self.routine_management_frame.update_routine_list(routines)
        self.workout_session_frame.update_routine_options(routines)

# -------------------------------
# 루틴 관리 프레임
# -------------------------------
class RoutineManagementFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # 좌측: 저장된 루틴 목록
        self.routine_listbox = tk.Listbox(self, height=15)
        self.routine_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.routine_listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.routine_listbox.config(yscrollcommand=scrollbar.set)

        # 우측: 버튼들
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="left", fill="y", padx=10, pady=10)
        btn_create = ttk.Button(btn_frame, text="새 루틴 생성", command=self.open_create_routine_window)
        btn_create.pack(pady=10)

    def update_routine_list(self, routines):
        self.routine_listbox.delete(0, tk.END)
        for r in routines:
            self.routine_listbox.insert(tk.END, r.name)

    def open_create_routine_window(self):
        CreateRoutineWindow(self)

# -------------------------------
# 루틴 생성 창 (운동 이름/순서만 기록)
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

        self.exercises = []  # 루틴에 추가될 운동들 (세트 정보 없음)

    def open_create_exercise_window(self):
        CreateExerciseWindow(self)

    def add_exercise(self, exercise):
        self.exercises.append(exercise)
        # 추가 순서대로 리스트에 표시 (순서 번호 포함)
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
        self.master.master.update_routine_list()

# -------------------------------
# 운동 생성 창 (운동 이름과 주동근만 입력)
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
        # 기본값은 첫 번째 항목
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
# 운동 세션 프레임 (루틴 선택)
# -------------------------------
class WorkoutSessionFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="루틴 선택:").pack(pady=5)
        self.routine_var = tk.StringVar()
        self.routine_combo = ttk.Combobox(self, textvariable=self.routine_var, state="readonly")
        self.routine_combo.pack(pady=5)
        btn_start = ttk.Button(self, text="운동 세션 시작", command=self.start_workout_session)
        btn_start.pack(pady=10)
        self.routines = []

    def update_routine_options(self, routines):
        self.routines = routines
        names = [r.name for r in routines]
        self.routine_combo['values'] = names

    def start_workout_session(self):
        selected = self.routine_var.get()
        if not selected:
            messagebox.showerror("오류", "루틴을 선택하세요.")
            return
        routine = next((r for r in self.routines if r.name == selected), None)
        if routine is None:
            messagebox.showerror("오류", "루틴을 찾을 수 없습니다.")
            return
        WorkoutSessionWindow(self, routine)

# -------------------------------
# 운동 세션 창 (실행 시 세트, reps, 무게, RIR를 입력)
# -------------------------------
class WorkoutSessionWindow(tk.Toplevel):
    def __init__(self, parent_frame, routine):
        super().__init__(parent_frame)
        self.title("운동 세션")
        self.geometry("500x600")
        self.routine = routine
        self.current_exercise_index = 0
        self.session_log = {
            "date": datetime.date.today().isoformat(),
            "routine_name": routine.name,
            "muscle_volumes": {mg: 0 for mg in MUSCLE_GROUPS},
            "sets_count": {mg: 0 for mg in MUSCLE_GROUPS}
        }
        # 현재 운동의 세트들을 임시 저장할 리스트
        self.current_exercise_sets = []
        self.build_widgets()
        self.display_current_exercise()

    def build_widgets(self):
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(expand=True, fill="both", pady=10)

        # 운동 정보
        self.exercise_info_label = ttk.Label(self.content_frame, text="", font=("Arial", 14))
        self.exercise_info_label.pack(pady=5)

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
        btn_timer = ttk.Button(btn_frame, text="타이머 실행", command=self.run_timer)
        btn_timer.pack(side="left", padx=5)

        # 추가된 세트 내역을 보여줄 리스트박스
        ttk.Label(self.content_frame, text="추가된 세트:").pack(pady=5)
        self.sets_listbox = tk.Listbox(self.content_frame, height=6)
        self.sets_listbox.pack(fill="x", padx=10, pady=5)

        # 다음 운동 또는 세션 종료 버튼
        self.next_btn = ttk.Button(self.content_frame, text="다음 운동", command=self.next_exercise)
        self.next_btn.pack(pady=10)

    def display_current_exercise(self):
        # 현재 운동 초기화: 세트 입력창 클리어 및 리스트박스 비움
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
        else:
            # 모든 운동 완료 시
            self.finish_session()

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

        # 업데이트: 운동의 주동근에 따른 총 볼륨, 세트 수 기록
        exercise = self.routine.exercises[self.current_exercise_index]
        muscle = exercise.muscle_group
        self.session_log["muscle_volumes"][muscle] += weight * reps
        self.session_log["sets_count"][muscle] += 1

        # 입력창 초기화
        self.weight_entry.delete(0, tk.END)
        self.reps_entry.delete(0, tk.END)
        self.rir_entry.delete(0, tk.END)

    def run_timer(self):
        seconds = simpledialog.askinteger("타이머", "타이머 시간을 초 단위로 입력하세요:", minvalue=1)
        if seconds:
            TimerWindow(self, seconds)

    def next_exercise(self):
        # 이동 전에 최소 한 세트 이상 입력되었는지 선택할 수 있도록 함.
        if not self.current_exercise_sets:
            if not messagebox.askyesno("확인", "현재 운동에 입력한 세트가 없습니다. 다음 운동으로 넘어가시겠습니까?"):
                return
        self.current_exercise_index += 1
        if self.current_exercise_index < len(self.routine.exercises):
            self.display_current_exercise()
        else:
            self.finish_session()

    def finish_session(self):
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
                prev = prev_volumes.get(mg, 0)
                diff = current - prev
                info += f"{mg}: 현재 볼륨 = {current}, 이전 볼륨 = {prev}, 차이 = {diff}\n"
        else:
            info += "비교할 이전 세션이 없습니다."
        messagebox.showinfo("비교 결과", info)

# -------------------------------
# 주간 요약 프레임
# -------------------------------
class WeeklySummaryFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        btn_refresh = ttk.Button(self, text="주간 요약 새로고침", command=self.show_weekly_summary)
        btn_refresh.pack(pady=10)
        self.summary_text = tk.Text(self, height=20, width=70)
        self.summary_text.pack(pady=10)

    def show_weekly_summary(self):
        logs = load_workout_logs()
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        weekly_summary = {mg: {"sets": 0, "volume": 0} for mg in MUSCLE_GROUPS}
        for log in logs:
            log_date = datetime.datetime.strptime(log["date"], "%Y-%m-%d").date()
            if start_of_week <= log_date <= end_of_week:
                for mg in MUSCLE_GROUPS:
                    weekly_summary[mg]["volume"] += log["muscle_volumes"].get(mg, 0)
                    weekly_summary[mg]["sets"] += log["sets_count"].get(mg, 0)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, f"=== 주간 요약 ({start_of_week} ~ {end_of_week}) ===\n")
        for mg in MUSCLE_GROUPS:
            self.summary_text.insert(tk.END, f"{mg}: 총 세트 수 = {weekly_summary[mg]['sets']}, 총 볼륨 = {weekly_summary[mg]['volume']}\n")

# -------------------------------
# 메인 실행
# -------------------------------
if __name__ == "__main__":
    app = BodybuildingApp()
    app.mainloop()
