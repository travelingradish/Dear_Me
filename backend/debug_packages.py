#!/usr/bin/env python3
"""
Detailed package detection debugging
"""
import sys
import pkg_resources
import importlib

def test_python_jose_detailed():
    """Test python-jose in detail"""
    print("🔍 Detailed python-jose testing...")
    
    # Method 1: Try importing jose
    try:
        import jose
        print("✅ Method 1: 'import jose' - SUCCESS")
        print(f"   jose location: {jose.__file__}")
        print(f"   jose version: {getattr(jose, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Method 1: 'import jose' - FAILED: {e}")
    
    # Method 2: Try importing python_jose
    try:
        import python_jose
        print("✅ Method 2: 'import python_jose' - SUCCESS")
    except ImportError as e:
        print(f"❌ Method 2: 'import python_jose' - FAILED: {e}")
    
    # Method 3: Try the components we actually use
    try:
        from jose import jwt
        print("✅ Method 3: 'from jose import jwt' - SUCCESS")
    except ImportError as e:
        print(f"❌ Method 3: 'from jose import jwt' - FAILED: {e}")
    
    # Method 4: Check with pkg_resources
    try:
        pkg_resources.get_distribution("python-jose")
        print("✅ Method 4: pkg_resources finds 'python-jose'")
    except pkg_resources.DistributionNotFound:
        print("❌ Method 4: pkg_resources cannot find 'python-jose'")
    
    # Method 5: Check installed packages
    print("\n📦 Checking all installed packages containing 'jose':")
    installed_packages = [pkg.project_name for pkg in pkg_resources.working_set]
    jose_packages = [pkg for pkg in installed_packages if 'jose' in pkg.lower()]
    if jose_packages:
        for pkg in jose_packages:
            print(f"   Found: {pkg}")
    else:
        print("   No packages with 'jose' found")

def check_pip_list():
    """Check what pip thinks is installed"""
    print("\n🔍 Checking pip list...")
    import subprocess
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        jose_lines = [line for line in lines if 'jose' in line.lower()]
        
        if jose_lines:
            print("📦 Pip shows these jose-related packages:")
            for line in jose_lines:
                print(f"   {line}")
        else:
            print("❌ Pip list shows no jose-related packages")
            
    except Exception as e:
        print(f"❌ Error running pip list: {e}")

def test_actual_backend_import():
    """Test what the backend actually tries to import"""
    print("\n🔍 Testing backend's actual imports...")
    
    try:
        # This is what the backend actually imports
        from jose import JWTError, jwt
        print("✅ Backend import 'from jose import JWTError, jwt' - SUCCESS")
        
        # Test creating a token (what the backend does)
        test_data = {"test": "data"}
        secret = "test_secret"
        token = jwt.encode(test_data, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        print("✅ JWT encode/decode test - SUCCESS")
        
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
    except Exception as e:
        print(f"❌ JWT test failed: {e}")

def main():
    print("=" * 60)
    print("🔧 Python-Jose Detailed Diagnostics")
    print("=" * 60)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print()
    
    test_python_jose_detailed()
    check_pip_list()
    test_actual_backend_import()
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    print("If imports are still failing:")
    print("1. Try: pip uninstall python-jose")
    print("2. Then: pip install python-jose[cryptography]")
    print("3. Or try: pip install python-jose==3.3.0")
    print("4. Check if you have multiple Python installations")

if __name__ == "__main__":
    main()