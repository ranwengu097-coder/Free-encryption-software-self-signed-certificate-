import sys
import os
import json
import base64
import hashlib
import random
import math
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# ========== 加密核心 ==========
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".secure_chat")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_EXT = ".enc"


def init_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"password_hash": "", "use_password": False}, f)


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode()


def b64_decode(token: str) -> bytes:
    return base64.b64decode(token.encode())


def encrypt_text(text: str) -> str:
    if not text:
        return ""
    return b64_encode(text.encode("utf-8"))


def decrypt_text(token: str) -> str:
    if not token:
        return ""
    try:
        return b64_decode(token).decode("utf-8")
    except Exception:
        raise ValueError("解密失败，密文格式无效")


def encrypt_file_content(data: bytes) -> str:
    if not data:
        return ""
    return b64_encode(data)


def decrypt_file_content(token: str) -> bytes:
    if not token:
        return b""
    return b64_decode(token)


# ========== 动画粒子 ==========
class Particle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-0.8, -0.2)
        self.life = random.uniform(2.0, 5.0)
        self.max_life = self.life
        self.size = random.uniform(1.5, 3.5)
        r = random.randint(0, 1)
        self.color = "#00e5ff" if r == 0 else "#76ff03"

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.03
        if self.x < 0:
            self.x = self.w
        elif self.x > self.w:
            self.x = 0

    @property
    def alive(self):
        return self.life > 0

    @property
    def alpha_hex(self):
        a = int(255 * (self.life / self.max_life))
        return f"{a:02x}"


class AnimatedCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.particles = []
        self.grid_offset = 0
        self.t = 0  # animation frame counter
        self.bind("<Configure>", self.on_resize)
        self._job = None
        self.start_animation()

    def on_resize(self, event):
        self.configure(width=event.width, height=event.height)

    def start_animation(self):
        self._animate()

    def _animate(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            self._job = self.after(50, self._animate)
            return

        self.t += 1
        self.delete("all")

        # --- 渐变背景 ---
        steps = 40
        for i in range(steps):
            ratio = i / steps
            r = int(10 + 15 * math.sin(ratio * math.pi + self.t * 0.02))
            g = int(10 + 15 * math.sin(ratio * math.pi + 2.0 + self.t * 0.025))
            b = int(30 + 25 * math.sin(ratio * math.pi + 4.0 + self.t * 0.018))
            color = f"#{r:02x}{g:02x}{b:02x}"
            y0 = int(i * h / steps)
            y1 = int((i + 1) * h / steps) + 1
            self.create_rectangle(0, y0, w, y1, fill=color, outline="")

        # --- 网格线 ---
        self.grid_offset = (self.grid_offset + 1) % 30
        gx = self.grid_offset
        while gx < w:
            self.create_line(gx, 0, gx, h, fill="#1a3a5c", width=1)
            gx += 30
        gy = self.grid_offset
        while gy < h:
            self.create_line(0, gy, w, gy, fill="#1a3a5c", width=1)
            gy += 30

        # --- 粒子 ---
        if len(self.particles) < 80 and random.random() < 0.4:
            self.particles.append(Particle(random.randint(0, w), random.randint(0, h), w, h))

        alive = []
        for p in self.particles:
            p.update()
            if p.alive:
                c = p.color + p.alpha_hex
                self.create_oval(
                    p.x - p.size, p.y - p.size,
                    p.x + p.size, p.y + p.size,
                    fill=c, outline=""
                )
                alive.append(p)
        self.particles = alive

        self._job = self.after(35, self._animate)


# ========== GUI ==========
class SecureChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("对话加密工具 - Secure Chat v2.0")
        self.root.geometry("780x680")
        self.root.minsize(600, 500)
        self.root.configure(bg="#0a1628")

        # 全局状态
        self.auto_encrypt = tk.BooleanVar(value=True)
        self.file_extension = tk.StringVar(value=".enc")
        self.current_encrypted_path = None

        init_config()
        self.build_background()
        self.build_ui()

    def build_background(self):
        self.bg_canvas = AnimatedCanvas(self.root)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def build_ui(self):
        # 标题栏
        title_frame = tk.Frame(self.bg_canvas, bg="#0d2137", bd=0)
        title_frame.pack(fill=tk.X)
        tk.Label(
            title_frame,
            text="Secure Chat v2.0 — 对话 & 文件加密工具",
            bg="#0d2137",
            fg="#00e5ff",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=10)

        # Notebook 选项卡
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#0a1628", borderwidth=0)
        style.configure("TNotebook.Tab", background="#0d2137", foreground="#8899aa",
                        padding=[20, 6], font=("微软雅黑", 11))
        style.map("TNotebook.Tab", background=[("selected", "#0f3460")],
                  foreground=[("selected", "#00e5ff")])

        self.notebook = ttk.Notebook(self.bg_canvas)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))

        # Tab 1: 文本加解密
        self.text_tab = tk.Frame(self.notebook, bg="#0a1628")
        self.notebook.add(self.text_tab, text="  文本加解密  ")
        self.build_text_tab(self.text_tab)

        # Tab 2: 文件加解密
        self.file_tab = tk.Frame(self.notebook, bg="#0a1628")
        self.notebook.add(self.file_tab, text="  文件加解密  ")
        self.build_file_tab(self.file_tab)

    # ==================== 文本加解密 Tab ====================
    def build_text_tab(self, parent):
        # 控件栏
        ctrl_frame = tk.Frame(parent, bg="#0a1628", bd=0)
        ctrl_frame.pack(fill=tk.X, pady=(10, 4))

        self.auto_cb = tk.Checkbutton(
            ctrl_frame, text="自动加密", variable=self.auto_encrypt,
            bg="#0a1628", fg="#b0c4de", selectcolor="#0d2137",
            activebackground="#0a1628", activeforeground="#00e5ff",
            font=("微软雅黑", 10), command=self.on_auto_toggle
        )
        self.auto_cb.pack(side=tk.LEFT, padx=10)
        tk.Button(
            ctrl_frame, text="手动加密", command=self.manual_encrypt_text,
            width=10, bg="#0f3460", fg="#ccddee", bd=0, font=("微软雅黑", 10),
            activebackground="#1a5276", activeforeground="#ffffff"
        ).pack(side=tk.LEFT, padx=4)

        self.text_status = tk.Label(ctrl_frame, text="● 就绪", bg="#0a1628", fg="#76ff03", font=("微软雅黑", 10))
        self.text_status.pack(side=tk.RIGHT, padx=10)

        # 输入区
        in_frame = tk.LabelFrame(parent, text=" 明文输入 ", bg="#0a1628", fg="#88aacc",
                                  font=("微软雅黑", 10, "bold"), bd=1, relief=tk.GROOVE)
        in_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 3))
        self.input_text = scrolledtext.ScrolledText(
            in_frame, wrap=tk.WORD, font=("微软雅黑", 11),
            bg="#0d2137", fg="#d0e0f0", insertbackground="#00e5ff",
            relief=tk.FLAT, bd=4, height=8
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.input_text.bind("<KeyRelease>", self.on_text_input)

        # 输出区
        out_frame = tk.LabelFrame(parent, text=" 密文输出 (Base64) ", bg="#0a1628", fg="#88aacc",
                                   font=("微软雅黑", 10, "bold"), bd=1, relief=tk.GROOVE)
        out_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)
        self.output_text = scrolledtext.ScrolledText(
            out_frame, wrap=tk.WORD, font=("Consolas", 11),
            bg="#0d2137", fg="#76ff03", insertbackground="#00e5ff",
            relief=tk.FLAT, bd=4, height=7
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 解密区
        dec_frame = tk.LabelFrame(parent, text=" 密文解密 ", bg="#0a1628", fg="#88aacc",
                                   font=("微软雅黑", 10, "bold"), bd=1, relief=tk.GROOVE)
        dec_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)
        self.decrypt_input = scrolledtext.ScrolledText(
            dec_frame, wrap=tk.WORD, font=("Consolas", 11),
            bg="#0d2137", fg="#ffeb3b", insertbackground="#00e5ff",
            relief=tk.FLAT, bd=4, height=4
        )
        self.decrypt_input.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 按钮栏
        btn_frame = tk.Frame(parent, bg="#0a1628", bd=0)
        btn_frame.pack(fill=tk.X, padx=10, pady=(4, 8))
        btn_style = {"bg": "#0f3460", "fg": "#ccddee", "bd": 0, "font": ("微软雅黑", 9),
                     "activebackground": "#1a5276", "activeforeground": "#ffffff"}
        tk.Button(btn_frame, text="解密文本", command=self.decrypt_text_action, width=10, **btn_style
                  ).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="复制密文", command=self.copy_encrypted, width=10, **btn_style
                  ).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="导出密文", command=self.export_encrypted, width=10, **btn_style
                  ).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="导入解密", command=self.import_and_decrypt, width=10, **btn_style
                  ).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="清空", command=self.clear_text, width=6, **btn_style
                  ).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="关于", command=self.show_about, width=6, **btn_style
                  ).pack(side=tk.RIGHT, padx=3)

    def on_text_input(self, event=None):
        if self.auto_encrypt.get():
            self.encrypt_text_now()

    def on_auto_toggle(self):
        if self.auto_encrypt.get():
            self.encrypt_text_now()

    def manual_encrypt_text(self):
        self.encrypt_text_now()

    def encrypt_text_now(self):
        text = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text:
            self.output_text.delete("1.0", tk.END)
            return
        try:
            enc = encrypt_text(text)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", enc)
            self.text_status.config(text="● 已加密 (Base64)", fg="#76ff03")
        except Exception as e:
            self.text_status.config(text=f"✖ 加密失败: {e}", fg="#ff4444")

    def decrypt_text_action(self):
        token = self.decrypt_input.get("1.0", tk.END).rstrip("\n")
        if not token:
            messagebox.showwarning("提示", "请先粘贴密文到解密区")
            return
        try:
            plain = decrypt_text(token)
            self.decrypt_input.delete("1.0", tk.END)
            self.decrypt_input.insert("1.0", plain)
            self.text_status.config(text="● 解密成功", fg="#76ff03")
            messagebox.showinfo("解密结果", f"明文:\n\n{plain}")
        except Exception:
            self.text_status.config(text="✖ 解密失败，密文格式无效", fg="#ff4444")
            messagebox.showerror("解密失败", "密文不是有效的 Base64 格式，请检查是否完整复制。")

    def copy_encrypted(self):
        enc = self.output_text.get("1.0", tk.END).strip()
        if enc:
            self.root.clipboard_clear()
            self.root.clipboard_append(enc)
            self.text_status.config(text="● 密文已复制到剪贴板", fg="#76ff03")

    def export_encrypted(self):
        enc = self.output_text.get("1.0", tk.END).strip()
        if not enc:
            messagebox.showwarning("提示", "没有可导出的密文")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".enc",
            filetypes=[("加密文件", "*.enc"), ("文本", "*.txt")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ciphertext": enc, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False)
            self.text_status.config(text=f"● 已导出: {os.path.basename(path)}", fg="#76ff03")

    def import_and_decrypt(self):
        path = filedialog.askopenfilename(
            filetypes=[("加密文件", "*.enc"), ("文本", "*.txt"), ("全部", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            token = data.get("ciphertext", "")
            if not token:
                raise ValueError("无效密文")
            plain = decrypt_text(token)
            self.decrypt_input.delete("1.0", tk.END)
            self.decrypt_input.insert("1.0", token)
            self.text_status.config(text="● 导入成功", fg="#76ff03")
            messagebox.showinfo("解密结果", f"来源: {os.path.basename(path)}\n\n{plain}")
        except Exception as e:
            self.text_status.config(text=f"✖ 导入失败: {e}", fg="#ff4444")
            messagebox.showerror("导入失败", str(e))

    def clear_text(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.decrypt_input.delete("1.0", tk.END)
        self.text_status.config(text="● 已清空", fg="#76ff03")

    def show_about(self):
        about = (
            "对话加密工具 v2.0\n\n"
            "两大核心功能:\n"
            "1. 文本加解密 — Base64 编解码\n"
            "2. 文件加解密 — 任意文件 Base64 转码\n\n"
            "注意: Base64 是一种编码方式，\n"
            "不是密码学加密，任何人都可以解码。\n"
            "如需强加密请配合其他工具使用。\n\n"
            "纯标准库实现，无需安装额外依赖。"
        )
        messagebox.showinfo("关于", about)

    # ==================== 文件加解密 Tab ====================
    def build_file_tab(self, parent):
        # ---- 加密区域 ----
        enc_section = tk.LabelFrame(parent, text=" 文件加密 ", bg="#0a1628", fg="#00e5ff",
                                     font=("微软雅黑", 11, "bold"), bd=1, relief=tk.GROOVE)
        enc_section.pack(fill=tk.X, padx=10, pady=(10, 4))

        btn_style = {"bg": "#0f3460", "fg": "#ccddee", "bd": 0, "font": ("微软雅黑", 10),
                     "activebackground": "#1a5276", "activeforeground": "#ffffff"}

        row0 = tk.Frame(enc_section, bg="#0a1628")
        row0.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(row0, text="源文件:", bg="#0a1628", fg="#88aacc", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.enc_source_label = tk.Label(row0, text="未选择", bg="#0d2137", fg="#8899aa",
                                           font=("微软雅黑", 9), anchor=tk.W, width=50)
        self.enc_source_label.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        tk.Button(row0, text="选择文件", command=self.select_encrypt_file, width=9, **btn_style
                  ).pack(side=tk.LEFT, padx=4)

        row1 = tk.Frame(enc_section, bg="#0a1628")
        row1.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(row1, text="加密后缀:", bg="#0a1628", fg="#88aacc", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.ext_entry = tk.Entry(
            row1, textvariable=self.file_extension, width=10,
            bg="#0d2137", fg="#00e5ff", insertbackground="#00e5ff",
            font=("Consolas", 11), relief=tk.FLAT, bd=4
        )
        self.ext_entry.pack(side=tk.LEFT, padx=6)
        tk.Label(row1, text="(默认 .enc，可改为 .locked 等)", bg="#0a1628", fg="#556677",
                 font=("微软雅黑", 8)).pack(side=tk.LEFT)

        row2 = tk.Frame(enc_section, bg="#0a1628")
        row2.pack(fill=tk.X, padx=10, pady=(4, 10))
        tk.Button(row2, text="加密文件", command=self.encrypt_file_action, width=14, **btn_style
                  ).pack(side=tk.LEFT, padx=4)
        self.enc_status = tk.Label(row2, text="", bg="#0a1628", fg="#76ff03", font=("微软雅黑", 9))
        self.enc_status.pack(side=tk.LEFT, padx=10)

        # ---- 解密区域 ----
        dec_section = tk.LabelFrame(parent, text=" 文件解密 ", bg="#0a1628", fg="#76ff03",
                                     font=("微软雅黑", 11, "bold"), bd=1, relief=tk.GROOVE)
        dec_section.pack(fill=tk.X, padx=10, pady=(4, 10))

        row3 = tk.Frame(dec_section, bg="#0a1628")
        row3.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(row3, text="加密文件:", bg="#0a1628", fg="#88aacc", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.dec_source_label = tk.Label(row3, text="未选择", bg="#0d2137", fg="#8899aa",
                                           font=("微软雅黑", 9), anchor=tk.W, width=50)
        self.dec_source_label.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        tk.Button(row3, text="选择文件", command=self.select_decrypt_file, width=9, **btn_style
                  ).pack(side=tk.LEFT, padx=4)

        row4 = tk.Frame(dec_section, bg="#0a1628")
        row4.pack(fill=tk.X, padx=10, pady=(4, 10))
        tk.Button(row4, text="解密文件", command=self.decrypt_file_action, width=14, **btn_style
                  ).pack(side=tk.LEFT, padx=4)
        self.dec_status = tk.Label(row4, text="", bg="#0a1628", fg="#76ff03", font=("微软雅黑", 9))
        self.dec_status.pack(side=tk.LEFT, padx=10)

        # 日志区
        log_frame = tk.LabelFrame(parent, text=" 操作日志 ", bg="#0a1628", fg="#88aacc",
                                   font=("微软雅黑", 10, "bold"), bd=1, relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0d2137", fg="#b0c4de", insertbackground="#00e5ff",
            relief=tk.FLAT, bd=4, height=10, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def log(self, msg):
        self.log_text.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def select_encrypt_file(self):
        path = filedialog.askopenfilename(title="选择要加密的文件")
        if path:
            self.enc_source_path = path
            self.enc_source_label.config(text=os.path.basename(path))
            self.log(f"已选择源文件: {path}")

    def select_decrypt_file(self):
        path = filedialog.askopenfilename(title="选择要解密的加密文件")
        if path:
            self.dec_source_path = path
            self.dec_source_label.config(text=os.path.basename(path))
            self.log(f"已选择加密文件: {path}")

    def encrypt_file_action(self):
        if not hasattr(self, "enc_source_path"):
            messagebox.showwarning("提示", "请先选择要加密的文件")
            return
        src = self.enc_source_path
        ext = self.file_extension.get().strip()
        if not ext.startswith("."):
            ext = "." + ext
        if ext == ".":
            ext = DEFAULT_EXT

        try:
            with open(src, "rb") as f:
                data = f.read()
            encoded = encrypt_file_content(data)
            dst = src + ext
            with open(dst, "w", encoding="utf-8") as f:
                f.write(encoded)
            size_kb = len(data) / 1024
            self.enc_status.config(
                text=f"加密成功! → {os.path.basename(dst)} ({size_kb:.1f} KB)",
                fg="#76ff03"
            )
            self.log(f"加密完成: {src} → {dst}  ({size_kb:.1f} KB, 后缀: {ext})")
        except Exception as e:
            self.enc_status.config(text=f"加密失败: {e}", fg="#ff4444")
            self.log(f"加密失败: {e}")

    def decrypt_file_action(self):
        if not hasattr(self, "dec_source_path"):
            messagebox.showwarning("提示", "请先选择要解密的加密文件")
            return
        src = self.dec_source_path

        try:
            with open(src, "r", encoding="utf-8") as f:
                encoded = f.read()
            decoded = decrypt_file_content(encoded)

            # 去掉加密时加的后缀
            base_name = os.path.basename(src)
            # 尝试找到原始文件名：如果文件名里有原始扩展名线索...
            # 简单策略：让用户选择保存位置
            dst = filedialog.asksaveasfilename(
                title="解密文件另存为",
                defaultextension="",
                initialfile=base_name.replace(".enc", "").replace(".locked", ""),
            )
            if not dst:
                self.log("解密取消（未选择保存位置）")
                return

            with open(dst, "wb") as f:
                f.write(decoded)
            size_kb = len(decoded) / 1024
            self.dec_status.config(
                text=f"解密成功! → {os.path.basename(dst)} ({size_kb:.1f} KB)",
                fg="#76ff03"
            )
            self.log(f"解密完成: {src} → {dst}  ({size_kb:.1f} KB)")
        except Exception as e:
            self.dec_status.config(text=f"解密失败: {e}", fg="#ff4444")
            self.log(f"解密失败: {e}")


def main():
    root = tk.Tk()
    root.iconbitmap(default="")
    app = SecureChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
