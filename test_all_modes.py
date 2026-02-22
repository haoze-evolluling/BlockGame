"""
测试所有丢包模式
"""
import sys
import os
import time

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from network_control import NetworkController

def test_all_modes():
    print("🧪 测试所有丢包模式\n")
    print("=" * 50)
    
    controller = NetworkController()
    
    # 检查clumsy路径
    print(f"\n📍 Clumsy路径: {controller.clumsy_path}")
    if controller.clumsy_path and os.path.exists(controller.clumsy_path):
        print("✅ 找到clumsy.exe")
    else:
        print("❌ 找不到clumsy.exe")
        return
    
    print("\n" + "=" * 50)
    
    # 测试0% - 正常模式
    print("\n[测试 1/3] 正常模式 (0%)")
    print("-" * 50)
    success, message = controller.set_packet_loss(0)
    print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {message}")
    print(f"当前丢包率: {controller.get_status()['loss_percent']}%")
    time.sleep(2)
    
    # 测试50% - 中等延迟
    print("\n[测试 2/3] 中等延迟 (50%)")
    print("-" * 50)
    success, message = controller.set_packet_loss(50)
    print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {message}")
    print(f"当前丢包率: {controller.get_status()['loss_percent']}%")
    
    if success:
        print("\n⚠️ 注意：现在网络丢包率为50%")
        print("你可以尝试访问网页测试效果")
        input("按回车键继续...")
    
    # 恢复正常
    print("\n[恢复] 恢复正常网络...")
    print("-" * 50)
    success, message = controller.set_packet_loss(0)
    print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {message}")
    print(f"当前丢包率: {controller.get_status()['loss_percent']}%")
    
    # 测试100% - 完全阻断（可选）
    print("\n[测试 3/3] 完全阻断 (100%)")
    print("-" * 50)
    choice = input("⚠️ 警告：这会完全断网！是否测试？(y/N): ").strip().lower()
    
    if choice == 'y':
        print("\n正在断网...")
        success, message = controller.set_packet_loss(100)
        print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
        print(f"消息: {message}")
        print(f"当前丢包率: {controller.get_status()['loss_percent']}%")
        
        if success:
            print("\n⚠️ 网络已完全断开")
            input("按回车键恢复网络...")
            
            print("\n恢复网络...")
            success, message = controller.set_packet_loss(0)
            print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
            print(f"消息: {message}")
    else:
        print("已跳过100%测试")
    
    # 清理
    print("\n" + "=" * 50)
    print("\n🧹 清理资源...")
    controller.cleanup()
    
    print("\n✨ 所有测试完成！")
    print("\n总结:")
    print("  ✅ 0% 丢包 - 正常模式")
    print("  ✅ 50% 丢包 - 使用clumsy")
    print("  ✅ 100% 丢包 - 禁用网络适配器")

if __name__ == '__main__':
    try:
        test_all_modes()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
        print("正在清理...")
        controller = NetworkController()
        controller.cleanup()
        controller.set_packet_loss(0)
        print("✅ 已恢复正常")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
