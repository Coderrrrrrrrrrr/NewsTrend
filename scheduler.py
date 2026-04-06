import time
import subprocess
import sys
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

# Path to the python executable
PYTHON_PATH = r"D:anaconda\anaconda\python.exe"
MAIN_SCRIPT = "main.py"

def run_job():
    print(f"\n[{datetime.now()}] >>> 尚书省启动：开始定时情报抓取与决策分析...")
    process = None
    try:
        # We use subprocess.Popen to stream output in real-time
        process = subprocess.Popen(
            [PYTHON_PATH, MAIN_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

        process.wait()
        if process.returncode == 0:
            print(f"[{datetime.now()}] <<< 任务圆满完成。")
        else:
            print(f"[{datetime.now()}] !!! 任务异常终止，返回码: {process.returncode}")
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] !!! 用户中断，正在停止子进程...")
        if process and process.poll() is None:  # 如果进程还在运行
            process.terminate()  # 发送终止信号
            try:
                process.wait(timeout=5)  # 等待最多5秒
            except subprocess.TimeoutExpired:
                process.kill()  # 强制终止
                process.wait()
        print(f"[{datetime.now()}] <<< 子进程已停止。")
        raise  # 重新抛出异常，让调度器也能退出
    except Exception as e:
        print(f"[{datetime.now()}] !!! 调度器发生致命错误: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # Run once at start
    run_job()
    
    # Then run every hour (can be adjusted via env var)
    interval_minutes = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 60))
    print(f"[*] 调度系统已就绪。执行周期：每 {interval_minutes} 分钟一次。按 Ctrl+C 停止。")
    
    scheduler.add_job(run_job, 'interval', minutes=interval_minutes)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] 调度系统正在安全关闭...")
        scheduler.shutdown(wait=False)  # 立即关闭调度器，不等待任务完成
        print("[*] 调度系统已退出。")
