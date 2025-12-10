import google.generativeai as genai
import os
import glob
import csv
from datetime import datetime

def find_latest_csv():
    """Finds the most recently created CSV file in the dist/csv directory."""
    try:
        list_of_files = glob.glob(os.path.join('dist', 'csv', '*.csv'))
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file
    except Exception as e:
        print(f"尋找 CSV 檔案時發生錯誤: {e}")
        return None

def get_api_key():
    """Prompts the user to enter their Google AI API key."""
    print("\n若要使用 AI 分析功能，您需要一組 Google AI API 金鑰。")
    print("您可以從 Google AI Studio 取得金鑰: https://aistudio.google.com/app/apikey")
    api_key = input("請輸入您的 API 金鑰，或按 Enter 取消: ").strip()
    return api_key

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
            # Read the CSV content, skipping the header
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                print("CSV 檔案為空或無效，沒有可分析的資料。")
                return
                
            data_rows = list(reader)
            if not data_rows:
                print("CSV 檔案只有標頭但沒有資料，無法分析。")
                return

        # Prepare the data for the prompt
        # We'll just take the titles (first column)
        titles = [row[0] for row in data_rows if row] # Ensure row is not empty
        if not titles:
            print("在 CSV 資料中找不到有效的標題。")
            return

        data_for_prompt = "\n".join(f"- {title}" for title in titles)

        # Create the model
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

        # Print the response
        print("\n" + "="*30)
        print("      AI 分析報告")
        print("="*30)
        print(response.text)
        print("\n--- 報告結束 ---")

        # Save the report to a Markdown file
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_output_dir = os.path.join('dist', 'reports')
            os.makedirs(report_output_dir, exist_ok=True)
            report_filename = os.path.join(report_output_dir, f"ai_report_{timestamp}.md")

            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"\nAI 報告已儲存至: {report_filename}")
        except Exception as e:
            print(f"儲存 AI 報告時發生錯誤: {e}")

    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {csv_file_path}")
    except Exception as e:
        print(f"分析過程中發生錯誤: {e}")
        # This will catch potential API errors, like an invalid key
        print("請確認您的 API 金鑰是否有效並擁有權限。")


def run_analyzer():
    """Main function for the analyzer module."""
    print("\n--- AI 分析 ---")
    
    # 1. Find the latest CSV file
    csv_file = find_latest_csv()
    if not csv_file:
        print("\n找不到任何已爬取的資料可供分析。")
        print("請先執行爬蟲 (選項 1) 來產生 CSV 檔案。")
        return
    
    print(f"找到資料檔: {os.path.basename(csv_file)}")

    # 2. Get API Key
    api_key = get_api_key()
    if not api_key:
        print("\n分析已取消，必須提供 API 金鑰。")
        return

    # 3. Run the analysis
    analyze_data(api_key, csv_file)

if __name__ == '__main__':
    run_analyzer()