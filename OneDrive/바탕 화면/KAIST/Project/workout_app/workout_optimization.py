import time
import json
import os
import datetime

# -------------------------------
# 상수 정의
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
    def __init__(self, name, muscle_group):
        self.name = name
        self.muscle_group = muscle_group
        self.sets = []  # List of SetDetail 객체

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

class Routine:
    def __init__(self, name):
        self.name = name
        self.exercises = []  # List of Exercise 객체

    def add_exercise(self, exercise):
        self.exercises.append(exercise)

    def total_volume_by_muscle(self):
        volumes = {mg: 0 for mg in MUSCLE_GROUPS}
        for ex in self.exercises:
            volumes[ex.muscle_group] += ex.total_volume()
        return volumes

    def to_dict(self):
        return {
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises]
        }

    @staticmethod
    def from_dict(data):
        routine = Routine(data["name"])
        for ex_data in data["exercises"]:
            ex = Exercise(ex_data["name"], ex_data["muscle_group"])
            for set_data in ex_data["sets"]:
                s = SetDetail(set_data["set_number"], set_data["weight"], set_data["reps"], set_data["rir"])
                ex.add_set(s)
            routine.add_exercise(ex)
        return routine

# -------------------------------
# 타이머 함수
# -------------------------------
def start_timer(seconds):
    while seconds:
        print(f"남은 시간: {seconds}초", end='\r')
        time.sleep(1)
        seconds -= 1
    print("\n타이머 종료!")

# -------------------------------
# 파일 입출력 함수들
# -------------------------------
def load_routines():
    if not os.path.exists(ROUTINES_FILE):
        return []
    with open(ROUTINES_FILE, "r") as f:
        data = json.load(f)
        routines = [Routine.from_dict(r) for r in data]
        return routines

def save_routines(routines):
    with open(ROUTINES_FILE, "w") as f:
        json.dump([r.to_dict() for r in routines], f, indent=4)

def load_workout_logs():
    if not os.path.exists(WORKOUT_LOG_FILE):
        return []
    with open(WORKOUT_LOG_FILE, "r") as f:
        logs = json.load(f)
        return logs

