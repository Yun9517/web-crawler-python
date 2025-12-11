import google.generativeai as genai
import os
import sys
import glob
import csv
import markdown
from datetime import datetime
from dotenv import load_dotenv

def _get_data_path(subfolder):
    """
    Get the absolute path to a data subfolder (e.g., 'csv' or 'reports').
    This works for both development (running .py script) and bundled (.exe) mode.
    """
    if getattr(sys, 'frozen', False):
        # Running as a bundled .exe. The base path is the directory of the executable.
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a .py script. Construct path relative to this file.
        # __file__ -> tech_blog_crawler/analyzer.py
        # '..' -> goes up to project root
        # 'dist' -> the target folder
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist'))
    
    # Ensure the base 'dist' directory exists, especially for script mode.
    os.makedirs(base_path, exist_ok=True)

    return os.path.join(base_path, subfolder)

def find_latest_csv():
    """Finds the most recently created CSV file."""
    try:
        csv_search_path = os.path.join(_get_data_path('csv'), '*.csv')
        list_of_files = glob.glob(csv_search_path)
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file
    except Exception as e:
        print(f"尋找 CSV 檔案時發生錯誤: {e}")
        return None

def get_api_key():
    """
    Retrieves the API key by checking environment variables first,
    then falling back to user prompt.
    """
    if getattr(sys, 'frozen', False):
        # In bundled mode, look for .env next to the .exe
        dotenv_path = os.path.join(os.path.dirname(sys.executable), '.env')
    else:
        # In script mode, look for .env in the project root
        dotenv_path = os.path.join(os.path.abspath('.'), '.env')
    
    load_dotenv(dotenv_path=dotenv_path)

    user_key = os.environ.get("GEMINI_API_KEY")
    if user_key:
        print("訊息：已自動從 .env 檔案讀取 'GEMINI_API_KEY'。")
        return user_key

    default_key = os.environ.get("DEFAULT_GEMINI_API_KEY")
    if default_key:
        print("訊息：正在使用應用程式提供的預設 API 金鑰。")
        return default_key

    print("\n未在 .env 檔案中找到金鑰，請手動輸入。")
    print("若要自動讀取，請將 .env 檔案放在與執行檔 (.exe) 相同的目錄中。")
    print("您可以從 Google AI Studio 取得金鑰: https://aistudio.google.com/app/apikey")
    return input("請輸入您的 API 金鑰，或按 Enter 取消: ").strip()

def _save_as_md(content, timestamp):
    """Saves the report content as a Markdown file."""
    try:
        report_output_dir = _get_data_path('reports')
        os.makedirs(report_output_dir, exist_ok=True)
        filename = os.path.join(report_output_dir, f"ai_report_{timestamp}.md")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"AI 報告已儲存至: {filename}")
    except Exception as e:
        print(f"儲存 Markdown 檔案時發生錯誤: {e}")

def _save_as_html(content, timestamp):
    """Saves the report content as an HTML file with basic styling."""
    try:
        html_body = markdown.markdown(content)
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI 分析報告</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 0 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: .3em;
                }}
                code {{
                    background-color: #f6f8fa;
                    padding: .2em .4em;
                    margin: 0;
                    font-size: 85%;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        report_output_dir = _get_data_path('reports')
        os.makedirs(report_output_dir, exist_ok=True)
        filename = os.path.join(report_output_dir, f"ai_report_{timestamp}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"AI 報告已儲存至: {filename}")
    except Exception as e:
        print(f"儲存 HTML 檔案時發生錯誤: {e}")

def _save_report_menu(report_content):
    """Displays a menu to ask the user how to save the report."""
    while True:
        print("\n--- 儲存選項 ---")
        print("請選擇報告的儲存格式：")
        print("  1. 儲存為 Markdown (.md)")
        print("  2. 儲存為 HTML (.html)")
        print("  3. 兩者皆要")
        print("  4. 不儲存")
        choice = input("請輸入選項 > ").strip()

        if choice in ['1', '2', '3', '4']:
            break
        else:
            print("無效的選項，請重新輸入。")
    
    if choice == '4':
        print("未儲存報告。")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if choice == '1':
        _save_as_md(report_content, timestamp)
    elif choice == '2':
        _save_as_html(report_content, timestamp)
    elif choice == '3':
        _save_as_md(report_content, timestamp)
        _save_as_html(report_content, timestamp)

def analyze_data(api_key, csv_file_path):
    """
    Reads data from a CSV file and uses the Gemini API to generate an analysis.
    """
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"設定 AI 模型時發生錯誤: {e}")
        return

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)
            except StopIteration:
                print("CSV 檔案為空或無效，沒有可分析的資料。")
                return
            data_rows = list(reader)
            if not data_rows:
                print("CSV 檔案只有標頭但沒有資料，無法分析。")
                return

        titles = [row[0] for row in data_rows if row]
        if not titles:
            print("在 CSV 資料中找不到有效的標題。")
            return

        data_for_prompt = "\n".join(f"- {title}" for title in titles)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""你是一位資深的軟體工程與市場分析顧問。
你的任務是基於提供的 CSV 文章列表，生成一份專業的「數據洞察報告」。

## 輸出格式要求 (嚴格遵守 Markdown 格式)：
1.  **### 執行摘要**：用三句話總結最重大的發現。
2.  **## 趨勢分析**：
    * **熱門主題：** 找出數據中前三名的趨勢關鍵字。
    * **增長趨勢：** 如果有日期欄位，分析近期討論熱度是否有顯著變化。
3.  **## 產品行動建議**：針對分析結果，提出一項可立即執行的產品或工程行動建議。
4.  **## 數據源附註**：註明數據來源於爬蟲，且分析基於標題文字。

**Article Titles:**
{data_for_prompt}

---
**Analysis Report:**
"""
        print("\n正在生成 AI 分析報告... (可能需要一點時間)")
        response = model.generate_content(prompt)
        report_text = response.text

        print("\n" + "="*30)
        print("      AI 分析報告")
        print("="*30)
        print(report_text)
        print("\n--- 報告結束 ---")

        _save_report_menu(report_text)

    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {csv_file_path}")
    except Exception as e:
        print(f"分析過程中發生錯誤: {e}")
        print("請確認您的 API 金鑰是否有效並擁有權限。")

def run_analyzer():
    """Main function for the analyzer module."""
    print("\n--- AI 分析 ---")
    
    csv_file = find_latest_csv()
    if not csv_file:
        print("\n找不到任何已爬取的資料可供分析。")
        print("請先執行爬蟲 (選項 1) 來產生 CSV 檔案。")
        return
    
    print(f"找到資料檔: {os.path.basename(csv_file)}")

    api_key = get_api_key()
    if not api_key:
        print("\n分析已取消，必須提供 API 金鑰。")
        return

    analyze_data(api_key, csv_file)