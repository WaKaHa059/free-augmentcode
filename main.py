import os
import shutil
import json
import platform
import subprocess
import random
import string
import hashlib
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

class AugmentCodeManager:
    """AugmentCode环境管理器，用于重置和管理AugmentCode的使用环境"""
    
    def __init__(self):
        """初始化管理器，设置平台相关的路径和配置"""
        self.system = platform.system()
        self.config = self._load_config()
        self.backup_dir = Path(self.config.get('backup_dir', './backups'))
        self.workspace = Path(self.config.get('workspace', './workspace'))
        
        # 设置日志
        self._setup_logging()
        
        # 根据不同操作系统设置AugmentCode的配置路径
        self.augment_paths = self._get_augment_paths()
        
        # 确保工作目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("AugmentCode管理器已初始化")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则创建默认配置"""
        config_path = Path('config.json')
        if not config_path.exists():
            default_config = {
                "backup_dir": "./backups",
                "workspace": "./workspace",
                "reset_strategies": ["device_id", "telemetry_id", "history", "database"],
                "log_level": "INFO"
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> None:
        """设置日志记录"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("augment_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("AugmentCodeManager")
    
    def _get_augment_paths(self) -> Dict[str, Path]:
        """获取不同操作系统下AugmentCode的配置路径"""
        if self.system == "Windows":
            app_data = Path(os.getenv('APPDATA', ''))
            return {
                "vscode": app_data / "Code" / "User" / "globalStorage",
                "augment_config": app_data / "Code" / "User" / "globalStorage" / "augment.augment",
                "database": app_data / "Code" / "User" / "globalStorage" / "augment.augment" / "state.vscdb",
                "history": app_data / "Code" / "User" / "globalStorage" / "augment.augment" / "history.json"
            }
        elif self.system == "Darwin":  # macOS
            home = Path.home()
            return {
                "vscode": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage",
                "augment_config": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "augment.augment",
                "database": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "augment.augment" / "state.vscdb",
                "history": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "augment.augment" / "history.json"
            }
        elif self.system == "Linux":
            home = Path.home()
            return {
                "vscode": home / ".config" / "Code" / "User" / "globalStorage",
                "augment_config": home / ".config" / "Code" / "User" / "globalStorage" / "augment.augment",
                "database": home / ".config" / "Code" / "User" / "globalStorage" / "augment.augment" / "state.vscdb",
                "history": home / ".config" / "Code" / "User" / "globalStorage" / "augment.augment" / "history.json"
            }
        else:
            self.logger.error(f"不支持的操作系统: {self.system}")
            return {}
    
    def backup_current_state(self) -> Path:
        """备份当前AugmentCode的配置和数据"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"正在备份当前状态到: {backup_path}")
        
        # 备份AugmentCode配置目录
        if self.augment_paths.get("augment_config") and self.augment_paths["augment_config"].exists():
            try:
                shutil.copytree(
                    self.augment_paths["augment_config"],
                    backup_path / "augment_config",
                    dirs_exist_ok=True
                )
                self.logger.info("AugmentCode配置备份成功")
            except Exception as e:
                self.logger.error(f"备份AugmentCode配置失败: {e}")
        
        # 备份VSCode全局存储
        if self.augment_paths.get("vscode") and self.augment_paths["vscode"].exists():
            try:
                shutil.copytree(
                    self.augment_paths["vscode"],
                    backup_path / "vscode_global_storage",
                    dirs_exist_ok=True
                )
                self.logger.info("VSCode全局存储备份成功")
            except Exception as e:
                self.logger.error(f"备份VSCode全局存储失败: {e}")
        
        return backup_path
    
    def reset_environment(self, strategies: Optional[List[str]] = None) -> None:
        """重置AugmentCode的使用环境
        
        Args:
            strategies: 重置策略列表，可选值包括'device_id', 'telemetry_id', 'history', 'database'
        """
        if not strategies:
            strategies = self.config.get('reset_strategies', [])
        
        self.logger.info(f"开始重置环境，使用策略: {', '.join(strategies)}")
        
        # 确保AugmentCode配置目录存在
        if not self.augment_paths.get("augment_config") or not self.augment_paths["augment_config"].exists():
            self.logger.warning("未找到AugmentCode配置目录，可能未安装或路径不正确")
            return
        
        # 1. 生成新的设备ID
        if "device_id" in strategies:
            self._reset_device_id()
        
        # 2. 重置遥测ID
        if "telemetry_id" in strategies:
            self._reset_telemetry_id()
        
        # 3. 清除使用历史
        if "history" in strategies:
            self._clear_history()
        
        # 4. 重置数据库
        if "database" in strategies:
            self._reset_database()
        
        self.logger.info("环境重置完成，请重启VSCode和AugmentCode")
    
    def _reset_device_id(self) -> None:
        """重置设备ID"""
        self.logger.info("重置设备ID")
        
        # 生成随机设备ID
        new_device_id = self._generate_random_id(32)
        
        # 查找并替换设备ID
        device_id_file = self.augment_paths["augment_config"] / "deviceId.json"
        if device_id_file.exists():
            try:
                with open(device_id_file, 'w') as f:
                    json.dump({"deviceId": new_device_id}, f, indent=2)
                self.logger.info(f"设备ID已更新为: {new_device_id}")
            except Exception as e:
                self.logger.error(f"更新设备ID失败: {e}")
        else:
            # 如果文件不存在，创建它
            try:
                device_id_file.parent.mkdir(parents=True, exist_ok=True)
                with open(device_id_file, 'w') as f:
                    json.dump({"deviceId": new_device_id}, f, indent=2)
                self.logger.info(f"创建新设备ID文件: {new_device_id}")
            except Exception as e:
                self.logger.error(f"创建设备ID文件失败: {e}")
    
    def _reset_telemetry_id(self) -> None:
        """重置遥测ID"""
        self.logger.info("重置遥测ID")
        
        # 生成随机遥测ID
        new_telemetry_id = self._generate_random_id(36)  # UUID格式
        
        # 查找并替换遥测ID
        telemetry_file = self.augment_paths["augment_config"] / "telemetry.json"
        if telemetry_file.exists():
            try:
                with open(telemetry_file, 'w') as f:
                    json.dump({"telemetryId": new_telemetry_id}, f, indent=2)
                self.logger.info(f"遥测ID已更新为: {new_telemetry_id}")
            except Exception as e:
                self.logger.error(f"更新遥测ID失败: {e}")
        else:
            # 如果文件不存在，创建它
            try:
                telemetry_file.parent.mkdir(parents=True, exist_ok=True)
                with open(telemetry_file, 'w') as f:
                    json.dump({"telemetryId": new_telemetry_id}, f, indent=2)
                self.logger.info(f"创建新遥测ID文件: {new_telemetry_id}")
            except Exception as e:
                self.logger.error(f"创建遥测ID文件失败: {e}")
    
    def _clear_history(self) -> None:
        """清除AugmentCode的使用历史"""
        self.logger.info("清除使用历史")
        
        history_file = self.augment_paths.get("history")
        if history_file and history_file.exists():
            try:
                with open(history_file, 'w') as f:
                    json.dump([], f)  # 清空历史记录
                self.logger.info("使用历史已清除")
            except Exception as e:
                self.logger.error(f"清除使用历史失败: {e}")
    
    def _reset_database(self) -> None:
        """重置AugmentCode的数据库"""
        self.logger.info("重置数据库")
        
        database_file = self.augment_paths.get("database")
        if database_file and database_file.exists():
            try:
                # 重命名数据库文件以重置
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_db = database_file.with_name(f"state_backup_{timestamp}.vscdb")
                database_file.rename(backup_db)
                self.logger.info(f"数据库已重置，原数据库备份为: {backup_db.name}")
            except Exception as e:
                self.logger.error(f"重置数据库失败: {e}")
    
    def _generate_random_id(self, length: int) -> str:
        """生成随机ID
        
        Args:
            length: ID长度
        
        Returns:
            随机生成的ID字符串
        """
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))
    
    def create_workspace(self, name: str) -> Path:
        """创建一个新的工作空间
        
        Args:
            name: 工作空间名称
        
        Returns:
            工作空间路径
        """
        workspace_path = self.workspace / name
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # 创建工作空间配置
        config_file = workspace_path / "workspace_config.json"
        with open(config_file, 'w') as f:
            json.dump({
                "name": name,
                "created_at": datetime.datetime.now().isoformat(),
                "device_id": self._generate_random_id(32),
                "telemetry_id": self._generate_random_id(36)
            }, f, indent=4)
        
        self.logger.info(f"创建新工作空间: {name}")
        return workspace_path
    
    def switch_to_workspace(self, name: str) -> None:
        """切换到指定的工作空间
        
        Args:
            name: 工作空间名称
        """
        workspace_path = self.workspace / name
        config_file = workspace_path / "workspace_config.json"
        
        if not config_file.exists():
            self.logger.error(f"工作空间不存在: {name}")
            return
        
        # 加载工作空间配置
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # 应用工作空间配置
        self.logger.info(f"切换到工作空间: {name}")
        
        # 更新设备ID
        device_id_file = self.augment_paths["augment_config"] / "deviceId.json"
        if device_id_file.exists():
            with open(device_id_file, 'w') as f:
                json.dump({"deviceId": config["device_id"]}, f, indent=2)
        
        # 更新遥测ID
        telemetry_file = self.augment_paths["augment_config"] / "telemetry.json"
        if telemetry_file.exists():
            with open(telemetry_file, 'w') as f:
                json.dump({"telemetryId": config["telemetry_id"]}, f, indent=2)
        
        self.logger.info(f"已切换到工作空间: {name}")

