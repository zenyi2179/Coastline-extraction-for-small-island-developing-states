# auth.py
#!/usr/bin/env python3
"""
Earth Engine 认证和初始化模块
处理 GEE 认证、初始化和会话管理
"""

import os
import time
from typing import Optional
import ee

from config import GEEConfig


class EarthEngineAuthenticator:
    """Earth Engine 认证和初始化管理类"""
    
    def __init__(self, project: Optional[str] = None):
        """初始化认证器"""
        self.project = project or GEEConfig.PROJECT_NAME
        self._setup_environment()
    
    def _setup_environment(self) -> None:
        """设置环境变量"""
        # 设置代理
        os.environ["HTTP_PROXY"] = GEEConfig.HTTP_PROXY
        os.environ["HTTPS_PROXY"] = GEEConfig.HTTPS_PROXY
        
        # 设置代理超时
        os.environ["http_proxy_timeout"] = "300"
        os.environ["https_proxy_timeout"] = "300"
        
        # 解决 OpenSSL 3.0 兼容性问题
        os.environ["CRYPTOGRAPHY_OPENSSL_NO_LEGACY"] = "1"
    
    def authenticate_and_initialize(self) -> bool:
        """执行认证和初始化"""
        try:
            print("[INFO]  | 正在初始化 Earth Engine...")
            ee.Initialize(project=self.project)
            print("[INFO]  | Earth Engine 初始化成功")
            return True
            
        except ee.EEException:
            print("[WARN]  | 初始化失败，尝试重新认证...")
            try:
                ee.Authenticate()
                ee.Initialize(project=self.project)
                print("[INFO]  | Earth Engine 认证和初始化成功")
                return True
                
            except Exception as auth_error:
                print(f"[ERROR] | Earth Engine 认证失败: {auth_error}")
                return False
    
    def initialize_with_retry(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
        """带重试的初始化"""
        for attempt in range(max_retries):
            print(f"[INFO]  | 尝试初始化 Earth Engine (第 {attempt + 1} 次)...")
            
            if self.authenticate_and_initialize():
                return True
            
            if attempt < max_retries - 1:
                print(f"[INFO]  | 等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
        
        print("[ERROR] | Earth Engine 初始化失败，达到最大重试次数")
        return False


# 全局认证器实例
_authenticator = EarthEngineAuthenticator()


def initialize_earth_engine() -> bool:
    """初始化 Earth Engine (全局函数)"""
    return _authenticator.initialize_with_retry()


def get_earth_engine_authenticator() -> EarthEngineAuthenticator:
    """获取 Earth Engine 认证器实例"""
    return _authenticator


if __name__ == "__main__":
    # 测试认证
    success = initialize_earth_engine()
    if success:
        print("[INFO]  | Earth Engine 测试认证成功")
    else:
        print("[ERROR] | Earth Engine 测试认证失败")