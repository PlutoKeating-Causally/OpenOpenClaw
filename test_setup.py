#!/usr/bin/env python3
"""
OpenOpenClaw 功能测试脚本

测试内容：
1. 配置管理器功能
2. 默认配置生成
3. 配置迁移
4. 端口配置
"""

import os
import sys
import json
import tempfile
import shutil

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config_manager import ConfigManager

def test_default_config_generation():
    """Test default openclaw.json generation"""
    print("\n[测试] 默认配置生成...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_mgr = ConfigManager()
        config_mgr.data_dir = tmpdir
        
        # Create default config
        config_mgr.create_default_config(tmpdir, gateway_port=18987)
        
        # Check if openclaw.json was created
        config_path = os.path.join(tmpdir, ".openclaw", "openclaw.json")
        assert os.path.exists(config_path), "openclaw.json 未创建"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify all required sections exist
        required_sections = [
            'meta', 'wizard', 'auth', 'models', 'agents', 
            'tools', 'commands', 'session', 'hooks', 
            'channels', 'gateway', 'skills', 'plugins'
        ]
        
        for section in required_sections:
            assert section in config, f"缺少必要配置段: {section}"
        
        # Verify gateway port
        assert config['gateway']['port'] == 18987, "网关端口配置错误"
        
        # Verify tools configuration
        assert config['tools']['web']['search']['enabled'] == True, "Web搜索未启用"
        assert config['tools']['web']['fetch']['enabled'] == True, "Web抓取未启用"
        
        print("✓ 默认配置生成测试通过")
        return True

def test_config_migration():
    """Test configuration migration"""
    print("\n[测试] 配置迁移...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_mgr = ConfigManager()
        config_mgr.data_dir = tmpdir
        
        # Create an old-style config
        old_config = {
            "gateway": {
                "port": 18987
            },
            "tools": {
                "exec": {
                    "security": "full"
                }
            }
        }
        
        # Migrate to latest
        migrated = config_mgr.migrate_config_to_latest(old_config)
        
        # Verify all sections were added
        required_sections = [
            'meta', 'wizard', 'auth', 'models', 'agents', 
            'tools', 'commands', 'session', 'hooks', 
            'channels', 'gateway', 'skills', 'plugins'
        ]
        
        for section in required_sections:
            assert section in migrated, f"迁移后缺少配置段: {section}"
        
        # Verify version was updated
        assert 'lastTouchedVersion' in migrated['meta'], "版本信息未更新"
        
        print("✓ 配置迁移测试通过")
        return True

def test_port_configuration():
    """Test port configuration in openclaw.json"""
    print("\n[测试] 端口配置...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_mgr = ConfigManager()
        config_mgr.data_dir = tmpdir
        
        # Create config with custom port
        config_mgr.create_default_config(tmpdir, gateway_port=18888)
        
        config_path = os.path.join(tmpdir, ".openclaw", "openclaw.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify port
        assert config['gateway']['port'] == 18888, "自定义端口配置错误"
        
        # Verify allowedOrigins includes the port
        origins = config['gateway']['controlUi']['allowedOrigins']
        assert any(':18888' in origin for origin in origins), "allowedOrigins 未包含自定义端口"
        
        print("✓ 端口配置测试通过")
        return True

def test_allowed_origins_sync():
    """Test allowed origins synchronization"""
    print("\n[测试] Allowed Origins 同步...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_mgr = ConfigManager()
        config_mgr.data_dir = tmpdir
        
        # Create initial config
        config_mgr.create_default_config(tmpdir, gateway_port=18987)
        
        # Sync with host port
        config_mgr.sync_allowed_origins(tmpdir, container_port=18987, host_port=18001)
        
        config_path = os.path.join(tmpdir, ".openclaw", "openclaw.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify both ports are in allowedOrigins
        origins = config['gateway']['controlUi']['allowedOrigins']
        
        # Should have both container port and host port
        assert any(':18987' in o for o in origins), "缺少容器端口"
        assert any(':18001' in o for o in origins), "缺少主机端口"
        assert any('192.168.13.13' in o for o in origins), "缺少局域网 IP"
        
        print("✓ Allowed Origins 同步测试通过")
        return True

def test_env_file_generation():
    """Test .env file generation"""
    print("\n[测试] 环境变量文件生成...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_mgr = ConfigManager()
        config_mgr.data_dir = tmpdir
        
        config_mgr.create_default_config(tmpdir, gateway_port=18987)
        
        env_path = os.path.join(tmpdir, ".openclaw", ".env")
        assert os.path.exists(env_path), ".env 文件未创建"
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Verify essential variables
        assert 'OPENCLAW_HOME=/root' in content, "缺少 OPENCLAW_HOME"
        assert 'OPENCLAW_GATEWAY_PORT=18987' in content, "缺少 OPENCLAW_GATEWAY_PORT"
        
        print("✓ 环境变量文件生成测试通过")
        return True

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("OpenOpenClaw 功能测试")
    print("=" * 60)
    
    tests = [
        test_default_config_generation,
        test_config_migration,
        test_port_configuration,
        test_allowed_origins_sync,
        test_env_file_generation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} 失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
