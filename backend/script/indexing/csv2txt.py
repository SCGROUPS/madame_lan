import csv
import os

csv_file = './data/input/data.csv'
output_dir = './data/output'

os.makedirs(output_dir, exist_ok=True)

with open(csv_file, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file, delimiter=',')
    for row in reader:
        if row['Tiêu Đề'] == "" and row['Thể_loại'] == "" and row['Chức_năng_URL'] == "" \
            and row['Nội dung văn bản'] == "":
            continue
        file_name = row['Tiêu Đề'].replace("\\", ".").replace("/", ".").strip() + '.txt'
        file_name = file_name if len(file_name) >= 5 else row['ID'] + '.txt'
        file_path = os.path.join(output_dir, file_name)
        content = "Tiêu đề:" +  row['Tiêu Đề'].strip() + "\n"
        content += "Thể loại:" +  row['Thể_loại'].strip() + "\n"
        content += "Nguồn:" +  row['Chức_năng_URL'].strip() + "\n"
        content += "Nội dung:" +  row['Nội dung văn bản'].strip()

        with open(file_path, mode='w', encoding='utf-8') as text_file:
            text_file.write(content)

        print(f"Wirite to file: {file_path}")
