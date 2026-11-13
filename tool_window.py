"""只读文件检查窗口，后台线程处理文件，界面线程展示结果。"""
import queue
import threading


def run_window(title, threshold_label, default_threshold, analyze, render):
    import tkinter as tk
    from tkinter import filedialog, ttk
    from tkinter.scrolledtext import ScrolledText

    root = tk.Tk()
    root.title(title)
    root.geometry("860x600")
    root.minsize(650, 420)
    frame = ttk.Frame(root, padding=14)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(5, weight=1)
    path = tk.StringVar()
    threshold = tk.StringVar(value=default_threshold)
    encoding = tk.StringVar(value="utf-8-sig")
    status = tk.StringVar(value="选择本地文件，开始检查。原文件不会被修改。")
    ttk.Label(frame, text="输入文件").grid(row=0, column=0, sticky="w", pady=6)
    ttk.Entry(frame, textvariable=path).grid(row=0, column=1, sticky="ew", padx=8)

    def choose():
        selected = filedialog.askopenfilename(parent=root, title="选择要检查的文件")
        if selected:
            path.set(selected)

    ttk.Button(frame, text="选择文件", command=choose).grid(row=0, column=2)
    ttk.Label(frame, text=threshold_label).grid(row=1, column=0, sticky="w", pady=6)
    ttk.Entry(frame, textvariable=threshold).grid(row=1, column=1, sticky="ew", padx=8)
    ttk.Label(frame, text="文本编码").grid(row=2, column=0, sticky="w", pady=6)
    ttk.Combobox(frame, textvariable=encoding, values=["utf-8-sig", "gb18030", "utf-16"]).grid(
        row=2, column=1, sticky="ew", padx=8)
    ttk.Label(frame, textvariable=status).grid(row=4, column=0, columnspan=3, sticky="w", pady=8)
    output = ScrolledText(frame, wrap="word", font=("Consolas", 11))
    output.grid(row=5, column=0, columnspan=3, sticky="nsew")
    output.configure(state="disabled")
    results = queue.Queue()

    def worker(values):
        try:
            report = analyze(*values)
            results.put((True, render(report)))
        except Exception as error:
            results.put((False, str(error)))

    def poll():
        try:
            ok, text = results.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", text)
        output.configure(state="disabled")
        status.set("检查完成，可选择报告文字复制。" if ok else "检查失败，请检查文件、编码和参数。")
        start.configure(state="normal")

    def begin():
        values = (path.get(), threshold.get(), encoding.get())
        start.configure(state="disabled")
        status.set("正在读取文件……")
        threading.Thread(target=worker, args=(values,), daemon=True).start()
        root.after(100, poll)

    start = ttk.Button(frame, text="开始检查", command=begin)
    start.grid(row=3, column=1, sticky="w", padx=8, pady=8)
    root.mainloop()
