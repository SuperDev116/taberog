import tkinter as tk
from tkinter import filedialog, messagebox
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from tkinter import messagebox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Construct the full path to the file
downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
output_path = os.path.join(downloads_folder, 'tabelog_output.csv')
kanryou_path = os.path.join(downloads_folder, 'tabelog_kanryou.csv')

def draw_main_window():
    root = tk.Tk()
    app = ShippingCalculatorApp(root)
    root.mainloop()


class ShippingCalculatorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("食べログツール")
        self.root.geometry("400x100")

        font_size = 14

        # スタート、一時停止、終了ボタン
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="検索開始", command=self.start_search, font=("Arial", font_size))
        self.start_button.grid(padx=20, pady=20)


    def select_and_read_file(self):
        """Open a file dialog to select a file and read its content."""
        try:
            # Open file dialog to select a file
            file_path = filedialog.askopenfilename(
                title="Select a file",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            print(file_path)
            # Check if a file was selected
            if not file_path:
                return

            # Read the content of the selected file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            return content

        except Exception as e:
            # Handle errors (e.g., file not readable, etc.)
            messagebox.showerror("Error", f"Failed to read file: {e}")

        """
    Collect information from product detail page and keepa page
    """
    
    
    def get_value_after_keyword(self, data_list, keyword, num=1):
        """
        Find the value next to the given keyword in a list.

        :param data_list: List containing the data.
        :param keyword: The keyword to search for.
        :param num: The number of positions after the keyword to fetch (default is 1).
        :return: The value next to the keyword or None if not found.
        """
        try:
            index = data_list.index(keyword)  # Find the index of the keyword
            return data_list[index + num] if index + num < len(data_list) else None
        except ValueError:
            return None  # If the keyword is not found, return None
        

    def start_search(self):

        content = self.select_and_read_file()
        url_list = []

        with open(kanryou_path, 'r', encoding='utf-8') as file_done:
            done_set = set(row.strip() for row in file_done if row.strip())
        
        for row in content.split('\n'):
            row = row.strip()
            print(row)
            if not row:
                continue  # Skip empty rows

            if row in done_set:
                print(f"-------------------------------------------- {row} --------------------------------------------")
                continue

            url_list.append(row)

        if not url_list:
            messagebox.showwarning("警告", "CSVファイルに検索するURLがありません。")
            return

        # driver = webdriver.Chrome()
        driver = webdriver.Firefox()
        driver.maximize_window()

        for url in url_list:
            print(f"情報: '{url}' の検索を開始します。")
            driver.get(f'{url}')
            time.sleep(10) # Adjust sleep time as necessary
            # continue

            try:
                lang_switch = driver.find_element(By.CSS_SELECTOR, '.c-lang-switch__more')
                lang_switch.click()
            except:
                pass

            while True:
                try:
                    shops_info_list_div = driver.find_element(By.CSS_SELECTOR , '.js-rstlist-info.rstlist-info')
                    shop_info_divs = shops_info_list_div.find_elements(By.CSS_SELECTOR , '.list-rst.js-bookmark.js-rst-cassette-wrap.js-done')
                    
                    for shop_info_div in shop_info_divs:
                        shop_link = shop_info_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        driver.execute_script("window.open(arguments[0], '_blank');", shop_link)
                        time.sleep(5)

                        driver.switch_to.window(driver.window_handles[1])
                        time.sleep(1)
                        # driver.get(shop_link)
                        # time.sleep(5)

                        info_div = driver.find_element(By.ID, 'rst-data-head')
                        info_txt = info_div.text.split('\n')
                        print(info_txt)
                        
                        shop_info = {}
                        
                        # ----- ----- ----- -----
                        # 店名
                        # ----- ----- ----- -----
                        try:
                            shop_info['name'] = self.get_value_after_keyword(info_txt, '店名')
                            print(f'name ----- ----- ----- {shop_info["name"]}')
                        except Exception as e:
                            print(e)
                            shop_info['name'] = 'なし'

                        # ----- ----- ----- -----
                        # 住所
                        # ----- ----- ----- -----
                        try:
                            shop_info['address'] = self.get_value_after_keyword(info_txt, '住所')
                            print(f'address ----- ----- ----- {shop_info["address"]}')
                        except:
                            shop_info['address'] = 'なし'

                        # ----- ----- ----- -----
                        # 電話番号
                        # ----- ----- ----- -----
                        try:
                            shop_info['phone'] = self.get_value_after_keyword(info_txt, 'お問い合わせ')
                            print(f'phone ----- ----- ----- {shop_info["phone"]}')
                        except:
                            shop_info['phone'] = 'なし'

                        # ----- ----- ----- -----
                        # 画像
                        # ----- ----- ----- -----
                        try:
                            image_div = driver.find_element(By.CLASS_NAME, 'rstdtl-top-postphoto')
                            shop_info['images'] = 'あり'
                            print(f'images ----- ----- ----- {shop_info["images"]}')
                        except:
                            shop_info['images'] = 'なし'

                        data = {
                            "店名": shop_info['name'],
                            "住所": shop_info['address'],
                            "電話番号": shop_info['phone'],
                            "画像": shop_info['images'],
                        }

                        # Save to CSV
                        out = pd.DataFrame([data])
                        out.to_csv(output_path, mode="a", header=not pd.io.common.file_exists(output_path), index=False, encoding="utf-8-sig")
                        print('write done')

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        time.sleep(1)

                    with open(kanryou_path, 'a', encoding='utf-8') as file:
                        file.write(f"{url.split(' ')[0]},{url.split(' ')[1]}\n")
                    
                    pagination_div = driver.find_element(By.CSS_SELECTOR, '.list-pagenation')
                    next_20_btn = pagination_div.find_element(By.CSS_SELECTOR, '.c-pagination__arrow.c-pagination__arrow--next')
                    next_20_btn.click()
                    time.sleep(10)
                    
                except Exception as e:
                    print(e)
                    time.sleep(1)


        driver.quit()

        messagebox.showinfo("OK", "スクレイピング完了しました。")

        
if __name__ == '__main__':
    draw_main_window()