def save_workout_log(log):
    logs = load_workout_logs()
    logs.append(log)
    with open(WORKOUT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

# -------------------------------
# 루틴 및 운동 생성 관련 함수
# -------------------------------
def create_exercise():
    ex_name = input("운동 이름을 입력하세요: ")
    print("주동근(운동 부위)를 선택하세요:")
    for idx, mg in enumerate(MUSCLE_GROUPS):
        print(f"{idx+1}. {mg}")
    mg_choice = int(input("번호 입력: ")) - 1
    muscle_group = MUSCLE_GROUPS[mg_choice]
    exercise = Exercise(ex_name, muscle_group)

    num_sets = int(input("세트 수를 입력하세요: "))
    for i in range(num_sets):
        print(f"\n--- {ex_name}의 {i+1}번째 세트 ---")
        weight = float(input("  무게(kg): "))
        reps = int(input("  Reps 수: "))
        rir = int(input("  RIR: "))
        set_detail = SetDetail(i+1, weight, reps, rir)
        exercise.add_set(set_detail)
        # 마지막 세트가 아니라면 타이머 옵션 제공
        if i < num_sets - 1:
            timer_choice = input("다음 세트 전 타이머 실행할까요? (y/n): ")
            if timer_choice.lower() == 'y':
                seconds = int(input("타이머 시간을 초 단위로 입력하세요: "))
                start_timer(seconds)
    return exercise

def create_new_routine():
    name = input("루틴 이름을 입력하세요: ")
    routine = Routine(name)
    while True:
        add_ex = input("루틴에 운동을 추가하시겠습니까? (y/n): ")
        if add_ex.lower() != 'y':
            break
        exercise = create_exercise()
        routine.add_exercise(exercise)
    return routine

# -------------------------------
# 운동 세션 진행 및 기록 함수
# -------------------------------
def start_workout_session(routine):
    print(f"\n*** 루틴 [{routine.name}] 운동을 시작합니다. ***")
    # 이번 세션의 각 운동 세트 수를 기록 (주당 세트 수 계산용)
    total_sets = {mg: 0 for mg in MUSCLE_GROUPS}
    for ex in routine.exercises:
        print(f"\n운동: {ex.name} (부위: {ex.muscle_group})")
        for s in ex.sets:
            print(f"  세트 {s.set_number}: {s.weight}kg x {s.reps}회, RIR {s.rir}")
            total_sets[ex.muscle_group] += 1
            # 해당 세트가 마지막이 아니라면 타이머 옵션 제공
            if s.set_number < len(ex.sets):
                timer_choice = input("다음 세트 전 타이머 실행할까요? (y/n): ")
                if timer_choice.lower() == 'y':
                    seconds = int(input("타이머 시간을 초 단위로 입력하세요: "))
                    start_timer(seconds)
    # 오늘 날짜 기록
    date = datetime.date.today().isoformat()
    muscle_volumes = routine.total_volume_by_muscle()
    log = {
        "date": date,
        "routine_name": routine.name,
        "muscle_volumes": muscle_volumes,
        "sets_count": total_sets
    }
    save_workout_log(log)
    print("\n운동 기록이 저장되었습니다.")
    return log

def compare_with_previous(log):
    logs = load_workout_logs()
    routine_name = log["routine_name"]
    current_date = log["date"]
    previous_log = None
    # 최근 기록부터 역순으로 확인하여 오늘 이전의 같은 루틴 기록 찾기
    for l in logs[::-1]:
        if l["routine_name"] == routine_name and l["date"] < current_date:
            previous_log = l
            break
    if previous_log:
        print("\n=== 지난 세션과 비교 ===")
        current_volumes = log["muscle_volumes"]
        prev_volumes = previous_log["muscle_volumes"]
        for mg in MUSCLE_GROUPS:
            current = current_volumes.get(mg, 0)
            prev = prev_volumes.get(mg, 0)
            diff = current - prev
            print(f"{mg}: 현재 볼륨 = {current}, 이전 볼륨 = {prev}, 차이 = {diff}")
    else:
        print("\n비교할 이전 세션이 없습니다.")

# -------------------------------
# 주간 요약 함수
# -------------------------------
def show_weekly_summary():
    logs = load_workout_logs()
    today = datetime.date.today()
    # 이번 주 (월~일) 구하기
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    weekly_summary = {mg: {"sets": 0, "volume": 0} for mg in MUSCLE_GROUPS}

    for log in logs:
        log_date = datetime.datetime.strptime(log["date"], "%Y-%m-%d").date()
        if start_of_week <= log_date <= end_of_week:
            for mg in MUSCLE_GROUPS:
                weekly_summary[mg]["volume"] += log["muscle_volumes"].get(mg, 0)
                weekly_summary[mg]["sets"] += log["sets_count"].get(mg, 0)

    print(f"\n=== 주간 요약 ({start_of_week} ~ {end_of_week}) ===")
    for mg in MUSCLE_GROUPS:
        print(f"{mg}: 총 세트 수 = {weekly_summary[mg]['sets']}, 총 볼륨 = {weekly_summary[mg]['volume']}")

# -------------------------------
# 메인 메뉴
# -------------------------------
def main():
    routines = load_routines()
    while True:
        print("\n===============================")
        print("보디빌딩 운동 기록 앱")
        print("===============================")
        print("1. 새 루틴 생성")
        print("2. 저장된 루틴 보기")
        print("3. 운동 세션 시작")
        print("4. 주간 요약 보기")
        print("5. 종료")
        choice = input("원하는 메뉴 번호를 입력하세요: ")

        if choice == "1":
            routine = create_new_routine()
            routines.append(routine)
            save_routines(routines)
            print("루틴이 저장되었습니다.")
        elif choice == "2":
            if not routines:
                print("저장된 루틴이 없습니다.")
            else:
                print("\n저장된 루틴:")
                for idx, r in enumerate(routines):
                    print(f"{idx+1}. {r.name}")
        elif choice == "3":
            if not routines:
                print("먼저 루틴을 생성하세요.")
            else:
                print("\n운동 세션을 진행할 루틴을 선택하세요:")
                for idx, r in enumerate(routines):
                    print(f"{idx+1}. {r.name}")
                try:
                    r_choice = int(input("번호 입력: ")) - 1
                    if r_choice < 0 or r_choice >= len(routines):
                        print("잘못된 선택입니다.")
                        continue
                except ValueError:
                    print("숫자를 입력하세요.")
                    continue

                routine = routines[r_choice]
                log = start_workout_session(routine)
                compare_with_previous(log)
        elif choice == "4":
            show_weekly_summary()
        elif choice == "5":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 시도하세요.")

if __name__ == "__main__":
    main()
