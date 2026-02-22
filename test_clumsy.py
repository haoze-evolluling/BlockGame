"""
测试clumsy集成
"""
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from network_control import NetworkController

def test_clumsy():
    print("🧪 测试clumsy集成\n")
    
    controller = NetworkController()
    
    # 检查clumsy路径
    print(f"Clumsy路径: {controller.clumsy_path}")
    if controller.clumsy_path and os.path.exists(controller.clumsy_path):
        print("✅ 找到clumsy.exe\n")
    else:
        print("❌ 找不到clumsy.exe")
        print("请确保clumsy.exe在项目根目录\n")
        return
    
    # 测试50%丢包
    print("测试设置50%丢包...")
    success, message = controller.set_packet_loss(50)
    print(f"结果: {message}")
    
    if success:
        print("✅ 成功启动clumsy")
        print("\n⚠️ 注意：现在网络丢包率为50%")
        input("\n按回车键恢复正常...")
        
        # 恢复正常
        print("\n恢复正常网络...")
        success, message = controller.set_packet_loss(0)
        print(f"结果: {message}")
        
        if success:
            print("✅ 已恢复正常")
    else:
        print("❌ 启动失败")
    
    # 清理
    controller.cleanup()
    print("\n✨ 测试完成")

if __name__ == '__main__':
    try:
        test_clumsy()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
