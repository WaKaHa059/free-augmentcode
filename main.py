import os
import shutil
import uuid
import argparse
import platform
import json
import logging
from datetime import datetime

class AugmentEnvManager:
    def __init__(self, verbose=False):
        """初始化AugmentCode环境管理器"""
        self.verbose = verbose
        self.system = platform.system()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO if verbose else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AugmentCodeManager')
        
        # 根据系统设置路径
        if self.system == "Darwin":  # macOS
            self.extension_path = os.path.expanduser("~/.vscode/extensions/augment.vscode-augment-0.509.1")
            self.config_path = os.path.expanduser("~/Library/Application Support/Code/User/globalStorage/augment.vscode-augment")
            self.workspace_storage = os.path.expanduser("~/Library/Application Support/Code/User/workspaceStorage")
        elif self.system == "Windows":
            self.extension_path = os.path.expanduser("~\\.vscode\\extensions\\augment.vscode-augment-0.509.1")
            self.config_path = os.path.expanduser("~\\AppData\\Roaming\\Code\\User\\globalStorage\\augment.vscode-augment")
            self.workspace_storage = os.path.expanduser("~\\AppData\\Roaming\\Code\\User\\workspaceStorage")
        else:  # Linux
            self.extension_path = os.path.expanduser("~/.vscode/extensions/augment.vscode-augment-0.509.1")
            self.config_path = os.path.expanduser("~/.config/Code/User/globalStorage/augment.vscode-augment")
            self.workspace_storage = os.path.expanduser("~/.config/Code/User/workspaceStorage")
        
        # 关键文件和目录
        self.device_id_file = os.path.join(self.config_path, "deviceId.json")
        self.auth_file = os.path.join(self.config_path, "auth.json")
        self.history_dir = os.path.join(self.config_path, "history")
        self.cache_dir = os.path.join(self.config_path, "cache")
        self.workspace_configs = os.path.join(self.workspace_storage, "*", "Augment.vscode-augment")
        
        self.logger.info(f"AugmentCode管理器已初始化，系统: {self.system}")
        
    def backup_env(self):
        """备份当前环境配置"""
        if not os.path.exists(self.config_path):
            self.logger.warning("未找到AugmentCode配置目录，可能未安装或路径不正确")
            return None
            
        backup_path = os.path.join(
            os.path.expanduser("~"), 
            "augmentcode_backups", 
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        try:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copytree(self.config_path, backup_path)
            self.logger.info(f"环境已备份至: {backup_path}")
            print(f"✅ 环境已备份至: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"备份失败: {e}")
            print(f"⚠️ 备份失败: {e}")
            return None
    
    def reset_env(self, reset_all=True, reset_device_id=True, reset_auth=True, reset_history=True, reset_cache=True):
        """重置AugmentCode环境
        
        Args:
            reset_all: 是否重置所有组件
            reset_device_id: 是否重置设备ID
            reset_auth: 是否重置认证状态
            reset_history: 是否重置历史记录
            reset_cache: 是否重置缓存
        """
        print("🚀 开始重置AugmentCode环境...")
        
        # 先备份当前环境
        backup_path = self.backup_env()
        
        # 检查配置目录是否存在
        if not os.path.exists(self.config_path):
            self.logger.warning("未找到AugmentCode配置目录，可能未安装或路径不正确")
            print("⚠️ 未找到AugmentCode配置目录，可能未安装或路径不正确")
            return False
        
        # 重置设备ID
        if reset_all or reset_device_id:
            if os.path.exists(self.device_id_file):
                os.remove(self.device_id_file)
                self.logger.info("已重置设备ID")
                print("✅ 已重置设备ID")
            else:
                self.logger.info("设备ID文件不存在，跳过")
        
        # 重置认证状态
        if reset_all or reset_auth:
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
                self.logger.info("已重置认证状态")
                print("✅ 已重置认证状态")
            else:
                self.logger.info("认证文件不存在，跳过")
        
        # 清理历史记录
        if reset_all or reset_history:
            if os.path.exists(self.history_dir):
                shutil.rmtree(self.history_dir)
                os.makedirs(self.history_dir, exist_ok=True)
                self.logger.info("已清理历史记录")
                print("✅ 已清理历史记录")
            else:
                self.logger.info("历史记录目录不存在，跳过")
        
        # 清理缓存
        if reset_all or reset_cache:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info("已清理缓存")
                print("✅ 已清理缓存")
            else:
                self.logger.info("缓存目录不存在，跳过")
        
        # 清理工作区特定配置
        if reset_all:
            for workspace_config in self._find_workspace_configs():
                try:
                    shutil.rmtree(workspace_config)
                    self.logger.info(f"已清理工作区配置: {workspace_config}")
                    print(f"✅ 已清理工作区配置: {os.path.basename(os.path.dirname(workspace_config))}")
                except Exception as e:
                    self.logger.error(f"清理工作区配置失败: {e}")
        
        print("🎉 环境重置完成！请重启VS Code并重新登录AugmentCode。")
        return True
    
    def _find_workspace_configs(self):
        """查找所有工作区特定的AugmentCode配置"""
        import glob
        return glob.glob(self.workspace_configs)
    
    def create_workspace(self, name):
        """创建新的工作空间
        
        Args:
            name: 工作空间名称
        """
        workspace_dir = os.path.join(self.config_path, "workspaces", name)
        
        if os.path.exists(workspace_dir):
            self.logger.error(f"工作空间 '{name}' 已存在")
            print(f"❌ 工作空间 '{name}' 已存在")
            return False
        
        try:
            os.makedirs(workspace_dir, exist_ok=True)
            
            # 创建工作区配置
            config = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "device_id": str(uuid.uuid4()),
                "description": f"AugmentCode工作区: {name}"
            }
            
            config_path = os.path.join(workspace_dir, "workspace_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"创建工作空间 '{name}' 成功")
            print(f"✅ 工作空间 '{name}' 创建成功")
            return True
        except Exception as e:
            self.logger.error(f"创建工作空间失败: {e}")
            print(f"❌ 创建工作空间失败: {e}")
            return False
    
    def switch_workspace(self, name):
        """切换到指定工作空间
        
        Args:
            name: 工作空间名称
        """
        workspace_dir = os.path.join(self.config_path, "workspaces", name)
        
        if not os.path.exists(workspace_dir):
            self.logger.error(f"工作空间 '{name}' 不存在")
            print(f"❌ 工作空间 '{name}' 不存在")
            return False
        
        try:
            # 备份当前环境
            self.backup_env()
            
            # 加载工作区配置
            config_path = os.path.join(workspace_dir, "workspace_config.json")
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # 应用工作区配置
            self._apply_workspace_config(config)
            
            self.logger.info(f"已切换到工作空间 '{name}'")
            print(f"✅ 已切换到工作空间 '{name}'")
            print("请重启VS Code使更改生效。")
            return True
        except Exception as e:
            self.logger.error(f"切换工作空间失败: {e}")
            print(f"❌ 切换工作空间失败: {e}")
            return False
    
    def _apply_workspace_config(self, config):
        """应用工作区配置
        
        Args:
            config: 工作区配置字典
        """
        # 应用设备ID
        if "device_id" in config:
            os.makedirs(os.path.dirname(self.device_id_file), exist_ok=True)
            with open(self.device_id_file, "w") as f:
                json.dump({"deviceId": config["device_id"]}, f)
        
        # 可以添加其他配置项的应用逻辑
    
    def list_workspaces(self):
        """列出所有工作空间"""
        workspaces_dir = os.path.join(self.config_path, "workspaces")
        
        if not os.path.exists(workspaces_dir):
            print("没有找到工作空间")
            return []
        
        workspaces = []
        for item in os.listdir(workspaces_dir):
            item_path = os.path.join(workspaces_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "workspace_config.json")):
                try:
                    with open(os.path.join(item_path, "workspace_config.json"), "r") as f:
                        config = json.load(f)
                    workspaces.append(config)
                except:
                    pass
        
        if not workspaces:
            print("没有找到工作空间")
            return []
        
        print("可用的工作空间:")
        print("-" * 40)
        for ws in workspaces:
            print(f"名称: {ws['name']}")
            print(f"创建时间: {ws['created_at']}")
            print(f"设备ID: {ws['device_id'][:8]}...")
            print("-" * 40)
        
        return workspaces

def main():
    parser = argparse.ArgumentParser(description="AugmentCode环境管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细日志")
    
    # 备份命令
    backup_parser = subparsers.add_parser("backup", help="备份当前环境")
    
    # 重置命令
    reset_parser = subparsers.add_parser("reset", help="重置环境")
    reset_parser.add_argument("--all", action="store_true", help="重置所有组件（默认）")
    reset_parser.add_argument("--device-id", action="store_true", help="仅重置设备ID")
    reset_parser.add_argument("--auth", action="store_true", help="仅重置认证状态")
    reset_parser.add_argument("--history", action="store_true", help="仅重置历史记录")
    reset_parser.add_argument("--cache", action="store_true", help="仅重置缓存")
    
    # 创建工作空间命令
    create_ws_parser = subparsers.add_parser("create-workspace", help="创建新工作空间")
    create_ws_parser.add_argument("name", help="工作空间名称")
    
    # 切换工作空间命令
    switch_ws_parser = subparsers.add_parser("switch-workspace", help="切换到指定工作空间")
    switch_ws_parser.add_argument("name", help="工作空间名称")
    
    # 列出工作空间命令
    list_ws_parser = subparsers.add_parser("list-workspaces", help="列出所有工作空间")
    
    args = parser.parse_args()
    
    # 初始化管理器
    manager = AugmentEnvManager(verbose=args.verbose)
    
    # 执行命令
    if args.command == "backup":
        manager.backup_env()
    elif args.command == "reset":
        # 确定重置哪些组件
        if args.all or not any([args.device_id, args.auth, args.history, args.cache]):
            manager.reset_env(reset_all=True)
        else:
            manager.reset_env(
                reset_all=False,
                reset_device_id=args.device_id,
                reset_auth=args.auth,
                reset_history=args.history,
                reset_cache=args.cache
            )
    elif args.command == "create-workspace":
        manager.create_workspace(args.name)
    elif args.command == "switch-workspace":
        manager.switch_workspace(args.name)
    elif args.command == "list-workspaces":
        manager.list_workspaces()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()    