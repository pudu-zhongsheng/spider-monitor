"""
本地定时调度器
用于在本地环境定时执行空投监控程序
"""
import sys
import time
import threading
from datetime import datetime

try:
    import schedule
except ImportError:
    print("❌ 未安装 schedule 库")
    print("请运行: pip install schedule")
    sys.exit(1)

# 导入主程序的函数
import importlib.util
import sys

# 动态导入 spider-project.py 模块
spec = importlib.util.spec_from_file_location("spider_project", "spider-project.py")
spider_project = importlib.util.module_from_spec(spec)
sys.modules["spider_project"] = spider_project
spec.loader.exec_module(spider_project)

class LocalScheduler:
    """本地定时执行调度器"""
    
    def __init__(self, interval_minutes=2):
        """
        初始化调度器
        
        Args:
            interval_minutes: 检查间隔（分钟），默认2分钟
        """
        self.interval_minutes = interval_minutes
        self.running = False
        self.scheduler_thread = None
        
    def job(self):
        """定时任务执行的函数"""
        print("\n" + "=" * 60)
        print(f"⏰ 定时任务触发 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        spider_project.check_changes_once()
        print("=" * 60 + "\n")
    
    def start(self):
        """启动定时调度器"""
        if spider_project.is_github_actions():
            print("⚠️ 当前在GitHub Actions环境，不支持本地调度器")
            return False
        
        if self.running:
            print("⚠️ 调度器已经在运行中")
            return False
        
        print(f"🚀 启动本地定时调度器")
        print(f"⏱️  检查间隔: 每 {self.interval_minutes} 分钟")
        print(f"🕐 下次执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💡 按 Ctrl+C 停止调度器")
        print("=" * 60)
        
        # 立即执行一次
        self.job()
        
        # 设置定时任务
        schedule.every(self.interval_minutes).minutes.do(self.job)
        
        self.running = True
        
        # 在后台线程中运行调度器
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        return True
    
    def stop(self):
        """停止定时调度器"""
        if not self.running:
            print("⚠️ 调度器未在运行")
            return False
        
        self.running = False
        schedule.clear()
        print("🛑 调度器已停止")
        return True
    
    def run_forever(self):
        """运行调度器直到手动停止"""
        if not self.start():
            return
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 收到停止信号...")
            self.stop()
            print("✅ 调度器已安全停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='空投监控本地定时调度器')
    parser.add_argument(
        '--interval', 
        type=int, 
        default=30, 
        help='检查间隔（分钟），默认30分钟'
    )
    
    args = parser.parse_args()
    
    if args.interval < 1:
        print("❌ 间隔时间必须大于0分钟")
        return
    
    print("🚀 空投数据变化监控系统 - 本地定时模式")
    print("=" * 50)
    
    scheduler = LocalScheduler(interval_minutes=args.interval)
    scheduler.run_forever()


if __name__ == "__main__":
    main()