def main():
    """主函数，提供命令行界面"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AugmentCode环境管理器")
    subparsers = parser.add_subparsers(dest="command")
    
    # 备份命令
    backup_parser = subparsers.add_parser("backup", help="备份当前环境")
    
    # 重置命令
    reset_parser = subparsers.add_parser("reset", help="重置环境")
    reset_parser.add_argument(
        "--strategy", 
        choices=["device_id", "telemetry_id", "history", "database"], 
        nargs="+",
        help="指定重置策略，默认使用配置文件中的策略"
    )
    
    # 创建工作空间命令
    create_parser = subparsers.add_parser("create-workspace", help="创建新工作空间")
    create_parser.add_argument("name", help="工作空间名称")
    
    # 切换工作空间命令
    switch_parser = subparsers.add_parser("switch-workspace", help="切换到指定工作空间")
    switch_parser.add_argument("name", help="工作空间名称")
    
    # 列出工作空间命令
    list_parser = subparsers.add_parser("list-workspaces", help="列出所有工作空间")
    
    # 显示帮助信息
    args = parser.parse_args()
    
    manager = AugmentCodeManager()
    
    if args.command == "backup":
        backup_path = manager.backup_current_state()
        print(f"备份成功: {backup_path}")
    
    elif args.command == "reset":
        manager.reset_environment(args.strategy)
        print("环境重置完成，请重启VSCode和AugmentCode")
    
    elif args.command == "create-workspace":
        workspace_path = manager.create_workspace(args.name)
        print(f"工作空间创建成功: {workspace_path}")
    
    elif args.command == "switch-workspace":
        manager.switch_to_workspace(args.name)
        print(f"已切换到工作空间: {args.name}")
    
    elif args.command == "list-workspaces":
        print("可用工作空间:")
        for workspace in manager.workspace.iterdir():
            if workspace.is_dir() and (workspace / "workspace_config.json").exists():
                print(f"- {workspace.name}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()    