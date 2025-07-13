#!/usr/bin/env python3
"""
CycleMACD Web Application Launcher
Simple script to start the Flask web application
"""

import os
import sys

def main():
    print("=" * 50)
    print("CycleMACD Web Application")
    print("=" * 50)
    print("日本株MACDバックテストシステム")
    print("")
    print("起動中...")
    
    # Import and run the Flask app
    from app import app
    
    print("")
    print("アプリケーションが起動しました！")
    print("ブラウザで以下のURLにアクセスしてください:")
    print("  http://localhost:5000")
    print("")
    print("停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\nアプリケーションを停止しました。")
        sys.exit(0)

if __name__ == '__main__':
    main()