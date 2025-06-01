import json
import os
from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import hashlib
import requests
import uuid

# Định nghĩa đường dẫn đến các tệp dữ liệu JSON để lưu thông tin người dùng, sự kiện và yêu cầu sự kiện
USERS_FILE = "users.json"
EVENTS_FILE = "events.json"
REQUESTS_FILE = "event_requests.json"

# Khởi tạo các tệp dữ liệu nếu chưa tồn tại để đảm bảo ứng dụng hoạt động ngay từ lần chạy đầu tiên
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"admin": {"password": "21232f297a57a5a743894a0e4a801fc3", "role": "admin", "balance": 0}}, f)

if not os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(REQUESTS_FILE):
    with open(REQUESTS_FILE, 'w') as f:
        json.dump([], f)

class EventManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Quản Lý Sự Kiện")
        self.root.geometry("1000x600")
        self.root.configure(bg="#0078D7")  

        self.current_user = None
        self.user_role = None

        # Tùy chỉnh giao diện cho bảng Treeview (màu sắc, kích thước, kiểu chữ)
        style = ttk.Style()
        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground="#000000",
                        rowheight=25,
                        fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading",
                        background="#0078D7",
                        foreground="#0000FF",  
                        font=("Arial", 10, "bold"))
        style.map("Treeview",
                  background=[('selected', '#005BB5')])

        self.setup_login_ui()

    def setup_login_ui(self):
        """Thiết lập giao diện đăng nhập để người dùng nhập thông tin xác thực"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Đăng Nhập Hệ Thống", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=20)

        Label(frame, text="Tên đăng nhập:", bg="#0078D7", fg="#FFFFFF").pack()
        self.username_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.username_entry.pack(pady=5)

        Label(frame, text="Mật khẩu:", bg="#0078D7", fg="#FFFFFF").pack()
        self.password_entry = Entry(frame, show="*", bg="#FFFFFF", fg="#000000")
        self.password_entry.pack(pady=5)

        Button(frame, text="Đăng nhập", command=self.login, bg="#FFFFFF", fg="#0078D7").pack(pady=20)
        Button(frame, text="Đăng ký tài khoản", command=self.setup_register_ui, bg="#FFFFFF", fg="#0078D7").pack()

    def setup_register_ui(self):
        """Thiết lập giao diện đăng ký"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Đăng Ký Tài Khoản", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=20)

        Label(frame, text="Tên đăng nhập:", bg="#0078D7", fg="#FFFFFF").pack()
        self.reg_username_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.reg_username_entry.pack(pady=5)

        Label(frame, text="Mật khẩu:", bg="#0078D7", fg="#FFFFFF").pack()
        self.reg_password_entry = Entry(frame, show="*", bg="#FFFFFF", fg="#000000")
        self.reg_password_entry.pack(pady=5)

        Label(frame, text="Xác nhận mật khẩu:", bg="#0078D7", fg="#FFFFFF").pack()
        self.reg_confirm_password_entry = Entry(frame, show="*", bg="#FFFFFF", fg="#000000")
        self.reg_confirm_password_entry.pack(pady=5)

        Button(frame, text="Đăng ký", command=self.register_user, bg="#FFFFFF", fg="#0078D7").pack(pady=20)
        Button(frame, text="Quay lại đăng nhập", command=self.setup_login_ui, bg="#FFFFFF", fg="#0078D7").pack()

    def setup_main_ui(self):
        """Thiết lập giao diện chính của ứng dụng dựa trên vai trò người dùng"""
        self.clear_window()

        menubar = Menu(self.root, bg="#0078D7", fg="#FFFFFF")
        file_menu = Menu(menubar, tearoff=0, bg="#0078D7", fg="#FFFFFF")
        file_menu.add_command(label="Nạp tiền", command=self.deposit_money_ui)
        file_menu.add_command(label="Đăng xuất", command=self.logout)
        file_menu.add_command(label="Thoát", command=self.root.quit)
        menubar.add_cascade(label="Tệp", menu=file_menu)

        events_menu = Menu(menubar, tearoff=0, bg="#0078D7", fg="#FFFFFF")
        events_menu.add_command(label="Xem sự kiện", command=self.show_events)
        if self.user_role == "admin":
            events_menu.add_command(label="Thêm sự kiện", command=self.add_event_ui)
            events_menu.add_command(label="Quản lý yêu cầu sự kiện", command=self.manage_event_requests_ui)
        else:
            events_menu.add_command(label="Yêu cầu thêm sự kiện", command=self.request_event_ui)
        events_menu.add_command(label="Đặt vé", command=self.book_ticket_ui)
        if self.user_role == "admin":
            events_menu.add_command(label="Thống kê", command=self.show_statistics)
        menubar.add_cascade(label="Sự kiện", menu=events_menu)

        if self.user_role == "admin":
            admin_menu = Menu(menubar, tearoff=0, bg="#0078D7", fg="#FFFFFF")
            admin_menu.add_command(label="Quản lý người dùng", command=self.manage_users_ui)
            menubar.add_cascade(label="Quản trị", menu=admin_menu)

        self.root.config(menu=menubar)

        users = self.load_users()
        balance = users[self.current_user].get('balance', 0)
        Label(self.root, text=f"Số dư ví: {balance:,} VND", font=("Arial", 12), bg="#0078D7", fg="#FFFFFF").pack(anchor=NE, padx=10)

        buttons_frame = Frame(self.root, bg="#0078D7")
        buttons_frame.pack(pady=10)
        Button(buttons_frame, text="Nạp tiền", command=self.deposit_money_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Đăng xuất", command=self.logout, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

        self.show_events()

    def deposit_money_ui(self):
        """Thiết kế giao diện nạp tiền vào ví, hiển thị số dư hiện tại"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Nạp Tiền Vào Ví", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        users = self.load_users()
        balance = users[self.current_user].get('balance', 0)
        Label(frame, text=f"Số dư hiện tại: {balance:,} VND", bg="#0078D7", fg="#FFFFFF").pack(pady=5)

        Label(frame, text="Số tiền nạp (VND):", bg="#0078D7", fg="#FFFFFF").pack()
        self.deposit_amount_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.deposit_amount_entry.pack(pady=5)

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Nạp tiền", command=self.deposit_money, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Quay lại", command=self.setup_main_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def manage_users_ui(self):
        """Xây dựng giao diện quản lý người dùng (chỉ admin), hỗ trợ thêm/xóa/thay đổi vai trò"""
        self.clear_window()

        Label(self.root, text="Quản Lý Người Dùng", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        self.users_tree = ttk.Treeview(self.root, columns=("Username", "Role", "Balance"), show="headings")
        self.users_tree.heading("Username", text="Tên đăng nhập")
        self.users_tree.heading("Role", text="Vai trò")
        self.users_tree.heading("Balance", text="Số dư ví")
        self.users_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.load_users_to_tree()

        buttons_frame = Frame(self.root, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Thêm người dùng", command=self.add_user_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Xóa người dùng", command=self.delete_user, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Thay đổi vai trò", command=self.change_user_role, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Quay lại", command=self.setup_main_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def show_events(self):
        """Hiển thị danh sách sự kiện trong bảng Treeview với thông tin chi tiết"""
        self.clear_window()

        Label(self.root, text="Danh Sách Sự Kiện", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        users = self.load_users()
        balance = users[self.current_user].get('balance', 0)
        Label(self.root, text=f"Số dư ví: {balance:,} VND", font=("Arial", 12), bg="#0078D7", fg="#FFFFFF").pack(anchor=NE, padx=10)

        self.events_tree = ttk.Treeview(self.root, columns=("ID", "Tên", "Ngày", "Địa điểm", "Mô tả", "Số người", "Giá vé"), show="headings", selectmode="extended")
        self.events_tree.heading("ID", text="ID")
        self.events_tree.heading("Tên", text="Tên sự kiện")
        self.events_tree.heading("Ngày", text="Ngày diễn ra")
        self.events_tree.heading("Địa điểm", text="Địa điểm")
        self.events_tree.heading("Mô tả", text="Mô tả")
        self.events_tree.heading("Số người", text="Số người tham gia")
        self.events_tree.heading("Giá vé", text="Giá vé (VND)")
        self.events_tree.column("ID", width=50)
        self.events_tree.column("Mô tả", width=300)
        self.events_tree.column("Số người", width=100)
        self.events_tree.column("Giá vé", width=100)
        self.events_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.load_events_to_tree()

        buttons_frame = Frame(self.root, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Nạp tiền", command=self.deposit_money_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        if self.user_role == "admin":
            Button(buttons_frame, text="Thêm sự kiện", command=self.add_event_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
            Button(buttons_frame, text="Quản lý yêu cầu sự kiện", command=self.manage_event_requests_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
            Button(buttons_frame, text="Nhập từ web", command=self.import_events_from_web, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
            Button(buttons_frame, text="Sửa sự kiện", command=self.edit_event_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        else:
            Button(buttons_frame, text="Yêu cầu thêm sự kiện", command=self.request_event_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Xóa sự kiện", command=self.delete_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Đặt vé", command=self.book_ticket_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        if self.user_role == "admin":
            Button(buttons_frame, text="Thống kê", command=self.show_statistics, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
            Button(buttons_frame, text="Quản lý người dùng", command=self.manage_users_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Đăng xuất", command=self.logout, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def show_statistics(self):
        """Hiển thị thống kê doanh thu sự kiện trong bảng Treeview (chỉ admin)"""
        if self.user_role != "admin":
            messagebox.showerror("Lỗi", "Chỉ quản trị viên mới có quyền xem thống kê")
            return

        self.clear_window()

        Label(self.root, text="Thống Kê Doanh Thu", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        total_revenue = 0
        events = self.load_events()

        stats_tree = ttk.Treeview(self.root, columns=("ID", "Tên", "Số vé", "Giá vé", "Doanh thu"), show="headings")
        stats_tree.heading("ID", text="ID")
        stats_tree.heading("Tên", text="Tên sự kiện")
        stats_tree.heading("Số vé", text="Số vé đã bán")
        stats_tree.heading("Giá vé", text="Giá vé (VND)")
        stats_tree.heading("Doanh thu", text="Doanh thu (VND)")
        stats_tree.column("ID", width=50)
        stats_tree.column("Số vé", width=100)
        stats_tree.column("Giá vé", width=100)
        stats_tree.column("Doanh thu", width=150)
        stats_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for event in events:
            participants = event.get('current_participants', 0)
            price = event.get('price', 0)
            revenue = participants * price
            total_revenue += revenue
            stats_tree.insert("", "end", values=(
                event['id'],
                event['name'],
                participants,
                f"{price:,}",
                f"{revenue:,}"
            ))

        Label(self.root, text=f"Tổng doanh thu tất cả sự kiện: {total_revenue:,} VND",
              font=("Arial", 12, "bold"), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        buttons_frame = Frame(self.root, bg="#0078D7")
        buttons_frame.pack(pady=10)
        Button(buttons_frame, text="Quay lại", command=self.show_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def request_event_ui(self):
        """Thiết lập giao diện yêu cầu thêm sự kiện cho người dùng thường"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Yêu Cầu Thêm Sự Kiện", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        Label(frame, text="Tên sự kiện:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_name_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_name_entry.pack(pady=5)

        Label(frame, text="Ngày diễn ra (dd/mm/yyyy):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_date_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_date_entry.pack(pady=5)

        Label(frame, text="Địa điểm:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_location_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_location_entry.pack(pady=5)

        Label(frame, text="Số người tham gia tối đa:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_capacity_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_capacity_entry.pack(pady=5)

        Label(frame, text="Giá vé (VND):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_price_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_price_entry.pack(pady=5)

        Label(frame, text="Mô tả:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_description_entry = Text(frame, width=50, height=5, bg="#FFFFFF", fg="#000000")
        self.event_description_entry.pack(pady=5)

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Gửi yêu cầu", command=self.send_event_request, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Nhập từ web", command=self.request_event_from_web, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Hủy", command=self.show_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def add_event_ui(self):
        """Thiết lập giao diện thêm sự kiện (chỉ dành cho admin)"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Thêm Sự Kiện Mới", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        Label(frame, text="Tên sự kiện:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_name_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_name_entry.pack(pady=5)

        Label(frame, text="Ngày diễn ra (dd/mm/yyyy):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_date_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_date_entry.pack(pady=5)

        Label(frame, text="Địa điểm:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_location_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_location_entry.pack(pady=5)

        Label(frame, text="Số người tham gia tối đa:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_capacity_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_capacity_entry.pack(pady=5)

        Label(frame, text="Giá vé (VND):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_price_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_price_entry.pack(pady=5)

        Label(frame, text="Mô tả:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_description_entry = Text(frame, width=50, height=5, bg="#FFFFFF", fg="#000000")
        self.event_description_entry.pack(pady=5)

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Lưu", command=self.save_event, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Hủy", command=self.show_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def manage_event_requests_ui(self):
        """Hiển thị danh sách yêu cầu sự kiện (admin) với thông tin tương tự và người yêu cầu"""
        self.clear_window()

        Label(self.root, text="Quản Lý Yêu Cầu Sự Kiện", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        self.requests_tree = ttk.Treeview(self.root, columns=("ID", "Tên", "Ngày", "Địa điểm", "Mô tả", "Số người", "Giá vé", "Người yêu cầu"), show="headings", selectmode="extended")
        self.requests_tree.heading("ID", text="ID")
        self.requests_tree.heading("Tên", text="Tên sự kiện")
        self.requests_tree.heading("Ngày", text="Ngày diễn ra")
        self.requests_tree.heading("Địa điểm", text="Địa điểm")
        self.requests_tree.heading("Mô tả", text="Mô tả")
        self.requests_tree.heading("Số người", text="Số người tối đa")
        self.requests_tree.heading("Giá vé", text="Giá vé (VND)")
        self.requests_tree.heading("Người yêu cầu", text="Người yêu cầu")
        self.requests_tree.column("ID", width=50)
        self.requests_tree.column("Mô tả", width=200)
        self.requests_tree.column("Số người", width=100)
        self.requests_tree.column("Giá vé", width=100)
        self.requests_tree.column("Người yêu cầu", width=100)
        self.requests_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.load_requests_to_tree()

        buttons_frame = Frame(self.root, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Chấp nhận yêu cầu", command=self.accept_event_requests, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Từ chối yêu cầu", command=self.reject_event_requests, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Quay lại", command=self.show_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def edit_event_ui(self):
        """Sửa thông tin sự kiện (admin hoặc người tạo): Cập nhật tên, ngày, địa điểm, sức chứa, giá vé, mô tả trong events.json."""
        selected_item = self.events_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một sự kiện để sửa")
            return

        if len(selected_item) > 1:
            messagebox.showwarning("Cảnh báo", "Chỉ có thể sửa một sự kiện tại một thời điểm")
            return

        event_id = self.events_tree.item(selected_item[0])['values'][0]

        events = self.load_events()
        event = next((e for e in events if e['id'] == str(event_id)), None)

        if not event:
            messagebox.showerror("Lỗi", f"Không tìm thấy sự kiện với ID {event_id}")
            print(f"Lỗi: Không tìm thấy sự kiện với ID {event_id} trong events.json")
            return

        if self.user_role != "admin" and event.get('created_by', '') != self.current_user:
            messagebox.showerror("Lỗi", "Bạn không có quyền sửa sự kiện này")
            return

        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Sửa Sự Kiện", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        Label(frame, text="Tên sự kiện:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_name_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_name_entry.insert(0, event['name'])
        self.event_name_entry.pack(pady=5)

        Label(frame, text="Ngày diễn ra (dd/mm/yyyy):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_date_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_date_entry.insert(0, event['date'])
        self.event_date_entry.pack(pady=5)

        Label(frame, text="Địa điểm:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_location_entry = Entry(frame, width=50, bg="#FFFFFF", fg="#000000")
        self.event_location_entry.insert(0, event['location'])
        self.event_location_entry.pack(pady=5)

        Label(frame, text="Số người tham gia tối đa:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_capacity_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_capacity_entry.insert(0, str(event.get('capacity', 0)))
        self.event_capacity_entry.pack(pady=5)

        Label(frame, text="Giá vé (VND):", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_price_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.event_price_entry.insert(0, str(event.get('price', 0)))
        self.event_price_entry.pack(pady=5)

        Label(frame, text="Mô tả:", bg="#0078D7", fg="#FFFFFF").pack()
        self.event_description_entry = Text(frame, width=50, height=5, bg="#FFFFFF", fg="#000000")
        self.event_description_entry.insert("1.0", event['description'])
        self.event_description_entry.pack(pady=5)

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Lưu", command=lambda: self.save_event(event_id), bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Hủy", command=self.show_events, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def book_ticket_ui(self):
        """Thiết kế giao diện đặt vé sự kiện, hỗ trợ chọn số lượng vé"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Đặt Vé Sự Kiện", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        users = self.load_users()
        balance = users[self.current_user].get('balance', 0)
        Label(frame, text=f"Số dư ví: {balance:,} VND", bg="#0078D7", fg="#FFFFFF").pack(pady=5)

        self.events_tree = ttk.Treeview(frame, columns=("ID", "Tên", "Ngày", "Địa điểm", "Mô tả", "Số người", "Giá vé"), show="headings")
        self.events_tree.heading("ID", text="ID")
        self.events_tree.heading("Tên", text="Tên sự kiện")
        self.events_tree.heading("Ngày", text="Ngày diễn ra")
        self.events_tree.heading("Địa điểm", text="Địa điểm")
        self.events_tree.heading("Mô tả", text="Mô tả")
        self.events_tree.heading("Số người", text="Số người tham gia")
        self.events_tree.heading("Giá vé", text="Giá vé (VND)")
        self.events_tree.column("ID", width=30)
        self.events_tree.column("Mô tả", width=300)
        self.events_tree.column("Số người", width=100)
        self.events_tree.column("Giá vé", width=100)
        self.events_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.load_events_to_tree()

        quantity_frame = Frame(frame, bg="#0078D7")
        quantity_frame.pack(pady=10)
        Label(quantity_frame, text="Số lượng vé:", bg="#0078D7", fg="#FFFFFF").pack(side=LEFT)
        self.ticket_quantity_entry = Entry(quantity_frame, width=5, bg="#FFFFFF", fg="#000000")
        self.ticket_quantity_entry.insert(0, "1")
        self.ticket_quantity_entry.pack(side=LEFT, padx=5)
        Button(quantity_frame, text="-", command=self.decrement_ticket_quantity, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(quantity_frame, text="+", command=self.increment_ticket_quantity, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Đặt vé", command=self.book_ticket, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Nạp tiền", command=self.deposit_money_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Quay lại", command=self.setup_main_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def increment_ticket_quantity(self):
        """Tăng số lượng vé trong ô nhập khi nhấn nút '+'"""
        try:
            current = int(self.ticket_quantity_entry.get())
            self.ticket_quantity_entry.delete(0, END)
            self.ticket_quantity_entry.insert(0, str(current + 1))
        except ValueError:
            self.ticket_quantity_entry.delete(0, END)
            self.ticket_quantity_entry.insert(0, "1")

    def decrement_ticket_quantity(self):
        """Giảm số lượng vé trong ô nhập khi nhấn nút '-' (tối thiểu 1)"""
        try:
            current = int(self.ticket_quantity_entry.get())
            if current > 1:
                self.ticket_quantity_entry.delete(0, END)
                self.ticket_quantity_entry.insert(0, str(current - 1))
        except ValueError:
            self.ticket_quantity_entry.delete(0, END)
            self.ticket_quantity_entry.insert(0, "1")

    def add_user_ui(self):
        """Tạo giao diện thêm người dùng mới với thông tin tên, mật khẩu và vai trò (chỉ admin)"""
        self.clear_window()

        frame = Frame(self.root, bg="#0078D7")
        frame.pack(expand=True)

        Label(frame, text="Thêm Người Dùng Mới", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        Label(frame, text="Tên đăng nhập:", bg="#0078D7", fg="#FFFFFF").pack()
        self.new_username_entry = Entry(frame, bg="#FFFFFF", fg="#000000")
        self.new_username_entry.pack(pady=5)

        Label(frame, text="Mật khẩu:", bg="#0078D7", fg="#FFFFFF").pack()
        self.new_password_entry = Entry(frame, show="*", bg="#FFFFFF", fg="#000000")
        self.new_password_entry.pack(pady=5)

        Label(frame, text="Vai trò:", bg="#0078D7", fg="#FFFFFF").pack()
        self.new_role_var = StringVar(value="user")
        Radiobutton(frame, text="Người dùng", variable=self.new_role_var, value="user", bg="#0078D7", fg="#FFFFFF", selectcolor="#005BB5").pack()
        Radiobutton(frame, text="Quản trị", variable=self.new_role_var, value="admin", bg="#0078D7", fg="#FFFFFF", selectcolor="#005BB5").pack()

        buttons_frame = Frame(frame, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Lưu", command=self.save_new_user, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Hủy", command=self.manage_users_ui, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def load_users(self):
        """Tải dữ liệu người dùng từ tệp JSON"""
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Lỗi khi tải người dùng: {e}")
            return {}

    def save_users(self, users):
        """Lưu dữ liệu người dùng vào tệp JSON"""
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=4)
        except Exception as e:
            print(f"Lỗi khi lưu người dùng: {e}")
            messagebox.showerror("Lỗi", "Không thể lưu dữ liệu người dùng")

    def load_events(self):
        """Tải dữ liệu sự kiện từ tệp JSON"""
        try:
            with open(EVENTS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Lỗi khi tải sự kiện: {e}")
            return []

    def save_events(self, events):
        """Lưu dữ liệu sự kiện vào tệp JSON"""
        try:
            with open(EVENTS_FILE, 'w') as f:
                json.dump(events, f, indent=4)
        except Exception as e:
            print(f"Lỗi khi lưu sự kiện: {e}")
            messagebox.showerror("Lỗi", "Không thể lưu dữ liệu sự kiện")

    def load_requests(self):
        """Tải yêu cầu sự kiện từ tệp JSON"""
        try:
            with open(REQUESTS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Lỗi khi tải yêu cầu: {e}")
            return []

    def save_requests(self, requests):
        """Lưu yêu cầu sự kiện vào tệp JSON"""
        try:
            with open(REQUESTS_FILE, 'w') as f:
                json.dump(requests, f, indent=4)
        except Exception as e:
            print(f"Lỗi khi lưu yêu cầu: {e}")
            messagebox.showerror("Lỗi", "Không thể lưu yêu cầu sự kiện")

    def load_users_to_tree(self):
        """Cập nhật danh sách người dùng vào bảng Treeview để hiển thị"""
        users = self.load_users()
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for username, data in users.items():
            self.users_tree.insert("", "end", values=(username, data['role'], f"{data.get('balance', 0):,}"))

    def load_events_to_tree(self):
        """Cập nhật danh sách sự kiện vào bảng Treeview để hiển thị chi tiết"""
        events = self.load_events()
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        for event in events:
            participants = f"{event.get('current_participants', 0)}/{event.get('capacity', 0)}"
            price = f"{event.get('price', 0):,}"
            self.events_tree.insert("", "end", values=(
                event['id'],
                event['name'],
                event['date'],
                event['location'],
                event['description'],
                participants,
                price
            ))

    def load_requests_to_tree(self):
        """Cập nhật danh sách yêu cầu sự kiện vào bảng Treeview để quản lý"""
        requests = self.load_requests()
        for item in self.requests_tree.get_children():
            self.requests_tree.delete(item)
        for request in requests:
            self.requests_tree.insert("", "end", values=(
                request['id'],
                request['name'],
                request['date'],
                request['location'],
                request['description'],
                request['capacity'],
                f"{request['price']:,}",
                request['requested_by']
            ))

    def hash_password(self, password):
        """Mã hóa mật khẩu bằng MD5 (đơn giản, trong môi trường sản xuất nên dùng mã hóa mạnh hơn)"""
        return hashlib.md5(password.encode()).hexdigest()

    def login(self):
        """Xử lý đăng nhập, kiểm tra tên đăng nhập và mật khẩu"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        users = self.load_users()

        if username not in users:
            messagebox.showerror("Lỗi", "Tên đăng nhập không tồn tại")
            return

        hashed_password = self.hash_password(password)
        if users[username]['password'] != hashed_password:
            messagebox.showerror("Lỗi", "Mật khẩu không đúng")
            return

        self.current_user = username
        self.user_role = users[username]['role']
        self.setup_main_ui()

    def logout(self):
        """Xử lý quá trình đăng xuất"""
        self.current_user = None
        self.user_role = None
        self.setup_login_ui()

    def register_user(self):
        """Xử lý đăng ký tài khoản mới, kiểm tra thông tin và lưu vào tệp JSON"""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm_password = self.reg_confirm_password_entry.get()

        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        if password != confirm_password:
            messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp")
            return

        users = self.load_users()

        if username in users:
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại")
            return

        users[username] = {
            "password": self.hash_password(password),
            "role": "user",
            "balance": 0
        }

        self.save_users(users)
        messagebox.showinfo("Thành công", "Đăng ký tài khoản thành công")
        self.setup_login_ui()

    def deposit_money(self):
        """Xử lý nạp tiền vào ví, cập nhật số dư người dùng"""
        amount = self.deposit_amount_entry.get()

        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền nạp phải là số nguyên dương")
            return

        users = self.load_users()
        users[self.current_user]['balance'] = users[self.current_user].get('balance', 0) + amount
        self.save_users(users)
        messagebox.showinfo("Thành công", f"Đã nạp {amount:,} VND. Số dư mới: {users[self.current_user]['balance']:,} VND")
        self.setup_main_ui()

    def send_event_request(self):
        """Gửi yêu cầu tạo sự kiện tới admin"""
        name = self.event_name_entry.get()
        date = self.event_date_entry.get()
        location = self.event_location_entry.get()
        capacity = self.event_capacity_entry.get()
        price = self.event_price_entry.get()
        description = self.event_description_entry.get("1.0", "end-1c")

        if not name or not date or not location or not capacity or not price:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin")
            return

        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Lỗi", "Ngày không đúng định dạng (dd/mm/yyyy)")
            return

        try:
            capacity = int(capacity)
            price = int(price)
            if capacity <= 0 or price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số người tham gia tối đa phải là số nguyên dương và giá vé không được âm")
            return

        requests = self.load_requests()
        request_id = str(uuid.uuid4())

        requests.append({
            "id": request_id,
            "name": name,
            "date": date,
            "location": location,
            "capacity": capacity,
            "price": price,
            "description": description,
            "requested_by": self.current_user
        })

        self.save_requests(requests)
        messagebox.showinfo("Thành công", "Yêu cầu thêm sự kiện đã được gửi tới admin")
        self.show_events()

    def save_event(self, event_id=None):
        """Lưu hoặc cập nhật sự kiện, kiểm tra quyền admin và dữ liệu hợp lệ (chỉ dành cho admin)"""
        if self.user_role != "admin":
            messagebox.showerror("Lỗi", "Chỉ quản trị viên mới có quyền thêm/sửa sự kiện")
            return

        name = self.event_name_entry.get()
        date = self.event_date_entry.get()
        location = self.event_location_entry.get()
        capacity = self.event_capacity_entry.get()
        price = self.event_price_entry.get()
        description = self.event_description_entry.get("1.0", "end-1c")

        if not name or not date or not location or not capacity or not price:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin")
            return

        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Lỗi", "Ngày không đúng định dạng (dd/mm/yyyy)")
            return

        try:
            capacity = int(capacity)
            price = int(price)
            if capacity <= 0 or price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số người tham gia tối đa phải là số nguyên dương và giá vé không được âm")
            return

        events = self.load_events()

        if event_id:
            for event in events:
                if event['id'] == str(event_id):
                    event['name'] = name
                    event['date'] = date
                    event['location'] = location
                    event['capacity'] = capacity
                    event['price'] = price
                    event['description'] = description
                    event['current_participants'] = event.get('current_participants', 0)
                    if event['current_participants'] > capacity:
                        messagebox.showerror("Lỗi", "Số người tham gia hiện tại vượt quá sức chứa mới")
                        return
                    break
        else:
            new_id = str(max([int(e['id']) for e in events] or [0]) + 1)
            events.append({
                "id": new_id,
                "name": name,
                "date": date,
                "location": location,
                "capacity": capacity,
                "price": price,
                "current_participants": 0,
                "description": description,
                "created_by": self.current_user
            })

        self.save_events(events)
        messagebox.showinfo("Thành công", "Đã lưu sự kiện thành công")
        self.show_events()

    def delete_events(self):
        """Xóa sự kiện (admin hoặc người tạo): Loại bỏ sự kiện khỏi events.json."""
        selected_items = self.events_tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một sự kiện để xóa")
            return

        events = self.load_events()
        deleted_count = 0

        for item in selected_items:
            event_id = self.events_tree.item(item)['values'][0]
            event = next((e for e in events if e['id'] == str(event_id)), None)

            if not event:
                messagebox.showerror("Lỗi", f"Không tìm thấy sự kiện với ID {event_id}")
                print(f"Lỗi: Không tìm thấy sự kiện với ID {event_id} trong events.json")
                continue

            if self.user_role != "admin" and event.get('created_by', '') != self.current_user:
                messagebox.showerror("Lỗi", f"Bạn không có quyền xóa sự kiện '{event['name']}'")
                continue

            events = [e for e in events if e['id'] != str(event_id)]
            deleted_count += 1

        if deleted_count == 0:
            messagebox.showinfo("Thông báo", "Không có sự kiện nào được xóa")
            return

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa {deleted_count} sự kiện đã chọn?"):
            return

        self.save_events(events)
        messagebox.showinfo("Thành công", f"Đã xóa {deleted_count} sự kiện thành công")
        self.show_events()

    def book_ticket(self):
        """Xử lý đặt vé, kiểm tra số dư và sức chứa sự kiện"""
        selected_item = self.events_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một sự kiện để đặt vé")
            return

        event_id = self.events_tree.item(selected_item[0])['values'][0]

        events = self.load_events()
        event = next((e for e in events if e['id'] == str(event_id)), None)

        if not event:
            messagebox.showerror("Lỗi", f"Không tìm thấy sự kiện với ID {event_id}")
            print(f"Lỗi: Không tìm thấy sự kiện với ID {event_id} trong events.json")
            return

        try:
            quantity = int(self.ticket_quantity_entry.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Số lượng vé phải là số nguyên dương")
            return

        current_participants = event.get('current_participants', 0)
        capacity = event.get('capacity', 0)
        price = event.get('price', 0)

        if current_participants + quantity > capacity:
            messagebox.showerror("Lỗi", f"Sự kiện '{event['name']}' không đủ vé. Số vé còn lại: {capacity - current_participants}")
            return

        users = self.load_users()
        balance = users[self.current_user].get('balance', 0)
        total_cost = price * quantity

        if balance < total_cost:
            messagebox.showerror("Lỗi", f"Số dư không đủ! Cần {total_cost:,} VND, hiện có {balance:,} VND")
            return

        if not messagebox.askyesno("Xác nhận",
                                 f"Xác nhận đặt {quantity} vé cho sự kiện '{event['name']}'? Tổng giá: {total_cost:,} VND"):
            return

        event['current_participants'] += quantity
        users[self.current_user]['balance'] -= total_cost
        self.save_events(events)
        self.save_users(users)
        messagebox.showinfo("Thành công",
                           f"Đặt {quantity} vé thành công! Số người tham gia: {event['current_participants']}/{capacity}\n"
                           f"Số dư còn lại: {users[self.current_user]['balance']:,} VND")
        self.load_events_to_tree()

    def save_new_user(self):
        """Lưu người dùng mới (chỉ dành cho admin)"""
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        role = self.new_role_var.get()

        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        users = self.load_users()

        if username in users:
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại")
            return

        users[username] = {
            "password": self.hash_password(password),
            "role": role,
            "balance": 0
        }

        self.save_users(users)
        messagebox.showinfo("Thành công", "Đã thêm người dùng thành công")
        self.manage_users_ui()

    def delete_user(self):
        """Xóa người dùng (admin): Loại bỏ tài khoản khỏi users.json (trừ tài khoản admin và tài khoản đang đăng nhập)."""
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người dùng để xóa")
            return

        username = self.users_tree.item(selected_item[0])['values'][0]

        if username == "admin":
            messagebox.showerror("Lỗi", "Không thể xóa tài khoản admin")
            return

        if username == self.current_user:
            messagebox.showerror("Lỗi", "Không thể xóa tài khoản đang đăng nhập")
            return

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa người dùng {username}?"):
            return

        users = self.load_users()
        users.pop(username, None)
        self.save_users(users)
        messagebox.showinfo("Thành công", "Đã xóa người dùng thành công")
        self.load_users_to_tree()

    def change_user_role(self):
        """Thay đổi vai trò người dùng (admin): Chuyển đổi giữa "user" và "admin" trong users.json."""
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người dùng để thay đổi vai trò")
            return

        username = self.users_tree.item(selected_item[0])['values'][0]

        if username == "admin":
            messagebox.showerror("Lỗi", "Không thể thay đổi vai trò của admin")
            return

        users = self.load_users()
        current_role = users[username]['role']
        new_role = "admin" if current_role == "user" else "user"

        if not messagebox.askyesno("Xác nhận",
                                 f"Thay đổi vai trò của {username} từ {current_role} thành {new_role}?"):
            return

        users[username]['role'] = new_role
        self.save_users(users)
        messagebox.showinfo("Thành công", "Đã thay đổi vai trò thành công")
        self.load_users_to_tree()

    def request_event_from_web(self):
        """Hiển thị danh sách sự kiện từ API để người dùng chọn và gửi yêu cầu"""
        try:
            url = "https://thongthai.work/simple_api/2001230374"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            imported_events = []
            for i, item in enumerate(data):
                event_date = (datetime.now() + timedelta(days=i+1)).strftime("%d/%m/%Y")
                event_data = {
                    "name": item.get('name', 'Sự Kiện Không Tên'),
                    "date": event_date,
                    "location": f"Địa điểm {i+1}",
                    "description": item.get('description', 'Không có mô tả'),
                    "capacity": 100,
                    "price": item.get('price', 0) * 1000,
                    "current_participants": 0
                }
                imported_events.append(event_data)

            if not imported_events:
                messagebox.showinfo("Thông báo", "Không tìm thấy sự kiện nào từ API")
                return

            self.show_web_events_for_request(imported_events)

        except requests.exceptions.HTTPError as http_err:
            messagebox.showerror("Lỗi HTTP", f"Lỗi khi gọi API: {str(http_err)}")
            print(f"Lỗi HTTP: {http_err}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Lỗi Kết Nối", "Không thể kết nối đến API. Vui lòng kiểm tra mạng.")
        except requests.exceptions.Timeout:
            messagebox.showerror("Lỗi Timeout", "Yêu cầu API bị timeout. Vui lòng thử lại sau.")
        except requests.exceptions.RequestException as req_err:
            messagebox.showerror("Lỗi Yêu Cầu", f"Lỗi không xác định khi gọi API: {str(req_err)}")
            print(f"Lỗi Yêu Cầu: {req_err}")
        except Exception as e:
            messagebox.showerror("Lỗi Khác", f"Lỗi không xác định: {str(e)}")
            print(f"Lỗi Không Xác Định: {e}")

    def show_web_events_for_request(self, events):
        """Hiển thị sự kiện từ web để người dùng chọn và yêu cầu"""
        import_window = Toplevel(self.root)
        import_window.title("Yêu Cầu Sự Kiện Từ Web")
        import_window.geometry("800x600")
        import_window.configure(bg="#0078D7")

        Label(import_window, text="Yêu Cầu Sự Kiện Từ Web", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        tree = ttk.Treeview(import_window, columns=("ID", "Tên", "Ngày", "Địa điểm", "Mô tả", "Số người", "Giá vé"), show="headings", selectmode="extended")
        tree.heading("ID", text="ID")
        tree.heading("Tên", text="Tên sự kiện")
        tree.heading("Ngày", text="Ngày diễn ra")
        tree.heading("Địa điểm", text="Địa điểm")
        tree.heading("Mô tả", text="Mô tả")
        tree.heading("Số người", text="Số người tối đa")
        tree.heading("Giá vé", text="Giá vé (VND)")
        tree.column("ID", width=50)
        tree.column("Mô tả", width=300)
        tree.column("Số người", width=100)
        tree.column("Giá vé", width=100)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for i, event in enumerate(events, 1):
            tree.insert("", "end", values=(
                f"Temp-{i}",
                event['name'],
                event['date'],
                event['location'],
                event['description'],
                event['capacity'],
                f"{event['price']:,}"
            ))

        buttons_frame = Frame(import_window, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Gửi yêu cầu",
               command=lambda: self.request_selected_web_events(tree, events), bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Đóng", command=import_window.destroy, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def request_selected_web_events(self, tree, imported_events):
        """Gửi yêu cầu cho các sự kiện web đã chọn"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một sự kiện để gửi yêu cầu")
            return

        requests = self.load_requests()
        added_count = 0

        for item in selected_items:
            index = tree.index(item)
            event_data = imported_events[index]

            try:
                datetime.strptime(event_data['date'], "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning("Cảnh báo", f"Sự kiện '{event_data['name']}' có ngày không hợp lệ, bỏ qua.")
                continue

            request_id = str(uuid.uuid4())
            requests.append({
                "id": request_id,
                "name": event_data['name'],
                "date": event_data['date'],
                "location": event_data['location'],
                "capacity": event_data['capacity'],
                "price": event_data['price'],
                "description": event_data['description'],
                "requested_by": self.current_user
            })
            added_count += 1

        if added_count > 0:
            self.save_requests(requests)
            messagebox.showinfo("Thành công", f"Đã gửi yêu cầu cho {added_count} sự kiện")
        else:
            messagebox.showinfo("Thông báo", "Không có yêu cầu nào được gửi do lỗi dữ liệu")
        self.show_events()

    def import_events_from_web(self):
        """Nhập sự kiện từ web (chỉ dành cho admin)"""
        if self.user_role != "admin":
            messagebox.showerror("Lỗi", "Chỉ quản trị viên mới có quyền nhập sự kiện trực tiếp")
            return

        try:
            url = "https://thongthai.work/simple_api/2001230374"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            imported_events = []
            for i, item in enumerate(data):
                event_date = (datetime.now() + timedelta(days=i+1)).strftime("%d/%m/%Y")
                event_data = {
                    "name": item.get('name', 'Sự Kiện Không Tên'),
                    "date": event_date,
                    "location": f"Địa điểm {i+1}",
                    "description": item.get('description', 'Không có mô tả'),
                    "capacity": 100,
                    "price": item.get('price', 0) * 1000,
                    "current_participants": 0
                }
                imported_events.append(event_data)

            if not imported_events:
                messagebox.showinfo("Thông báo", "Không tìm thấy sự kiện nào từ API")
                return

            self.show_imported_events(imported_events)

        except requests.exceptions.HTTPError as http_err:
            messagebox.showerror("Lỗi HTTP", f"Lỗi khi gọi API: {str(http_err)}")
            print(f"Lỗi HTTP: {http_err}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Lỗi Kết Nối", "Không thể kết nối đến API. Vui lòng kiểm tra mạng.")
        except requests.exceptions.Timeout:
            messagebox.showerror("Lỗi Timeout", "Yêu cầu API bị timeout. Vui lòng thử lại sau.")
        except requests.exceptions.RequestException as req_err:
            messagebox.showerror("Lỗi Yêu Cầu", f"Lỗi không xác định khi gọi API: {str(req_err)}")
            print(f"Lỗi Yêu Cầu: {req_err}")
        except Exception as e:
            messagebox.showerror("Lỗi Khác", f"Lỗi không xác định: {str(e)}")
            print(f"Lỗi Không Xác Định: {e}")

    def show_imported_events(self, events):
        """Hiển thị sự kiện đã nhập cho admin chọn và nhập"""
        import_window = Toplevel(self.root)
        import_window.title("Sự Kiện Nhập Từ Web")
        import_window.geometry("800x600")
        import_window.configure(bg="#0078D7")

        Label(import_window, text="Sự Kiện Nhập Từ Web", font=("Arial", 16), bg="#0078D7", fg="#FFFFFF").pack(pady=10)

        tree = ttk.Treeview(import_window, columns=("ID", "Tên", "Ngày", "Địa điểm", "Mô tả", "Số người", "Giá vé"), show="headings", selectmode="extended")
        tree.heading("ID", text="ID")
        tree.heading("Tên", text="Tên sự kiện")
        tree.heading("Ngày", text="Ngày diễn ra")
        tree.heading("Địa điểm", text="Địa điểm")
        tree.heading("Mô tả", text="Mô tả")
        tree.heading("Số người", text="Số người tối đa")
        tree.heading("Giá vé", text="Giá vé (VND)")
        tree.column("ID", width=50)
        tree.column("Mô tả", width=300)
        tree.column("Số người", width=100)
        tree.column("Giá vé", width=100)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for i, event in enumerate(events, 1):
            tree.insert("", "end", values=(
                f"Temp-{i}",
                event['name'],
                event['date'],
                event['location'],
                event['description'],
                event['capacity'],
                f"{event['price']:,}"
            ))

        buttons_frame = Frame(import_window, bg="#0078D7")
        buttons_frame.pack(pady=10)

        Button(buttons_frame, text="Nhập sự kiện đã chọn",
               command=lambda: self.import_selected_events(tree, events), bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Đóng", command=import_window.destroy, bg="#FFFFFF", fg="#0078D7").pack(side=LEFT, padx=5)

    def import_selected_events(self, tree, imported_events):
        """Nhập các sự kiện đã chọn từ web (chỉ dành cho admin)"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một sự kiện để nhập")
            return

        events = self.load_events()
        new_id = max([int(e['id']) for e in events] or [0]) + 1
        initial_new_id = new_id

        for item in selected_items:
            index = tree.index(item)
            event_data = imported_events[index]

            try:
                datetime.strptime(event_data['date'], "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning("Cảnh báo", f"Sự kiện '{event_data['name']}' có ngày không hợp lệ, bỏ qua.")
                continue

            events.append({
                "id": str(new_id),
                "name": event_data['name'],
                "date": event_data['date'],
                "location": event_data['location'],
                "capacity": event_data['capacity'],
                "price": event_data['price'],
                "current_participants": 0,
                "description": event_data['description'],
                "created_by": self.current_user
            })
            new_id += 1

        if new_id > initial_new_id:
            self.save_events(events)
            messagebox.showinfo("Thành công", f"Đã nhập {new_id - initial_new_id} sự kiện thành công")
        else:
            messagebox.showinfo("Thông báo", "Không có sự kiện nào được nhập do lỗi dữ liệu")
        self.show_events()

    def accept_event_requests(self):
        """Chấp nhận các yêu cầu sự kiện đã chọn (chỉ dành cho admin)"""
        if self.user_role != "admin":
            messagebox.showerror("Lỗi", "Chỉ quản trị viên mới có quyền xử lý yêu cầu")
            return

        selected_items = self.requests_tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một yêu cầu để chấp nhận")
            return

        requests = self.load_requests()
        events = self.load_events()
        new_id = max([int(e['id']) for e in events] or [0]) + 1
        accepted_count = 0

        for item in selected_items:
            request_id = self.requests_tree.item(item)['values'][0]
            request = next((r for r in requests if r['id'] == request_id), None)

            if not request:
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy yêu cầu với ID {request_id}")
                continue

            try:
                datetime.strptime(request['date'], "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning("Cảnh báo", f"Yêu cầu '{request['name']}' có ngày không hợp lệ, bỏ qua.")
                continue

            events.append({
                "id": str(new_id),
                "name": request['name'],
                "date": request['date'],
                "location": request['location'],
                "capacity": request['capacity'],
                "price": request['price'],
                "current_participants": 0,
                "description": request['description'],
                "created_by": request['requested_by']
            })
            requests = [r for r in requests if r['id'] != request_id]
            new_id += 1
            accepted_count += 1

        if accepted_count > 0:
            self.save_events(events)
            self.save_requests(requests)
            messagebox.showinfo("Thành công", f"Đã chấp nhận {accepted_count} yêu cầu sự kiện")
        else:
            messagebox.showinfo("Thông báo", "Không có yêu cầu nào được chấp nhận do lỗi dữ liệu")
        self.load_requests_to_tree()

    def reject_event_requests(self):
        """Từ chối các yêu cầu sự kiện đã chọn (chỉ dành cho admin)"""
        if self.user_role != "admin":
            messagebox.showerror("Lỗi", "Chỉ quản trị viên mới có quyền xử lý yêu cầu")
            return

        selected_items = self.requests_tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một yêu cầu để từ chối")
            return

        requests = self.load_requests()
        rejected_count = 0

        for item in selected_items:
            request_id = self.requests_tree.item(item)['values'][0]
            requests = [r for r in requests if r['id'] != request_id]
            rejected_count += 1

        if rejected_count > 0:
            self.save_requests(requests)
            messagebox.showinfo("Thành công", f"Đã từ chối {rejected_count} yêu cầu sự kiện")
        else:
            messagebox.showinfo("Thông báo", "Không có yêu cầu nào được từ chối")
        self.load_requests_to_tree()

    def clear_window(self):
        """Xóa tất cả các widget khỏi cửa sổ"""
        for widget in self.root.winfo_children():
            widget.destroy()
        try:
            self.root.config(menu=Menu(self.root, bg="#0078D7", fg="#FFFFFF"))
        except:
            pass

if __name__ == "__main__":
    root = Tk()
    app = EventManagementApp(root)
    root.mainloop()