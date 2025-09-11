import pythoncom
import wmi
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import threading
import datetime
import numpy as np
import time
import sys   # ✅ 리다이렉트에 필요
import pyrealsense2 as rs

# ✅ 로그 리다이렉트 클래스
class TextRedirector:
    def __init__(self, app, tag):
        self.app = app
        self.tag = tag

    def write(self, msg):
        if self.app.log_text:
            self.app.log_text.configure(state="normal")
            self.app.log_text.insert("end", msg)
            self.app.log_text.configure(state="disabled")
            self.app.log_text.see("end")  # 최신 줄로 스크롤
        # 동시에 콘솔에도 출력
        sys.__stdout__.write(msg)

    def flush(self):
        pass

    
# 리얼센스 카메라 serial number 검색용 
# Device: Intel RealSense D405, Serial: 427622273384
# Device: Intel RealSense D415, Serial: 125322063680
# Device: Intel RealSense D435, Serial: 234322070167


context = rs.context()
devices = context.query_devices()
for dev in devices:
    print(f"Device: {dev.get_info(rs.camera_info.name)}, Serial: {dev.get_info(rs.camera_info.serial_number)}")




# ===================================================================  
# AI 이미지 검사 애플리케이션 클래스
# 이 클래스는 tkinter 기반 GUI를 사용하여
# 다중 카메라의 실시간 영상 확인 및 바코드 인식 후 자동 캡처 기능을 제공합니다.
# =================================================================== 
class AIImageApp:
    def __init__(self, root):
        
        
        
        # ✅ CAM1 InstanceId 경로 (사용자 환경 맞게 수정)
        # 7&340BD62F&0&0003, 7&DAA5840&0&0005, 8&11F3FC2D&0&0000, 7&6C45F2E&0&0005, 8&277268BC&0&0003, 8&2EE012B0&0&0003
        self.CAM1_SN = "7&340BD62F"
        # 최대 6개의 카메라 장치를 저장할 리스트  #cam_num
        self.captures = [None] * 6   #cam 갯수 #cam_num
        self.initialization_done = False  # 초기화 완료 플래그 추가
        
        # 기본 설정 및 UI 초기화
        self.root = root
        self.root.title("AI Image Inspection System")
        self.root.geometry("1200x800")

        # 영상 표시 및 프레임 업데이트 여부를 제어하는 플래그
        self.running = True
        # 검사 로직(바코드 인식 및 캡처) 실행 여부를 제어하는 플래그
        self.inspection_active = False

        # 로그 기록용 위젯
        self.log_text = None  

        # ✅ stdout, stderr 리다이렉트
        sys.stdout = TextRedirector(self, "stdout")
        sys.stderr = TextRedirector(self, "stderr")

        # 영상 출력을 위한 Label 객체 리스트
        self.cam_labels = []

        # 바코드 인식 임계값 (중앙 ROI 영역의 흰색 비율)
        # self.threshold = 0.14
        
        # 뎁스 검사 설정 (기존 threshold 대신)
        self.ROI_SIZE = 100
        self.INSPECTION_SPECS = [
            {'pos': (600, 400), 'min_z': 0.4, 'max_z': 0.8},
        
        
        ]
        self.IMG_WIDTH = 1280
        self.IMG_HEIGHT = 720
        self.DIGITAL_ZOOM_LEVEL = 1.0  # 1.0: 줌 없음
        self.LASER_POWER = 150         # 0 ~ 360
        self.AUTO_EXPOSURE = True      # 자동 노출 활성화
        self.align = None  # RealSense align 객체
        
        

        # Treeview 헤더 스타일 설정
        style = ttk.Style()
        style.configure("Treeview.Heading", background="#d3d3d3", foreground="black")

        # 메뉴 및 메인 프레임 구성
        self.create_menu()
        self.create_main_frame()
        
        # 부팅중 점 애니메이션 관련 변수
        self.dot_count = 1
        self.max_dots = 12

        # 기본 HOME 화면 표시
        self.show_home()

        # 카메라 초기화는 별도 스레드로 실행 (GUI 멈춤 방지)
        # 카메라 초기화는 애플리케이션 시작 시 한 번만 수행되도록 변경
        # 이렇게 하면 '검사' 탭으로 이동할 때마다 카메라를 초기화하는 시간을 절약할 수 있습니다.
        print("[INFO] 카메라 초기화 시작...")
        threading.Thread(target=self._initialize_all_cameras, daemon=True).start()

        # 2. 검사탭이 다른 탭으로 넘어갈때 검사가 시행 안된다. 개선
        # 바코드 인식 및 이미지 캡처 로직을 담당하는 스레드를 초기화 시점에 시작하여 항상 실행되도록 합니다.
        self.inspection_thread = threading.Thread(target=self._run_inspection_logic, daemon=True)
        self.inspection_thread.start()
    def _find_camera_index_by_sn(self, sn_substring):
        """
        WMI를 통해 연결된 카메라의 PNPDeviceID에서 시리얼 번호(sn_substring)를 검색하고,
        OpenCV 인덱스와 매핑하여 해당 카메라 인덱스를 반환한다.
        """
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            target_id = None

            # === 1. WMI에서 해당 SN 포함된 장치 찾기 ===
            for item in c.Win32_PnPEntity():
                if item.PNPDeviceID and sn_substring in item.PNPDeviceID:
                    target_id = item.PNPDeviceID
                    print(f"[INFO] 매칭된 카메라: {item.Name}, PNPDeviceID={target_id}")
                    break

            if not target_id:
                print(f"[ERROR] S/N '{sn_substring}' 포함된 카메라를 찾지 못했습니다.")
                return None

            # === 2. OpenCV 인덱스 탐색 ===
            matched_index = None
            for i in range(10):  # 최대 10개 장치 탐색
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # 간단한 프레임 캡처 테스트
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        print(f"[DEBUG] OpenCV Index={i} 연결 성공")
                        # 여기서는 실제 SN ↔ Index 매핑 기능이 없으므로,
                        # SN 리스트를 기반으로 순서대로 매핑한다고 가정
                        # (실제 시스템에서는 DirectShow API로 devicePath 확인 필요)
                        matched_index = i
                        break

            if matched_index is not None:
                print(f"[INFO] S/N {sn_substring} → OpenCV Index={matched_index}")
                return matched_index
            else:
                print(f"[ERROR] OpenCV에서 SN {sn_substring} 장치를 찾을 수 없습니다.")
                return None

        except Exception as e:
            print(f"[ERROR] WMI 접근 중 예외 발생: {e}")
            return None

        finally:
            pythoncom.CoUninitialize()


        # 모든 카메라 장치를 초기화하고 연결 가능한 장치는 self.captures에 저장
    def _initialize_all_cameras(self):
        print("[DEBUG] _initialize_all_cameras 시작")
        #     # ✅ CAM1: 시리얼 번호 기반으로 인덱스 검색 → 리얼센스 적용하며 변경됨
        #     cam1_index = self._find_camera_index_by_sn(self.CAM1_SN)
        #     if cam1_index is not None:
        #         cap1 = cv2.VideoCapture(cam1_index, cv2.CAP_DSHOW)
        #         if cap1.isOpened():
        #             cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        #             cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        #             self.captures[0] = cap1
        #             print(f"[INFO] CAM1 연결 성공 (Index={cam1_index}, S/N={self.CAM1_SN})")
        #         else:
        #             print(f"[ERROR] CAM1 연결 실패 (Index={cam1_index})")
        #             self.captures[0] = None
        #     else:
        #         print("[ERROR] CAM1 S/N 기반 매핑 실패")
        #         self.captures[0] = None


        # 변경된 코드 (CAM1: RealSense D435)
        try:
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_device('125322063680')  # D435 시리얼 넘버
            config.enable_stream(rs.stream.depth, self.IMG_WIDTH, self.IMG_HEIGHT, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, self.IMG_WIDTH, self.IMG_HEIGHT, rs.format.bgr8, 30)
            profile = pipeline.start(config)
            self.align = rs.align(rs.stream.color)
            
            # 센서 설정
            depth_sensor = profile.get_device().first_depth_sensor()
            if depth_sensor.supports(rs.option.laser_power):
                print(f"레이저 파워를 {self.LASER_POWER}로 설정")
                depth_sensor.set_option(rs.option.laser_power, self.LASER_POWER)

            color_sensor = profile.get_device().first_color_sensor()
            if color_sensor.supports(rs.option.enable_auto_exposure):
                print(f"자동 노출을 {self.AUTO_EXPOSURE}로 설정")
                color_sensor.set_option(rs.option.enable_auto_exposure, 1)  # 자동 노출 활성화
            
            # 초기 프레임 테스트 (타임아웃 추가)
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            if frames:
                print("[INFO] CAM1 (RealSense D435) 초기 프레임 테스트 성공")
            else:
                print("[WARNING] CAM1 (RealSense D435) 초기 프레임 테스트 실패")
            self.captures[0] = pipeline
            print("[INFO] CAM1 (RealSense D435) 연결 성공 (S/N=125322063680)")
        except Exception as e:
            print(f"[ERROR] CAM1 (RealSense D435) 연결 실패: {e}")
            self.captures[0] = None
    
    

        # ✅ CAM2~CAM6: 순서대로 인덱스로 할당
        for i in range(1, 6):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)# MSMF 대신 DSHOW 사용
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.captures[i] = cap
                print(f"[INFO] CAM{i+1} 연결 성공 (Index={i})")
            else:
                print(f"[WARNING] CAM{i+1} 연결 실패 (Index={i})")
                self.captures[i] = None

        print("[INFO] 카메라 초기화 완료.")
        self.initialization_done = True
        
        
        
        # 상단 메뉴 구성
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        menu_bar.add_command(label="HOME", command=self.show_home)
        menu_bar.add_command(label="검사", command=self.show_inspection)
        menu_bar.add_command(label="조회", command=self.show_query)
        menu_bar.add_command(label="설정", command=self.show_settings)
        menu_bar.add_command(label="LOG", command=self.show_log)  # ✅ LOG 탭 추가

    # 메인 콘텐츠 프레임 생성
    def create_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

    # 기존 프레임 내용 제거
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # 각 카메라 연결 상태를 리스트 형태로 반환
    # 이 함수는 초기화 시점에 한 번만 호출되도록 변경되었으므로,
    # 카메라 캡처 객체(self.captures)가 이미 설정되어 있음을 가정합니다.
    def get_camera_status(self):
        if not getattr(self, 'initialization_done', False):
            return [f"CAM{i+1} -------- 부팅중" for i in range(6)]  # 초기화 미완료 시 부팅중
        status_list = []
        for i, cap in enumerate(self.captures):
            # 기존 코드, 리얼센스로 변경됨
            # if cap is None:
            #     status_list.append(f"CAM{i+1} -------- 부팅중")
            # else:
            #     try:
            #         if cap.isOpened():
            #             status_list.append(f"CAM{i+1} -------- ON")
            #         else:
            #             status_list.append(f"CAM{i+1} -------- 부팅 실패")
            #     except:
            #         status_list.append(f"CAM{i+1} -------- 부팅 실패")
            if cap is None:
                 status_list.append(f"CAM{i+1} -------- 부팅중")
                 continue
             
            # 변경된 코드
            try:
                if isinstance(cap, rs.pipeline):
                    frames = cap.wait_for_frames()
                    if frames:
                        status_list.append(f"CAM{i+1} -------- ON")
                    else:
                        status_list.append(f"CAM{i+1} -------- 부팅 실패")
                elif cap.isOpened():
                    status_list.append(f"CAM{i+1} -------- ON")
                else:
                    status_list.append(f"CAM{i+1} -------- 부팅 실패")
            except:
                status_list.append(f"CAM{i+1} -------- 부팅 실패")
        return status_list

    # HOME 화면 출력
    def show_home(self):
        self.clear_main_frame()
        # '검사' 탭에서 영상 스트리밍이 실행 중이었다면 중지합니다.
        self.running = False
        self.inspection_active = False # 검사 로직 비활성화

        label = tk.Label(self.main_frame, text="HOME - 사용법 및 설명서", font=("Arial", 20))
        label.pack(pady=20)

        # 안내 문구 추가
        guide_text = (
            "각 CAM을 부팅 중입니다. 이 동작은 10분 이상 소요될 수 있습니다.\n"
            "카메라가 1개 이상 ON이 되었을 때, 검사 화면으로 넘어가 주시기 바랍니다.\n"
            "로딩되지 않은 CAM은 검은색 화면으로 보입니다."
        )
        tk.Label(self.main_frame, text=guide_text, font=("Arial", 11)).pack(pady=10)

        # 카메라 상태 표시
        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(pady=20)

        # 상태 갱신 루프 시작
        self.update_status_labels()

        # 이미지 표시
        image_path = r"C:\\WIA_VISION\\home_image.jpg"
        if os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                max_width = 960
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_height = int(image.height * ratio)
                    image = image.resize((max_width, new_height))
                photo = ImageTk.PhotoImage(image)
                image_label = tk.Label(self.main_frame, image=photo)
                image_label.image = photo
                image_label.pack(pady=10)
            except Exception as e:
                tk.Label(self.main_frame, text=f"이미지 로딩 실패: {e}", fg="red").pack()
        else:
            tk.Label(self.main_frame, text=f"경로에 이미지 파일이 없습니다: {image_path}", fg="red").pack()

    def update_status_labels(self):
        """카메라 상태를 주기적으로 갱신 + 부팅중 애니메이션"""
        try : 
            for widget in self.status_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            print("[WARN] status_frame이 이미 파괴되어 업데이트 생략")
            return

        status_list = self.get_camera_status()

        for status in status_list:
            if "부팅중" in status:
                dots = "." * self.dot_count
                status = status + " " + dots
            tk.Label(self.status_frame, text=status, font=("Arial", 14)).pack(anchor="w")

        # 점 개수 갱신
        self.dot_count += 1
        if self.dot_count > self.max_dots:
            self.dot_count = 1

        # 5초마다 갱신
        self.root.after(5000, self.update_status_labels)
          
    # 검사 화면 구성 및 영상 표시 시작
    def show_inspection(self):
        print("[DEBUG] 검사 화면 진입 시작")
        start_time = time.time()

        self.clear_main_frame()
        self.running = True  # 영상 스트리밍 활성화
        self.inspection_active = True # 검사 로직 활성화

        # Frame 생성 및 2x3 그리드에 카메라 영상 표시용 Label 배치
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack(fill="both", expand=True)

        self.cam_labels = []
        cam_count = 4
        for i in range(2):
            for j in range(3):
                cam_index = i * 2 + j   # 0~3
                frame = tk.Label(self.grid_frame, bg="black")
                frame.grid(row=i, column=j, padx=5, pady=5, sticky="nsew")

                cam_label = tk.Label(frame, text=f"CAM{cam_index+1}", fg="white", bg="gray", font=("Arial", 10, "bold"))
                cam_label.pack(side="top", fill="x")

                video_label = tk.Label(frame, bg="black")
                video_label.pack(fill="both", expand=True)

                self.cam_labels.append(video_label)

        # 창크기에 따라 그리드 조정하기 위한 이벤트 바인딩
        for i in range(2):
            self.grid_frame.rowconfigure(i, weight=1)
        for j in range(3):
            self.grid_frame.columnconfigure(j, weight=1)
        # ✅ 여기에서 on_resize 이벤트 바인딩!
        self.grid_frame.bind("<Configure>", self.on_resize)

        # 0.5초 후 영상 출력 시작 (UI 렌더링 후 실행되도록)
        # 카메라 초기화가 이미 완료된 상태이므로 `init_cameras` 호출 대신 직접 영상 스트리밍 시작
        self.root.after(500, self.start_displaying_video)

        end_time = time.time()
        print(f"[DEBUG] 검사 화면 진입 완료 - 소요시간: {end_time - start_time:.2f}초")

    # 영상 디스플레이 시작 함수 (스레드로 update_frames 실행)
    # 1. 검사 화면으로 넘어갔을때, 각 카메라의 초기화 시간이 너무 오래 걸린다. 개선
    # 이 함수는 이제 단순히 화면 업데이트 스레드만 시작합니다. 카메라는 이미 초기화되어 있습니다.
    def start_displaying_video(self):
        # 이미 스레드가 실행 중이 아니라면 시작
        self.update_frames()
        # if not hasattr(self, '_display_thread') or not self._display_thread.is_alive():
        #     self._display_thread = threading.Thread(target=self.update_frames, daemon=True)
        #     self._display_thread.start()

    # 리사이즈 위한 함수
    def on_resize(self, event):
        # 그리드 프레임의 크기에 따라 라벨 크기 조정
        total_width = self.grid_frame.winfo_width()
        total_height = self.grid_frame.winfo_height()

        self.label_width = total_width // 2 # 2개 열에 대한 너비
        self.label_height = total_height // 3 # 2개 행에 대한 높이

    # 프레임을 지속적으로 업데이트하며 화면에 표시하는 함수
    # 3. update_frame 함수는 저해상도로 구동되도록 개선
    
    
    def update_frames(self):
        if not self.running:
            return

        frames = []

        for i, cap in enumerate(self.captures):
            # 기존 코드, 리얼센스로 변경됨
            # if cap is None:
            #     frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            # else:
            #     ret, frame = cap.read()
            #     if not ret:
            #         frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            #     else:
            #         # --- 🎯 상하/좌우 반전 ---
            #         frame = cv2.flip(frame, -1)

            #         # CAM1(0번 카메라) 바코드 감지 영역 표시
            #         if i == 0:
            #             cv2.rectangle(frame, (500, 170), (750, 400), (255, 255, 255), 2) #500, 170, 750, 400
            # 변경된 코드
            if cap is None:
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            else:
                if isinstance(cap, rs.pipeline):
                    # RealSense 프레임 읽기
                    try:
                        rs_frames = cap.wait_for_frames()
                        aligned_frames = self.align.process(rs_frames)
                        color_frame = aligned_frames.get_color_frame()
                        depth_frame = aligned_frames.get_depth_frame()
                        if color_frame and depth_frame:
                            frame = np.asanyarray(color_frame.get_data())
                            # 뎁스 검사 시각화 (복사본 사용)
                            inspection_frame = frame.copy()
                            all_ok = True
                            for spec in self.INSPECTION_SPECS:
                                u, v = spec['pos']
                                min_z, max_z = spec['min_z'], spec['max_z']
                                half_size = self.ROI_SIZE // 2
                                x_start, y_start = max(u - half_size, 0), max(v - half_size, 0)
                                x_end, y_end = min(u + half_size, self.IMG_WIDTH - 1), min(v + half_size, self.IMG_HEIGHT - 1)

                                depth_list = []
                                inlier_count = 0
                                total_count = 0

                                for y in range(y_start, y_end):
                                    for x in range(x_start, x_end):
                                        z = depth_frame.get_distance(x, y)
                                        if z > 0:
                                            total_count += 1
                                            depth_list.append(z)
                                            if min_z <= z <= max_z:
                                                inlier_count += 1

                                avg_depth = np.mean(depth_list) if depth_list else 0.0
                                inlier_ratio = (inlier_count / total_count) * 100 if total_count > 0 else 0.0

                                if inlier_ratio >= 95.0:
                                    result_text, color = "OK", (0, 255, 0)
                                else:
                                    result_text, color = "NG", (0, 0, 255)
                                    all_ok = False

                                label = f"{result_text} ({avg_depth:.3f}m, {inlier_ratio:.1f}%)"

                                # 시각화
                                cv2.rectangle(inspection_frame, (x_start, y_start), (x_end, y_end), color, 2)
                                cv2.putText(inspection_frame, label, (u - 40, v - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                            frame = inspection_frame  # 시각화된 프레임 사용
                        else:
                            frame = np.zeros((self.IMG_HEIGHT, self.IMG_WIDTH, 3), dtype=np.uint8)
                    except Exception as e:
                        print(f"[ERROR] RealSense CAM{i+1} 프레임 읽기 실패: {e}")
                        frame = np.zeros((self.IMG_HEIGHT, self.IMG_WIDTH, 3), dtype=np.uint8)
                else:
                    ret, frame = cap.read()
                    if not ret:
                        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                # --- 🎯 상하/좌우 반전 ---
                frame = cv2.flip(frame, -1)

                # CAM1(0번 카메라) 바코드 감지 영역 표시
                if i == 0:
                    cv2.rectangle(frame, (500, 170), (750, 400), (255, 255, 255), 2) #500, 170, 750, 400
            
            frames.append(frame)



        # === UI 라벨 업데이트 (동적 리사이즈 적용) ===
        for i in range(len(frames)):
            if i < len(self.cam_labels):  # Label 존재할 때만 업데이트
                frame_rgb = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)

                width = getattr(self, "label_width", 1280)
                height = getattr(self, "label_height", 720)

                imgtk = ImageTk.PhotoImage(image=img.resize((width, height)))
                self.cam_labels[i].imgtk = imgtk
                self.cam_labels[i].configure(image=imgtk)

        # 120ms 후 반복  (1/0.12)
        if self.running:
            self.root.after(150, self.update_frames)

    def _run_inspection_logic(self):
        """Background thread for inspection logic (placeholder)."""
        while True:
            if self.inspection_active:
                time.sleep(0.2)
            else:
                time.sleep(0.2)

    def detect_barcode_in_center(self, frame):
        return False

    def detect_depth_specs(self, depth_frame):
        return False

    def capture_images(self):
        pass

    def show_query(self):
        self.clear_main_frame()

    def open_large_image(self, event=None):
        pass

    def load_date_options(self):
        pass

    def search_images(self):
        pass

    def display_selected_image(self, event):
        pass

    def show_settings(self):
        self.clear_main_frame()

    def show_log(self):
        self.clear_main_frame()
        self.log_text = tk.Text(self.main_frame, wrap="word", state="disabled", bg="black", fg="white")
        self.log_text.pack(fill="both", expand=True)

    def confirm_and_save(self):
        pass

    def update_threshold(self, value):
        pass

    def on_close(self):
        self.running = False
        self.inspection_active = False
        for cap in self.captures:
            if cap:
                try:
                    if isinstance(cap, rs.pipeline):
                        cap.stop()
                    else:
                        cap.release()
                except Exception:
                    pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AIImageApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
